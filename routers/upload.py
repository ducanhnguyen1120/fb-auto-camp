from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import aiofiles
from database import get_db
from models import Creative, CreativeMetaAsset
from services import meta_api

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/api/v1/creatives", tags=["upload"])


@router.post("/add-with-file")
async def add_with_file(
    file: UploadFile = File(...),
    app: str = Form(""),
    style: str = Form(""),
    target: str = Form(""),
    custom: str = Form(""),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "file").suffix or ".mp4"
    asset_type = "video" if suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"} else "image"
    name = Path(file.filename or "file").stem

    row = Creative(name=name, type=asset_type, app=app, style=style, target=target, custom=custom, file_path=name)
    db.add(row); db.commit(); db.refresh(row)

    local_path = UPLOADS_DIR / f"{row.id}{suffix}"
    async with aiofiles.open(local_path, "wb") as f:
        while chunk := await file.read(65536):
            await f.write(chunk)

    row.file_path = str(local_path)
    db.commit()

    return {"success": True, "data": {
        "id": row.id, "name": row.name, "type": row.type,
        "app": row.app, "style": row.style, "target": row.target, "custom": row.custom,
        "filePath": row.file_path,
    }}


@router.post("/{creative_id}/upload")
async def upload_to_meta(
    creative_id: int,
    acc_id: str = Form(...),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    cr = db.query(Creative).filter(Creative.id == creative_id).first()
    if not cr:
        raise HTTPException(404, "Creative không tồn tại")

    existing = db.query(CreativeMetaAsset).filter(
        CreativeMetaAsset.creative_id == creative_id,
        CreativeMetaAsset.acc_id == acc_id,
    ).first()
    if existing:
        return {"success": True, "data": {"metaId": existing.meta_id, "type": existing.asset_type, "cached": True}}

    # Ưu tiên đọc từ server file
    server_path = Path(cr.file_path) if cr.file_path and "uploads" in cr.file_path else None
    if server_path and server_path.exists():
        file_bytes = server_path.read_bytes()
        filename = server_path.name
    elif file:
        file_bytes = await file.read()
        filename = file.filename or cr.name
        # Lưu lại nếu chưa có trên server
        suffix = Path(filename).suffix or ".mp4"
        local_path = UPLOADS_DIR / f"{creative_id}{suffix}"
        if not local_path.exists():
            local_path.write_bytes(file_bytes)
            cr.file_path = str(local_path)
            db.commit()
    else:
        raise HTTPException(400, "File không có trên server và không được gửi kèm")

    asset_type = cr.type
    try:
        if asset_type == "video":
            meta_id = await meta_api.upload_video(acc_id, file_bytes, filename)
        else:
            meta_id = await meta_api.upload_image(acc_id, file_bytes, filename)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    asset = CreativeMetaAsset(creative_id=creative_id, acc_id=acc_id, asset_type=asset_type, meta_id=meta_id)
    db.add(asset); db.commit()

    return {"success": True, "data": {"metaId": meta_id, "type": asset_type, "cached": False}}


@router.get("/{creative_id}/file")
def serve_file(creative_id: int, db: Session = Depends(get_db)):
    cr = db.query(Creative).filter(Creative.id == creative_id).first()
    if not cr or not cr.file_path:
        raise HTTPException(404, "File chưa được upload")
    p = Path(cr.file_path)
    if not p.exists():
        raise HTTPException(404, "File không tồn tại trên server")
    return FileResponse(p)


@router.get("/{creative_id}/meta-assets")
def get_meta_assets(creative_id: int, db: Session = Depends(get_db)):
    rows = db.query(CreativeMetaAsset).filter(CreativeMetaAsset.creative_id == creative_id).all()
    return {"success": True, "data": [{"accId": r.acc_id, "metaId": r.meta_id, "type": r.asset_type} for r in rows]}
