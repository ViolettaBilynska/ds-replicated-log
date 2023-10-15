from pydantic import BaseModel, Field


class Message(BaseModel):
    content: str = Field(..., description="Content of the message", example="Hello, World!")
