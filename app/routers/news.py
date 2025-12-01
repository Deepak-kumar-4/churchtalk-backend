# app/routers/news.py
import os
from datetime import datetime
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
)
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import NewsAdmin, Church
from ..schemas import (
    NewsOut,
    NewsCreateResponse,
    NewsDeleteRequest,
    NewsDeleteResponse,
    NewsListResponse,
    NewsListPayload,
)
from ..auth_utils import get_current_admin

router = APIRouter(prefix="/news", tags=["admin_news"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def build_image_meta(url: Optional[str]) -> Optional[dict]:
    """
    Build a Xano-like image metadata object from a stored URL.
    We don't have width/height here, so we return None for meta.
    """
    if not url:
        return None
    return {
        "access": "public",
        "path": url,
        "name": None,
        "type": "image",
        "size": None,
        "mime": None,
        "meta": None,
        "url": url,
    }


def ensure_church_owned(
    db: Session, church_id: int, admin_id: int
) -> Church:
    church = (
        db.query(Church)
        .filter(
            Church.id == church_id,
            Church.created_by == admin_id,
        )
        .first()
    )
    if not church:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to manage news for this church.",
        )
    return church


# 1) CREATE NEWS  -------------------------------------------------------------
@router.post("/create-news", response_model=NewsCreateResponse)
async def create_NewsAdmin(
    title: str = Form(...),
    content: str = Form(...),
    church_id: int = Form(...),
    news_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Create a news post for a church owned by the current admin.
    Expects multipart/form-data including an image file.
    """

    # Basic validation (trim + non-empty)
    title = title.strip()
    content = content.strip()

    if not title or not content:
        raise HTTPException(
            status_code=400,
            detail="Title and content are required.",
        )

    # Ensure admin owns this church
    ensure_church_owned(db, church_id, admin.id)

    # Image upload (required as per your plan)
    if news_image is None:
        raise HTTPException(
            status_code=400,
            detail="News image is required.",
        )

    file_bytes = await news_image.read()
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="News image file is empty.",
        )

    ts = int(datetime.utcnow().timestamp())
    safe_name = news_image.filename.replace(" ", "_")
    filename = f"news_{ts}_{safe_name}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    image_url = f"/uploads/{filename}"

    # Insert into DB
    now = datetime.utcnow()
    news = NewsAdmin(
        title=title,
        content=content,
        church_id=church_id,
        created_by=admin.id,
        image=image_url,        # stored as URL/path in DB
        created_at=now,
        updated_at=now,
    )
    db.add(news)
    db.commit()
    db.refresh(news)

    news_out = NewsOut(
        id=news.id,
        title=news.title,
        content=news.content,
        church_id=news.church_id,
        created_by=news.created_by,
        created_at=news.created_at,
        updated_at=news.updated_at,
        image=build_image_meta(news.image),
    )

    return {
        "message": "News created successfully",
        "newsItem": news_out,
    }


# 2) DELETE NEWS  -------------------------------------------------------------
@router.post("/delete", response_model=NewsDeleteResponse)
def delete_NewsAdmin(
    payload: NewsDeleteRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Delete a news item by id.
    Only the admin who created the news can delete it.
    """

    news = db.query(NewsAdmin).filter(NewsAdmin.id == payload.id).first()
    if not news:
        raise HTTPException(
            status_code=404,
            detail="News item not found.",
        )

    if news.created_by != admin.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to delete this news item.",
        )

    db.delete(news)
    db.commit()

    return NewsDeleteResponse(
        message="News item deleted successfully.",
        id=payload.id,
    )


# 3) GET NEWS (PAGINATED)  ----------------------------------------------------
@router.get("/get-news", response_model=NewsListResponse)
def get_NewsAdmin(
    church_id: int = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Get paginated news items for a church owned by the current admin.
    Mirrors your Xano /admin/news behavior.
    """

    # Make sure admin owns this church
    ensure_church_owned(db, church_id, admin.id)

    base_query = (
        db.query(NewsAdmin)
        .filter(
            NewsAdmin.church_id == church_id,
            NewsAdmin.created_by == admin.id,
        )
        .order_by(NewsAdmin.created_at.desc())
    )

    total_count = base_query.count()
    offset = (page - 1) * per_page

    items_db = base_query.offset(offset).limit(per_page).all()
    items: List[NewsOut] = []

    for n in items_db:
        items.append(
            NewsOut(
                id=n.id,
                title=n.title,
                content=n.content,
                church_id=n.church_id,
                created_by=n.created_by,
                created_at=n.created_at,
                updated_at=n.updated_at,
                image=build_image_meta(n.image),
            )
        )

    items_received = len(items)
    next_page = page + 1 if offset + items_received < total_count else None
    prev_page = page - 1 if page > 1 else None

    payload = NewsListPayload(
        itemsReceived=items_received,
        curPage=page,
        nextPage=next_page,
        prevPage=prev_page,
        offset=offset,
        perPage=per_page,
        items=items,
    )

    return NewsListResponse(
        newsList=payload,
        limit=per_page,
        offset=offset,
    )


# 4) UPDATE NEWS  -------------------------------------------------------------
@router.post("/update", response_model=NewsOut)
async def update_NewsAdmin(
    id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    news_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Update title/content (and optionally image) of a news item.
    Only the admin who created the news can update it.
    """

    news = db.query(NewsAdmin).filter(NewsAdmin.id == id).first()
    if not news:
        raise HTTPException(
            status_code=404,
            detail="News item not found.",
        )

    if news.created_by != admin.id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to update this news item.",
        )

    title = title.strip()
    content = content.strip()

    if not title or not content:
        raise HTTPException(
            status_code=400,
            detail="Title and content are required.",
        )

    image_url = news.image

    # If new image provided, upload and use it; otherwise keep old image
    if news_image is not None:
        file_bytes = await news_image.read()
        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="News image file is empty.",
            )

        ts = int(datetime.utcnow().timestamp())
        safe_name = news_image.filename.replace(" ", "_")
        filename = f"news_{ts}_{safe_name}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(file_bytes)

        image_url = f"/uploads/{filename}"

    # Update record
    news.title = title
    news.content = content
    news.image = image_url
    news.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(news)

    return NewsOut(
        id=news.id,
        title=news.title,
        content=news.content,
        church_id=news.church_id,
        created_by=news.created_by,
        created_at=news.created_at,
        updated_at=news.updated_at,
        image=build_image_meta(news.image),
    )