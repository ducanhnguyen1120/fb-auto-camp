from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Package

router = APIRouter(prefix="/api/v1/packages", tags=["packages"])

class PackageIn(BaseModel):
    name: str
    app_id: Optional[int] = None
    target_id: Optional[int] = None
    ad_id: Optional[int] = None

@router.get("")
def list_packages(db: Session = Depends(get_db)):
    rows = db.query(Package).order_by(Package.id).all()
    return {"success": True, "data": [_out(r) for r in rows]}

@router.post("")
def create_package(body: PackageIn, db: Session = Depends(get_db)):
    row = Package(**body.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _out(row)}

@router.put("/{pid}")
def update_package(pid: int, body: PackageIn, db: Session = Depends(get_db)):
    row = db.query(Package).filter(Package.id == pid).first()
    if not row: raise HTTPException(404, "Not found")
    for k, v in body.model_dump().items(): setattr(row, k, v)
    db.commit(); db.refresh(row)
    return {"success": True, "data": _out(row)}

@router.delete("/{pid}")
def delete_package(pid: int, db: Session = Depends(get_db)):
    row = db.query(Package).filter(Package.id == pid).first()
    if not row: raise HTTPException(404, "Not found")
    db.delete(row); db.commit()
    return {"success": True, "data": None}

def _out(r): return {"id": r.id, "name": r.name, "appId": r.app_id, "targetId": r.target_id, "adId": r.ad_id}
