from fastapi import APIRouter, Depends, Header, HTTPException, status

router = APIRouter(prefix="/admin")


def get_admin_header(x_admin_token: str | None = Header(None, alias="X-Admin-Token")) -> None:
    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin authentication required",
        )


@router.get("/review-queue")
def review_queue(admin_header: None = Depends(get_admin_header)) -> dict[str, list[dict[str, str]]]:
    return {"review_queue": []}
