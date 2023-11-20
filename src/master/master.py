import os
import asyncio
from fastapi import FastAPI, HTTPException
import httpx

from src.model.model import Message, ReplicationRequest
from src.utils.logger import get_logger

app = FastAPI()

messages = []
sequence_id = 0

SECONDARIES = os.environ.get("SECONDARIES", "").split(',')
HEALTH_CHECK_INTERVAL = 10

secondary_health = {secondary: "Unknown" for secondary in SECONDARIES}

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

    acks_received = 1  # Ack from the master is always considered received

    replication_tasks = [replicate_to_secondary(secondary, replication_request.message.content) for secondary in
                         SECONDARIES]
    pending_tasks = set(replication_tasks)

    while pending_tasks and acks_received < replication_request.write_concern:
        done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
        acks_received += sum(task.result() for task in done if task.result())

    if acks_received >= replication_request.write_concern:
        logger.info(f"Write concern of {replication_request.write_concern} satisfied, responding to client.")
        return {"status": "success",
                "detail": f"Message replicated with write concern {replication_request.write_concern}"}

    logger.error(f"Write concern of {replication_request.write_concern} not met. Only {acks_received} ACKs received.")
    raise HTTPException(
        status_code=500,
        detail=f"Write concern not met. Required: {replication_request.write_concern}, received: {acks_received} ACKs."
    )


async def check_secondary_health():
    for secondary in SECONDARIES:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{secondary}/health/")
                secondary_health[secondary] = "Healthy" if response.status_code == 200 else "Suspected"
        except httpx.RequestError as ex:
            logger.error(f"Health check failed for {secondary}: {str(ex)}")
            secondary_health[secondary] = "Unhealthy"
    asyncio.get_event_loop().call_later(HEALTH_CHECK_INTERVAL, asyncio.create_task, check_secondary_health())


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_secondary_health())


@app.get("/")
async def get_messages():
    sorted_messages = sorted(messages, key=lambda msg: msg.sequence_number)
    return sorted_messages


@app.get("/health/")
async def health_check():
    return secondary_health
