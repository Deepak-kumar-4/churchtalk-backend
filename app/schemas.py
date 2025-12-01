# app/schemas.py
from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict 
from typing import Optional, List
from datetime import datetime


# ---------- User / Auth ----------

class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_admin: bool = False
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminSignupResponse(BaseModel):
    authToken: str
    user: UserOut

    class Config:
        orm_mode = True


# ---------- Church ----------

class ChurchBase(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact_number: Optional[str] = None
    short_description: Optional[str] = None
    


class ChurchCreate(ChurchBase):
    pass


class ChurchOut(ChurchBase):
    id: int
    created_at: datetime
    created_by: Optional[int] = None
    logo: Optional[dict] = None   # Xano-like image metadata object

    model_config = ConfigDict(from_attributes=True)


# ---------- Church Members ----------

class ChurchMemberBase(BaseModel):
    church: int


class ChurchMemberCreate(ChurchMemberBase):
    pass


class ChurchMemberOut(BaseModel):
    id: int
    user: int
    church: int
    created_at: datetime
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- News ----------

class NewsBase(BaseModel):
    title: str
    content: str
    church_id: int


class NewsCreate(NewsBase):
    pass


class NewsOut(NewsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    image: Optional[dict] = None  # Xano-like image metadata

    model_config = ConfigDict(from_attributes=True)

class NewsCreateResponse(BaseModel):
    message: str
    newsItem: NewsOut


class NewsDeleteRequest(BaseModel):
    id: int


class NewsDeleteResponse(BaseModel):
    message: str
    id: int


class NewsListPayload(BaseModel):
    itemsReceived: int
    curPage: int
    nextPage: Optional[int] = None
    prevPage: Optional[int] = None
    offset: int
    perPage: int
    items: List[NewsOut]


class NewsListResponse(BaseModel):
    newsList: NewsListPayload
    limit: int
    offset: int

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    authToken: str
    user: dict

# ---------- Member / Join Church ----------

class JoinChurchRequest(BaseModel):
    church_id: int


class JoinChurchResponse(BaseModel):
    message: str
    joined: bool
    membership: "ChurchMemberOut"  # forward ref if needed


# ---------- Member Signup ----------

class MemberSignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class MemberSignupResponse(BaseModel):
    auth_token: str
    user: "UserOut"