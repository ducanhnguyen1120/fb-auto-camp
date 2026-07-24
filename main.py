from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
import models  # noqa

Base.metadata.create_all(bind=engine)

from routers import accounts, templates, packages, creatives, campaign, upload

UPLOADS_DIR = Path(__file__).parent / "uploads"
CLEAN_DAYS = 15


def _auto_clean():
    if not UPLOADS_DIR.exists():
        return
    cutoff = datetime.now() - timedelta(days=CLEAN_DAYS)
    db = SessionLocal()
    try:
        for f in UPLOADS_DIR.iterdir():
            if not f.is_file():
                continue
            if datetime.fromtimestamp(f.stat().st_mtime) > cutoff:
                continue
            cr = db.query(models.Creative).filter(models.Creative.file_path == str(f)).first()
            if not cr:
                f.unlink(missing_ok=True)
                continue
            has_meta = db.query(models.CreativeMetaAsset).filter(
                models.CreativeMetaAsset.creative_id == cr.id
            ).first()
            if has_meta:
                f.unlink(missing_ok=True)
                cr.file_path = cr.name
                db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app):
    _auto_clean()
    yield


app = FastAPI(title="FB Auto Camp", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(templates.router)
app.include_router(packages.router)
app.include_router(creatives.router)
app.include_router(campaign.router)
app.include_router(upload.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
