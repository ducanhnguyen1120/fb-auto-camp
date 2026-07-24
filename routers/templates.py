from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import TemplateApp, TemplateTarget, TemplateAd

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# --- APP ---
class AppIn(BaseModel):
    name: str
    pkg: Optional[str] = ""
    app_id: Optional[str] = ""
    dev_id: Optional[str] = ""
    page_id: Optional[str] = ""
    app_url: Optional[str] = ""

@router.get("/app")
def list_app(db: Session = Depends(get_db)):
    rows = db.query(TemplateApp).order_by(TemplateApp.id).all()
    return {"success": True, "data": [_app_out(r) for r in rows]}

@router.post("/app")
def create_app(body: AppIn, db: Session = Depends(get_db)):
    row = TemplateApp(**body.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _app_out(row)}

@router.put("/app/{tid}")
def update_app(tid: int, body: AppIn, db: Session = Depends(get_db)):
    row = db.query(TemplateApp).filter(TemplateApp.id == tid).first()
    if not row: raise HTTPException(404, "Not found")
    for k, v in body.model_dump().items(): setattr(row, k, v)
    db.commit(); db.refresh(row)
    return {"success": True, "data": _app_out(row)}

@router.delete("/app/{tid}")
def delete_app(tid: int, db: Session = Depends(get_db)):
    row = db.query(TemplateApp).filter(TemplateApp.id == tid).first()
    if not row: raise HTTPException(404, "Not found")
    db.delete(row); db.commit()
    return {"success": True, "data": None}

def _app_out(r):
    return {"id": r.id, "name": r.name, "pkg": r.pkg, "appId": r.app_id, "devId": r.dev_id, "pageId": r.page_id, "appUrl": r.app_url}

# --- TARGET ---
class TargetIn(BaseModel):
    name: str
    country: List[str] = []
    lang: List[str] = []
    gender: str = "all"
    age_min: int = 18
    age_max: int = 45
    budget_type: str = "CBO"
    budget: float = 0

@router.get("/target")
def list_target(db: Session = Depends(get_db)):
    rows = db.query(TemplateTarget).order_by(TemplateTarget.id).all()
    return {"success": True, "data": [_tgt_out(r) for r in rows]}

@router.post("/target")
def create_target(body: TargetIn, db: Session = Depends(get_db)):
    row = TemplateTarget(**body.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _tgt_out(row)}

@router.put("/target/{tid}")
def update_target(tid: int, body: TargetIn, db: Session = Depends(get_db)):
    row = db.query(TemplateTarget).filter(TemplateTarget.id == tid).first()
    if not row: raise HTTPException(404, "Not found")
    for k, v in body.model_dump().items(): setattr(row, k, v)
    db.commit(); db.refresh(row)
    return {"success": True, "data": _tgt_out(row)}

@router.delete("/target/{tid}")
def delete_target(tid: int, db: Session = Depends(get_db)):
    row = db.query(TemplateTarget).filter(TemplateTarget.id == tid).first()
    if not row: raise HTTPException(404, "Not found")
    db.delete(row); db.commit()
    return {"success": True, "data": None}

def _tgt_out(r):
    return {"id": r.id, "name": r.name, "country": r.country or [], "lang": r.lang or [], "gender": r.gender, "ageMin": r.age_min, "ageMax": r.age_max, "budgetType": r.budget_type, "budget": r.budget}

# --- AD ---
class AdIn(BaseModel):
    name: str
    headlines: Optional[str] = ""
    text: Optional[str] = ""
    cr_count: int = 1

@router.get("/ad")
def list_ad(db: Session = Depends(get_db)):
    rows = db.query(TemplateAd).order_by(TemplateAd.id).all()
    return {"success": True, "data": [_ad_out(r) for r in rows]}

@router.post("/ad")
def create_ad(body: AdIn, db: Session = Depends(get_db)):
    row = TemplateAd(**body.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _ad_out(row)}

@router.put("/ad/{tid}")
def update_ad(tid: int, body: AdIn, db: Session = Depends(get_db)):
    row = db.query(TemplateAd).filter(TemplateAd.id == tid).first()
    if not row: raise HTTPException(404, "Not found")
    for k, v in body.model_dump().items(): setattr(row, k, v)
    db.commit(); db.refresh(row)
    return {"success": True, "data": _ad_out(row)}

@router.delete("/ad/{tid}")
def delete_ad(tid: int, db: Session = Depends(get_db)):
    row = db.query(TemplateAd).filter(TemplateAd.id == tid).first()
    if not row: raise HTTPException(404, "Not found")
    db.delete(row); db.commit()
    return {"success": True, "data": None}

def _ad_out(r):
    return {"id": r.id, "name": r.name, "headlines": r.headlines, "text": r.text, "crCount": r.cr_count}
