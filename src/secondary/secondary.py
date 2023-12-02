import os
import asyncio
import random
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from typing import List

from src.model.model import Message
from src.utils.logger import get_logger

app = FastAPI()

SECONDARY_PORT = os.environ.get("SECONDARY_PORT", 8001)
replicated_messages: List[Message] = []

logger = get_logger(__name__)


@app.get("/messages/", response_model=List[Message])
async def get_messages():
    sorted_messages = sorted(replicated_messages, key=lambda msg: msg.sequence_number)
    logger.info(sorted_messages)
    data = jsonable_encoder(sorted_messages)
    return JSONResponse(content=data)


@app.post("/replicate/", response_model=Message)
async def replicate_message(message: Message):
    delay = random.uniform(0.5, 3.0)
    await asyncio.sleep(delay)

    if not any(msg.id == message.id for msg in replicated_messages):
        replicated_messages.append(message)
        logger.info(f"Replicated message: {message.content} with a delay of {delay}s")
    else:
        logger.info(f"Duplicate message ignored: {message.content}")

    return message


@app.get("/health/")
async def health_check():
    return {"status": "healthy"}
