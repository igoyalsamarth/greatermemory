from fastapi import FastAPI

from api.routes import router
from core.greatermemory import GreaterMemory
from core.model.schemas import GreaterMemoryModel


def create_app(config: GreaterMemoryModel) -> FastAPI:
    """Create the FastAPI app with core engine initialized."""
    app = FastAPI(title="GreaterMemory API", redirect_slashes=False)

    greatermemory = GreaterMemory(config)
    app.state.greatermemory = greatermemory

    app.include_router(router, prefix="/api", tags=["memories"])

    return app
