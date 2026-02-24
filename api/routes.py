from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.model.schemas import GreaterMemoryResponse
from core.greatermemory import GreaterMemory

router = APIRouter()


class MemoryInput(BaseModel):
    memory: str


@router.post("/memories", response_model=GreaterMemoryResponse)
def add_memory(request: Request, body: MemoryInput) -> GreaterMemoryResponse:
    """Add a new memory."""
    greatermemory: GreaterMemory = request.app.state.greatermemory
    return greatermemory.add(body.memory)


@router.get("/memories/retrieve", response_model=list[GreaterMemoryResponse])
def retrieve_memories(request: Request, query: str) -> list[GreaterMemoryResponse]:
    """Retrieve memories matching the query."""
    greatermemory: GreaterMemory = request.app.state.greatermemory
    return greatermemory.retrieve(query)
