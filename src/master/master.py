import os
import asyncio
from fastapi import FastAPI, HTTPException
import httpx

from src.model.model import Message
from src.utils.logger import get_logger

app = FastAPI()

messages = []

SECONDARIES = os.environ.get("SECONDARIES", "").split(',')

logger = get_logger(__name__)


async def replicate_to_secondary(secondary, content):

    timeout_config = httpx.Timeout(10.0, read=None)

    async with httpx.AsyncClient(timeout=timeout_config) as client:
        for _ in range(3):  # Try 3 times
            try:
                response = await client.post(f"{secondary}/replicate/", json={"content": content})

                code, text = response.status_code, response.text[:50] if response.text else "NaN"
                logger.info(f"Received response from {secondary} - Code=\[{code}] Content=[{text}]")

                if response.status_code == 200:
                    return True
            except Exception as ex:
                print(repr(ex))
            await asyncio.sleep(1)  # Wait for 1 second before retrying
    logger.error(f"Failed to replicate to {secondary}")
    return False


@app.post("/")
async def post_message(message: Message):
    messages.append(message.content)

    replication_results = await asyncio.gather(
        *(replicate_to_secondary(secondary, message.content) for secondary in SECONDARIES))

    if not all(replication_results):
        failed_secondaries = [SECONDARIES[i] for i, success in enumerate(replication_results) if not success]
        error_message = f"Failed to replicate to {', '.join(failed_secondaries)}"
        raise HTTPException(status_code=500, detail=error_message)

    return {"status": "success"}


@app.get("/")
async def get_messages():
    return messages


@app.get("/health/")
async def health_check():
    return {"status": "healthy"}
