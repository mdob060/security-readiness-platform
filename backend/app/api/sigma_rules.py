from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class SigmaRuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    level: str = "medium"
    category: Optional[str] = None
    detection: Optional[str] = None
    tags: Optional[str] = None
    author: Optional[str] = None


@router.get("/")
def list_sigma_rules(db: Session = Depends(get_db), level: Optional[str] = None):
    query = db.query(models.SigmaRule)
    if level:
        query = query.filter(models.SigmaRule.level == level)
    rules = query.order_by(models.SigmaRule.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "level": r.level,
            "category": r.category,
            "detection": r.detection,
            "tags": r.tags,
            "author": r.author,
            "is_active": r.is_active,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


@router.post("/")
def create_sigma_rule(rule: SigmaRuleCreate, db: Session = Depends(get_db)):
    db_rule = models.SigmaRule(**rule.model_dump(), status="stable", is_active=True)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.patch("/{rule_id}/toggle")
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(models.SigmaRule).filter(models.SigmaRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    db.commit()
    return {"id": rule_id, "is_active": rule.is_active}
