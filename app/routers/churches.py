# app/routers/churches.py
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
)
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Church
from ..schemas import ChurchOut
from ..auth_utils import get_current_admin

router = APIRouter(tags=["admin_churches"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def build_logo_meta(url: Optional[str]) -> Optional[dict]:
    """
    Build a Xano-like logo object from a stored URL.
    We at least return access/path/url so frontend can use logo.url.
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


@router.post("/churches", response_model=ChurchOut)
async def create_church(
    name: str = Form(...),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    contact_number: Optional[str] = Form(None),
    short_description: Optional[str] = Form(None),
    logo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Admin-only endpoint to create a church.
    Expects multipart/form-data with text fields + logo file.
    """

    # Trim text inputs like Xano's filters=trim
    name = name.strip()
    address = address.strip() if address else None
    city = city.strip() if city else None
    state = state.strip() if state else None
    contact_number = contact_number.strip() if contact_number else None
    short_description = short_description.strip() if short_description else None

    logo_url: Optional[str] = None

    if logo is not None:
        file_bytes = await logo.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Logo file is empty")

        ts = int(datetime.utcnow().timestamp())
        safe_name = logo.filename.replace(" ", "_")
        filename = f"{ts}_{safe_name}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(file_bytes)

        # Public URL as served by FastAPI static mount
        logo_url = f"/uploads/{filename}"

    # Insert into DB
    church = Church(
        name=name,
        address=address,
        city=city,
        state=state,
        contact_number=contact_number,
        short_description=short_description,
        logo=logo_url,        # text/url in DB
        created_by=admin.id,  # authenticated admin
    )
    db.add(church)
    db.commit()
    db.refresh(church)

    return ChurchOut(
        id=church.id,
        created_at=church.created_at,
        created_by=church.created_by,
        name=church.name,
        address=church.address,
        city=church.city,
        state=church.state,
        contact_number=church.contact_number,
        short_description=church.short_description,
        logo=build_logo_meta(church.logo),
    )


@router.get("/get-churches", response_model=List[ChurchOut])
def get_my_churches(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Return all churches where created_by == current admin.id
    """
    churches = (
        db.query(Church)
        .filter(Church.created_by == admin.id)
        .order_by(Church.id.asc())
        .all()
    )

    result: List[ChurchOut] = []
    for ch in churches:
        result.append(
            ChurchOut(
                id=ch.id,
                created_at=ch.created_at,
                created_by=ch.created_by,
                name=ch.name,
                address=ch.address,
                city=ch.city,
                state=ch.state,
                contact_number=ch.contact_number,
                short_description=ch.short_description,
                logo=build_logo_meta(ch.logo),
            )
        )

    return result
