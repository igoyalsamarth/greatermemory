import os

import uvicorn

from api.app import create_app
from core.model.schemas import SuperMemoryModel


def main():
    config = SuperMemoryModel(
        postgres_url=os.getenv(
            "POSTGRES_URL", "postgresql://localhost:5432/greatermemory"
        ),
        vector_db_url=os.getenv("VECTOR_DB_URL", "http://localhost:6333"),
        worker_url=os.getenv(
            "WORKER_URL", "amqp://greatermemory:greatermemory@localhost:5672/"
        ),
    )
    app = create_app(config)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
