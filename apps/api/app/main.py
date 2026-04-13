from fastapi import APIRouter, FastAPI

from .config import settings
from .routers import admin


app = FastAPI(title=settings.app_name)
api_router = APIRouter(prefix=settings.api_prefix)

api_router.include_router(admin.router)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
