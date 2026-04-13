from fastapi import FastAPI

from .config import settings
from .db import create_all_models
from .routers.admin import router as admin_router
from .routers.platform import router as platform_router
from .routers.public import router as public_router


app = FastAPI(title=settings.app_name)
app.include_router(admin_router)
app.include_router(platform_router)
app.include_router(public_router)


@app.on_event("startup")
def on_startup() -> None:
    create_all_models()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
