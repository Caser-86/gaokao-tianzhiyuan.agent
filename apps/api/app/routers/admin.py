from fastapi import APIRouter, Header, HTTPException, status

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != "dev-admin-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin authentication required",
        )


@router.get("/review-queue")
def list_review_queue(x_admin_token: str | None = Header(default=None)) -> dict[str, list]:
    require_admin(x_admin_token)
    return {"items": []}
