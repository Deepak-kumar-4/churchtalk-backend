# app/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(Text, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # store hashed password
    password_reset = Column(JSONB, nullable=True)  # {token, expiration, used}
    is_admin = Column(Boolean, default=False)
    age = Column(Integer, nullable=True)
    gender = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    address = Column(Text, nullable=True)

    churches_created = relationship("Church", back_populates="creator")
    news_created = relationship("NewsAdmin", back_populates="creator")
    memberships = relationship("ChurchMember", back_populates="user_obj")


class Church(Base):
    __tablename__ = "churches"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    contact_number = Column(Text, nullable=True)
    short_description = Column(Text, nullable=True)
    logo = Column(Text, nullable=True)  # store URL or path as text
    created_by = Column(Integer, ForeignKey("user.id"))

    creator = relationship("User", back_populates="churches_created")
    members = relationship("ChurchMember", back_populates="church_obj")
    news_posts = relationship("NewsAdmin", back_populates="church")


class ChurchMember(Base):
    __tablename__ = "church_members"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = Column(Integer, ForeignKey("user.id"), nullable=False)
    church = Column(Integer, ForeignKey("churches.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    user_obj = relationship("User", back_populates="memberships")
    church_obj = relationship("Church", back_populates="members")

class NewsAdmin(Base):
    __tablename__ = "news_admin"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    image = Column(Text, nullable=True)  # store image URL or path
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

    church = relationship("Church", back_populates="news_posts")
    creator = relationship("User", back_populates="news_created")


