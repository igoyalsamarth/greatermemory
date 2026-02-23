from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.model.schemas import SuperMemoryResponse
from core.supermemory import SuperMemory

router = APIRouter()


class MemoryInput(BaseModel):
    memory: str


@router.post("/memories", response_model=SuperMemoryResponse)
def add_memory(request: Request, body: MemoryInput) -> SuperMemoryResponse:
    """Add a new memory."""
    supermemory: SuperMemory = request.app.state.supermemory
    return supermemory.add(body.memory)


@router.get("/memories/retrieve", response_model=list[SuperMemoryResponse])
def retrieve_memories(request: Request, query: str) -> list[SuperMemoryResponse]:
    """Retrieve memories matching the query."""
    supermemory: SuperMemory = request.app.state.supermemory
    return supermemory.retrieve(query)
