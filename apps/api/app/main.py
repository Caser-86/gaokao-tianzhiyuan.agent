from fastapi import FastAPI

from .config import settings
from .routers.admin import router as admin_router


app = FastAPI(title=settings.app_name)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
