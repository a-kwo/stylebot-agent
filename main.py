import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.wardrobe_router import router as wardrobe_router
from routers.profile_router import router as profile_router

app = FastAPI(title="StyleBot Agent")

init_db()

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(wardrobe_router)
app.include_router(profile_router)

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
