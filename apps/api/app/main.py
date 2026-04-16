from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import create_all_models
from .routers.admin import router as admin_router
from .routers.chat import router as chat_router
from .routers.platform import router as platform_router
from .routers.public import router as public_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_all_models()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
if settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(platform_router)
app.include_router(public_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
