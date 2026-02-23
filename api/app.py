from fastapi import FastAPI

from api.routes import router
from core.supermemory import SuperMemory
from core.model.schemas import SuperMemoryModel


def create_app(config: SuperMemoryModel) -> FastAPI:
    """Create the FastAPI app with core engine initialized."""
    app = FastAPI(title="GreaterMemory API", redirect_slashes=False)

    supermemory = SuperMemory(config)
    app.state.supermemory = supermemory

    app.include_router(router, prefix="/api", tags=["memories"])

    return app
