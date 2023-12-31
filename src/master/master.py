import os
import asyncio
import time
from fastapi import FastAPI, HTTPException
import httpx

from src.model.model import ReplicationRequest
from src.utils.logger import get_logger

app = FastAPI()

messages = []
sequence_id = 0

SECONDARIES = os.environ.get("SECONDARIES", "").split(',')

secondary_health = {secondary: "Unknown" for secondary in SECONDARIES}

HEALTH_CHECK_INTERVAL = 10
SUSPECTED_THRESHOLD = 3

shutdown_signal = asyncio.Event()

logger = get_logger(__name__)


async def replicate_to_secondary(secondary, content):
    timeout_config = httpx.Timeout(10.0, read=None)
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        for attempt in range(3):
            try:
                response = await client.post(f"{secondary}/replicate/", json={"content": content})
                if response.status_code == 200:
                    logger.info(f"Replication to {secondary} successful.")
                    return True
                else:
                    logger.warning(
                        f"Replication to {secondary} returned status {response.status_code} on attempt {attempt + 1}.")
            except httpx.RequestError as ex:
                logger.error(f"Replication to {secondary} failed on attempt {attempt + 1}: {repr(ex)}")
            await asyncio.sleep(1)  # Wait for 1 second before retrying
    logger.error(f"Failed to replicate to {secondary} after 3 attempts.")
    return False


@app.post("/")
async def post_message(replication_request: ReplicationRequest):
    global sequence_id

    max_write_concern = len(SECONDARIES) + 1
    if replication_request.write_concern > max_write_concern:
        raise HTTPException(
            status_code=400,
            detail=f"Write concern too high. Maximum allowed is {max_write_concern}"
        )

    if any(msg.id == replication_request.message.id for msg in messages):
        logger.info(f"Duplicate message ID received: {replication_request.message.id}, ignoring.")
        return {"status": "success", "detail": "Duplicate message, already replicated."}

    replication_request.message.sequence_number = sequence_id
    sequence_id += 1
    messages.append(replication_request.message)

    if replication_request.write_concern == 1:
        logger.info("Write concern is 1, responding to client without waiting for secondaries.")
        for secondary in SECONDARIES:
            asyncio.create_task(replicate_to_secondary(secondary, replication_request.message.content))
        return {"status": "success", "detail": "Message replicated with write concern 1"}

    acks_needed = replication_request.write_concern - 1
    semaphore = asyncio.Semaphore(0)
    replication_tasks = []

    for secondary in SECONDARIES:
        task = asyncio.create_task(replicate_and_release(secondary, replication_request.message.content, semaphore))
        replication_tasks.append(task)

    successful_acks = 1  # Ack from the master is always considered received
    replication_timeout = 10  # seconds
    try:
        for _ in range(acks_needed):
            await asyncio.wait_for(semaphore.acquire(), timeout=replication_timeout)
            successful_acks += 1
    except asyncio.TimeoutError:
        logger.warning("Timeout reached while waiting for replication acknowledgments.")

    if successful_acks >= replication_request.write_concern:
        return {"status": "success",
                "detail": f"Message replicated with write concern {replication_request.write_concern}"}
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Write concern not met. Required: {replication_request.write_concern}, received: {successful_acks} ACKs."
        )


async def replicate_and_release(secondary, content, semaphore):
    success = await replicate_to_secondary(secondary, content)
    if success:
        semaphore.release()


@app.get("/")
async def get_messages():
    sorted_messages = sorted(messages, key=lambda msg: msg.sequence_number)
    return sorted_messages


async def perform_health_check(secondary):
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{secondary}/health/")
        response_time = time.time() - start_time

        if response.status_code == 200 and response_time < SUSPECTED_THRESHOLD:
            return secondary, "Healthy"
        else:
            return secondary, "Suspected"
    except Exception as ex:
        logger.error(f"Health check failed for {secondary}: {str(ex)}")
        return secondary, "Unhealthy"


async def check_secondary_health():
    while not shutdown_signal.is_set():
        health_check_tasks = [perform_health_check(secondary) for secondary in SECONDARIES]
        health_check_results = await asyncio.gather(*health_check_tasks)

        for secondary, status in health_check_results:
            secondary_health[secondary] = status

        await asyncio.sleep(HEALTH_CHECK_INTERVAL)


@app.get("/health/")
async def health_check():
    return secondary_health


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_secondary_health())


@app.on_event("shutdown")
async def shutdown_event():
    shutdown_signal.set()
