# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..schemas import UserCreate, UserOut, AdminSignupResponse
from ..auth_utils import hash_password, create_access_token

router = APIRouter(prefix="/auth", tags=["admin_auth"])


@router.post("/signup", response_model=AdminSignupResponse)
def admin_signup(payload: UserCreate, db: Session = Depends(get_db)):
    # 1. Check email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create admin user
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        is_admin=True,  # force admin true for this route
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Create token
    token = create_access_token(user.id)

    # 4. Return same shape as Xano
    return {
        "authToken": token,
        "user": user,
    }
