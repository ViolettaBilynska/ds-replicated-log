from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for each message")
    content: str = Field(..., description="Content of the message")
    sequence_number: int = Field(0, description="Sequence number for ordering messages")


class ReplicationRequest(BaseModel):
    message: Message
    write_concern: int = Field(ge=1, description="Number of ACKs required before responding to the client")
