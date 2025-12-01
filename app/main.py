# app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import (
    admin_auth_router,
    auth_login_router,
    churches_router,
    members_router,
    news_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Church Multi-tenant Backend (FastAPI)")

# ✅ CORS CONFIG – this MUST be exactly like this
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://churchtalk-frontend.vercel.app",  # your Vercel frontend (no trailing slash)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],   # allow Content-Type, Authorization, etc.
)

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Serve uploaded files (logos, news images)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(admin_auth_router)   # /auth/signup, /auth/* (admin)
app.include_router(auth_login_router)   # /auth/login
app.include_router(churches_router)
app.include_router(members_router)
app.include_router(news_router)


@app.get("/health")
def health_check():
  return {"status": "ok"}
