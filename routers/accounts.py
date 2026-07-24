from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Account

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

class AccountIn(BaseModel):
    label: str
    acc_id: str
    note: Optional[str] = ""

@router.get("")
def list_accounts(db: Session = Depends(get_db)):
    rows = db.query(Account).order_by(Account.id).all()
    return {"success": True, "data": [_out(r) for r in rows]}

@router.post("")
def create_account(body: AccountIn, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.acc_id == body.acc_id).first()
    if existing:
        raise HTTPException(400, "acc_id already exists")
    row = Account(label=body.label, acc_id=body.acc_id, note=body.note or "")
    db.add(row); db.commit(); db.refresh(row)
    return {"success": True, "data": _out(row)}

@router.put("/{account_id}")
def update_account(account_id: int, body: AccountIn, db: Session = Depends(get_db)):
    row = db.query(Account).filter(Account.id == account_id).first()
    if not row:
        raise HTTPException(404, "Not found")
    row.label = body.label
    row.acc_id = body.acc_id
    row.note = body.note or ""
    db.commit(); db.refresh(row)
    return {"success": True, "data": _out(row)}

@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    row = db.query(Account).filter(Account.id == account_id).first()
    if not row:
        raise HTTPException(404, "Not found")
    db.delete(row); db.commit()
    return {"success": True, "data": None}

def _out(r):
    return {"id": r.id, "label": r.label, "accId": r.acc_id, "note": r.note or ""}
