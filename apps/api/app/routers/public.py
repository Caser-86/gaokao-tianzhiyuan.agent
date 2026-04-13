from fastapi import APIRouter, HTTPException, status

from ..services.catalog import (
    get_major_detail,
    get_school_detail,
    get_search_entry,
    list_majors,
    list_schools,
)

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/search-entry")
def search_entry() -> dict[str, object]:
    return get_search_entry()


@router.get("/schools")
def school_list(region: str | None = None, keyword: str | None = None) -> dict[str, object]:
    return list_schools(region=region, keyword=keyword)


@router.get("/majors")
def major_list() -> dict[str, object]:
    return list_majors()


@router.get("/schools/{slug}")
def school_detail(slug: str) -> dict[str, object]:
    school = get_school_detail(slug)
    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="school not found",
        )
    return school


@router.get("/majors/{slug}")
def major_detail(slug: str) -> dict[str, object]:
    major = get_major_detail(slug)
    if major is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="major not found",
        )
    return major
