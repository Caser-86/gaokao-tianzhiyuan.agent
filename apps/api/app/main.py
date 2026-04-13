from fastapi import APIRouter, FastAPI

from .config import settings


app = FastAPI(title=settings.app_name)
api_router = APIRouter(prefix=settings.api_prefix)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
