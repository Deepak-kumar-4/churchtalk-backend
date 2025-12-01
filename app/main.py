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

# 🔓 CORS: allow everything for now (safe enough for your demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(admin_auth_router)
app.include_router(auth_login_router)
app.include_router(churches_router)
app.include_router(members_router)
app.include_router(news_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
