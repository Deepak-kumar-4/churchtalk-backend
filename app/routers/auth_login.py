from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import UserOut
from ..auth_utils import verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Swagger sends `username` field, we treat it as email
    email = form_data.username.strip().lower()
    password = form_data.password

    # 1. Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    # 2. Verify password
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    # 3. Create token
    token = create_access_token(user.id)

    # 4. Shape the response like Xano
    user_out = UserOut.model_validate(user)

    return {
        # For your Xano-style frontend
    "authToken": token,

    # For Swagger / OAuth2PasswordBearer
    "access_token": token,
    "token_type": "bearer",

    # User payload
    "user": user_out,
    }
