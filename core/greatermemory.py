import uuid
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings, ChatOllama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore

from core.model.schemas import (
    GreaterMemoryModel,
    GreaterMemoryResponse,
    GreaterMemoryCreate,
)
from db.models import Base, MemoryType, GreaterMemoryTable


MEMORY_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a memory extraction engine. Your job is to take unstructured text input and extract the memory from it in a structured format. "
            "Extract the memory as structured outputs to be used in future conversations. "
            "Include a confidence score (0.0 to 1.0) indicating how confident you are in each memory, "
            "and a memory_type from the allowed types. "
            "Possible memory types: {memory_types}. "
            "If the input says 'I love chocolate ice cream', you might extract a memory with memory_type 'preference' and memory 'User loves chocolate ice cream'. "
            "If the input says 'I have a meeting tomorrow at 3pm', you might extract a memory with memory_type 'episodic' and memory 'User has a meeting tomorrow at 3pm'. "
            "If the input says 'My name is John', you might extract a memory with memory_type 'fact' and memory 'User's name is John'. "
            "You are not allowed to counter question the user or ask for clarification. If the input is vague, extract the most likely memory with low confidence scores.",
        ),
        ("human", "{memory_input}"),
    ]
)


class GreaterMemory:
    """Core memory engine - stores and retrieves memories via PostgreSQL."""

    def __init__(self, config: GreaterMemoryModel):
        self.config = config
        self._engine = create_engine(config.postgres_url)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(
            self._engine, autocommit=False, autoflush=False
        )
        self.llm = ChatOllama(model="llama3.1:8b")
        self.embedding_model = OllamaEmbeddings(model="llama3.1:8b")
        vector_client = QdrantClient(url=config.vector_db_url)

        vector_size = len(self.embedding_model.embed_query("sample text"))
        if not vector_client.collection_exists("greatermemory"):
            vector_client.create_collection(
                collection_name="greatermemory",
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

        self.vector_store = QdrantVectorStore(
            client=vector_client,
            collection_name="greatermemory",
            embedding=self.embedding_model,
        )

    def add(self, memory: str) -> GreaterMemoryResponse:
        """Add a memory and return the created record."""
        chain = MEMORY_EXTRACTION_PROMPT | self.llm.with_structured_output(
            GreaterMemoryCreate
        )
        response = chain.invoke(
            {
                "memory_types": ", ".join(t.value for t in MemoryType),
                "memory_input": memory,
            }
        )

        print("LLM response:", response)

        memory_id = uuid.uuid4()

        metadata = {
            "id": str(memory_id),
            "memory_type": response.memory_type.value,
            "confidence_score": response.confidence_score,
        }

        row = GreaterMemoryTable(
            id=memory_id,
            memory=response.memory,
            memory_type=response.memory_type,
            confidence_score=response.confidence_score,
        )

        def insert_postgres() -> GreaterMemoryResponse:
            with self._session_factory() as session:
                session.add(row)
                session.commit()
                session.refresh(row)
                return GreaterMemoryResponse.model_validate(row)

        def insert_vector_db() -> None:
            self.vector_store.add_texts(
                texts=[response.memory],
                ids=[str(memory_id)],
                metadatas=[metadata],
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            pg_future = executor.submit(insert_postgres)
            vec_future = executor.submit(insert_vector_db)
            pg_result = pg_future.result()
            vec_future.result()

        return pg_result

    def retrieve(self, query: str, k: int = 5) -> list[GreaterMemoryResponse]:
        """Retrieve memories matching the query via cosine similarity over embeddings."""
        docs = self.vector_store.similarity_search(query, k=k)
        if not docs:
            return []
        ids = [uuid.UUID(d.metadata["id"]) for d in docs if "id" in d.metadata]
        if not ids:
            return []
        with self._session_factory() as session:
            stmt = select(GreaterMemoryTable).where(GreaterMemoryTable.id.in_(ids))
            rows = session.scalars(stmt).all()
            # Preserve order from similarity search (most similar first)
            order_map = {id_: i for i, id_ in enumerate(ids)}
            rows_sorted = sorted(rows, key=lambda r: order_map.get(r.id, len(ids)))
            return [GreaterMemoryResponse.model_validate(r) for r in rows_sorted]
