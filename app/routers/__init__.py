# app/routers/__init__.py

from .auth import router as admin_auth_router
from .auth_login import router as auth_login_router
from .churches import router as churches_router
from .members import router as members_router
from .news import router as news_router

__all__ = [
    "admin_auth_router",
    "auth_login_router",
    "churches_router",
    "members_router",
    "news_router",
]
