from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from qdrant_client import QdrantClient

from core.model.schemas import SuperMemoryModel, SuperMemoryResponse, SuperMemoryCreate
from db.models import Base, MemoryType, SuperMemoryTable

MEMORY_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extract the memory as structured output to be used in future conversations. "
            "Include a confidence score (0.0 to 1.0) indicating how confident you are in this memory, "
            "and a memory_type from the allowed types. "
            "Possible memory types: {memory_types}.",
        ),
        ("human", "{memory_input}"),
    ]
)


class SuperMemory:
    """Core memory engine - stores and retrieves memories via PostgreSQL."""

    def __init__(self, config: SuperMemoryModel):
        self.config = config
        self._engine = create_engine(config.postgres_url)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(
            self._engine, autocommit=False, autoflush=False
        )
        self.llm = ChatOllama(model="llama3.1")
        self.embedding_model = OllamaEmbeddings(model="llama3")
        self.vector_store = QdrantClient(":memory:")

    def add(self, memory: str) -> SuperMemoryResponse:
        """Add a memory and return the created record."""
        chain = MEMORY_EXTRACTION_PROMPT | self.llm.with_structured_output(
            SuperMemoryCreate
        )
        response = chain.invoke(
            {
                "memory_types": ", ".join(t.value for t in MemoryType),
                "memory_input": memory,
            }
        )

        with self._session_factory() as session:
            row = SuperMemoryTable(
                memory=response.memory,
                memory_type=response.memory_type,
                confidence_score=response.confidence_score,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return SuperMemoryResponse.model_validate(row)

    def retrieve(self, query: str) -> list[SuperMemoryResponse]:
        """Retrieve memories matching the query (text search on memory content)."""
        with self._session_factory() as session:
            stmt = (
                select(SuperMemoryTable)
                .where(SuperMemoryTable.memory.ilike(f"%{query}%"))
                .order_by(SuperMemoryTable.created_at.desc())
            )
            rows = session.scalars(stmt).all()
            return [SuperMemoryResponse.model_validate(r) for r in rows]
