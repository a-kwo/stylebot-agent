import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from database import init_db
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.wardrobe_router import router as wardrobe_router
from routers.profile_router import router as profile_router, quiz_router
from routers.outfits_router import router as outfits_router
from routers.image_router import router as image_router

app = FastAPI(title="StyleBot Agent")

init_db()

# Serve locally-stored wardrobe images
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
(uploads_dir / "wardrobe").mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Serve AI-generated quiz images
quiz_images_dir = Path(__file__).parent / "static" / "quiz_images"
quiz_images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/quiz_images", StaticFiles(directory=quiz_images_dir), name="quiz-images")

# API routers — must be registered before static file handling
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(wardrobe_router)
app.include_router(profile_router)
app.include_router(quiz_router)
app.include_router(outfits_router)
app.include_router(image_router)

# Static file serving: mount _next assets, then catch-all for HTML pages
frontend_dir = Path(__file__).parent / "frontend" / "out"
static_dir = Path(__file__).parent / "static"

if frontend_dir.exists():
    # Serve Next.js static assets (JS/CSS bundles)
    next_assets = frontend_dir / "_next"
    if next_assets.exists():
        app.mount("/_next", StaticFiles(directory=next_assets), name="next-assets")

    @app.get("/{path:path}")
    def serve_frontend(path: str):
        # Try exact file first
        file_path = frontend_dir / path
        if file_path.is_file():
            return FileResponse(file_path)

        # Try with .html extension (Next.js static export pattern)
        html_path = frontend_dir / f"{path}.html"
        if html_path.is_file():
            return FileResponse(html_path)

        # Fall back to index.html for SPA routing
        index_path = frontend_dir / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)

        return Response(status_code=404)

elif static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
