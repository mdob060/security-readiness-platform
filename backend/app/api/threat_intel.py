from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class IOCCreate(BaseModel):
    indicator: str
    indicator_type: str
    threat_type: Optional[str] = None
    confidence: Optional[int] = 70
    source: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None


class IOCCheck(BaseModel):
    indicator: str


@router.get("/indicators")
def list_indicators(db: Session = Depends(get_db), indicator_type: Optional[str] = None):
    query = db.query(models.ThreatIntel).filter(models.ThreatIntel.is_active == True)
    if indicator_type:
        query = query.filter(models.ThreatIntel.indicator_type == indicator_type)
    iocs = query.order_by(models.ThreatIntel.confidence.desc()).all()
    return [
        {
            "id": i.id,
            "indicator": i.indicator,
            "indicator_type": i.indicator_type,
            "threat_type": i.threat_type,
            "confidence": i.confidence,
            "source": i.source,
            "description": i.description,
            "tags": i.tags,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in iocs
    ]


@router.post("/check")
def check_indicator(payload: IOCCheck, db: Session = Depends(get_db)):
    ioc = db.query(models.ThreatIntel).filter(
        models.ThreatIntel.indicator == payload.indicator,
        models.ThreatIntel.is_active == True,
    ).first()
    if ioc:
        return {
            "found": True,
            "indicator": ioc.indicator,
            "threat_type": ioc.threat_type,
            "confidence": ioc.confidence,
            "description": ioc.description,
            "source": ioc.source,
        }
    return {"found": False, "indicator": payload.indicator, "message": "No threat intelligence found"}


@router.post("/indicators")
def add_indicator(ioc: IOCCreate, db: Session = Depends(get_db)):
    db_ioc = models.ThreatIntel(**ioc.model_dump(), is_active=True)
    db.add(db_ioc)
    db.commit()
    db.refresh(db_ioc)
    return db_ioc
