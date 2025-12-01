# app/routers/members.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, Church, ChurchMember, NewsAdmin
from ..schemas import (
    ChurchMemberOut,
    NewsOut,
    JoinChurchRequest,
    JoinChurchResponse,
    MemberSignupRequest,
    MemberSignupResponse,
)
from ..auth_utils import get_current_user, hash_password, create_access_token

router = APIRouter(tags=["member"])


# ---------- helpers ----------

def build_logo_meta(url: Optional[str]) -> Optional[dict]:
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


def build_image_meta(url: Optional[str]) -> Optional[dict]:
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


# 1) GET member/churches  -----------------------------------------------------
@router.get("/member/churches")
def member_list_churches(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Member view of all churches.
    Auth required. No ownership filter.
    """
    churches = db.query(Church).order_by(Church.id.asc()).all()

    result = []
    for ch in churches:
        result.append(
            {
                "id": ch.id,
                "created_at": ch.created_at,
                "name": ch.name,
                "address": ch.address,
                "city": ch.city,
                "state": ch.state,
                "contact_number": ch.contact_number,
                "short_description": ch.short_description,
                "created_by": ch.created_by,
                "logo": build_logo_meta(ch.logo),
            }
        )

    return result


# 2) POST member/churches/join  ----------------------------------------------
@router.post("/member/churches/joinchurch", response_model=JoinChurchResponse)
def member_join_church(
    payload: JoinChurchRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Join a church as a member.
    - Requires auth token
    - Prevents duplicate membership
    """

    # 1. Check church exists
    church = db.query(Church).filter(Church.id == payload.church_id).first()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found.")

    # 2. Check existing membership
    membership = (
        db.query(ChurchMember)
        .filter(
            ChurchMember.user == user.id,
            ChurchMember.church == payload.church_id,
        )
        .first()
    )

    if membership:
        # Already a member
        return {
            "message": "Already a member of this church",
            "joined": False,
            "membership": {
                "id": membership.id,
                "user": membership.user,
                "church": membership.church,
                "created_at": membership.created_at,
                "joined_at": membership.joined_at,
            },
        }

    # 3. Create new membership
    now = datetime.utcnow()
    membership = ChurchMember(
        user=user.id,
        church=payload.church_id,
        created_at=now,
        joined_at=now,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return {
        "message": "Joined church successfully",
        "joined": True,
        "membership": {
            "id": membership.id,
            "user": membership.user,
            "church": membership.church,
            "created_at": membership.created_at,
            "joined_at": membership.joined_at,
        },
    }


# 3) GET members/news-by-church  ---------------------------------------------
@router.get("/member/news-by-church", response_model=List[NewsOut])
def member_news_by_church(
    church_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get ALL news for a given church_id.
    Visible to any authenticated user.
    """

    news_items = (
        db.query(NewsAdmin)
        .filter(NewsAdmin.church_id == church_id)
        .order_by(NewsAdmin.created_at.desc())
        .all()
    )

    result: List[NewsOut] = []
    for n in news_items:
        result.append(
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

    return result


# 4) POST member/signup  ------------------------------------------------------
@router.post("/member/signup", response_model=MemberSignupResponse)
def member_signup(
    payload: MemberSignupRequest,
    db: Session = Depends(get_db),
):
    """
    Signup endpoint for members (non-admin).
    - Creates user with is_admin=False
    - Returns auth_token + user object
    """

    email = payload.email.strip().lower()

    # 1. Check email already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create user (non-admin)
    user = User(
        name=payload.name,
        email=email,
        password=hash_password(payload.password),
        is_admin=False,
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Create auth token
    token = create_access_token({"id": user.id})

    # 4. Return plain dict; FastAPI will cast to MemberSignupResponse
    return {
        "auth_token": token,
        "user": {
            "id": user.id,
            "created_at": user.created_at,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "age": user.age,
            "gender": user.gender,
            "phone": user.phone,
            "address": user.address,
        },
    }
