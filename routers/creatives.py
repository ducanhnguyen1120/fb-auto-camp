from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Creative

router = APIRouter(prefix="/api/v1/creatives", tags=["creatives"])

class CreativeIn(BaseModel):
    name: str
    size: Optional[str] = None
    type: Optional[str] = None
    app: Optional[str] = None
    style: Optional[str] = None
    target: Optional[str] = None
    custom: Optional[str] = None
    file_path: Optional[str] = None

@router.get("")
def list_creatives(db: Session = Depends(get_db)):
    rows = db.query(Creative).order_by(Creative.id).all()
    return {"success": True, "data": [_out(r) for r in rows]}

@router.post("")
def create_creative(body: CreativeIn, db: Session = Depends(get_db)):
    row = Creative(**body.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _out(row)}

@router.delete("/{cid}")
def delete_creative(cid: int, db: Session = Depends(get_db)):
    row = db.query(Creative).filter(Creative.id == cid).first()
    if not row: raise HTTPException(404, "Not found")
    db.delete(row); db.commit()
    return {"success": True, "data": None}

def _out(r):
    return {"id": r.id, "name": r.name, "size": r.size, "type": r.type, "app": r.app, "style": r.style, "target": r.target, "custom": r.custom, "filePath": r.file_path}
