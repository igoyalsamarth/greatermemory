import uuid
from datetime import datetime

from pydantic import BaseModel

from db.models import MemoryType


class SuperMemoryCreate(BaseModel):
    """Schema for creating a new memory."""

    memory: str
    memory_type: MemoryType
    confidence_score: float


class SuperMemoryResponse(BaseModel):
    """Schema for reading/returning a memory."""

    id: uuid.UUID
    memory: str
    memory_type: MemoryType
    confidence_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class SuperMemoryModel(BaseModel):
    """Database configuration."""

    postgres_url: str
    vector_db_url: str
    worker_url: str
