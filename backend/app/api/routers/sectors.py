from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.auth import User
from app.models.monitoring import SecurityEvent
from app.models.sectors import (
    AmlSanctionsEntry,
    AmlScreeningResult,
    FraudAlert,
    OtAlert,
    OtController,
    OtSensorReading,
    SectorStatus,
    SwiftAssessment,
    SwiftControl,
    Transaction,
    UebaBehaviorEvent,
    UebaEntityProfile,
)
from app.schemas.sectors import (
    AmlScreenRequest,
    AmlScreenResult,
    ControllerCreate,
    ControllerResponse,
    FraudAlertResponse,
    OtAlertResponse,
    SectorStatusResponse,
    SensorReadingCreate,
    SensorReadingResponse,
    SwiftAssessmentUpdate,
    SwiftControlWithStatus,
    TransactionCreate,
    TransactionResponse,
    UebaEntityResponse,
    UebaEventCreate,
)
from app.services.aml_screening import screen_name
from app.services.audit import log_action
from app.services.fraud_scoring import score_transaction
from app.services.ueba_scoring import update_baseline_and_score

banking_router = APIRouter(prefix="/api/banking", tags=["banking"])
ot_scada_router = APIRouter(prefix="/api/ot-scada", tags=["ot-scada"])
ueba_router = APIRouter(prefix="/api/ueba", tags=["ueba"])
swift_csp_router = APIRouter(prefix="/api/swift-csp", tags=["swift-csp"])
aml_router = APIRouter(prefix="/api/aml", tags=["aml"])
sector_monitor_router = APIRouter(prefix="/api/sector-monitor", tags=["sector-monitor"])

OT_ALERT_THRESHOLDS = {"temperature": 80.0, "pressure": 150.0, "vibration": 10.0}


@banking_router.post("/transactions", response_model=TransactionResponse)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    score, reasons = score_transaction(payload.account_from, payload.account_to, payload.amount, payload.channel)
    tx = Transaction(**payload.model_dump(), risk_score=score)
    db.add(tx)
    db.flush()
    if score >= 50:
        db.add(FraudAlert(transaction_id=tx.id, reason="; ".join(reasons), severity="high" if score >= 80 else "medium"))
        db.add(SecurityEvent(source="banking", event_type="fraud_alert", detail=f"Transaction {tx.id}: {'; '.join(reasons)}"))
    db.commit()
    db.refresh(tx)
    return tx


@banking_router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Transaction).order_by(Transaction.id.desc()).limit(200).all()


@banking_router.get("/fraud-alerts", response_model=list[FraudAlertResponse])
def list_fraud_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FraudAlert).order_by(FraudAlert.id.desc()).limit(200).all()


@ot_scada_router.get("/controllers", response_model=list[ControllerResponse])
def list_controllers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(OtController).all()


@ot_scada_router.post("/controllers", response_model=ControllerResponse, dependencies=[Depends(require_role("analyst"))])
def create_controller(payload: ControllerCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    controller = OtController(**payload.model_dump())
    db.add(controller)
    db.commit()
    db.refresh(controller)
    return controller


@ot_scada_router.post("/readings", response_model=SensorReadingResponse)
def ingest_reading(payload: SensorReadingCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    controller = db.get(OtController, payload.controller_id)
    if controller is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Controller not found")
    reading = OtSensorReading(**payload.model_dump())
    db.add(reading)
    threshold = OT_ALERT_THRESHOLDS.get(payload.metric)
    if threshold is not None and payload.value > threshold:
        db.add(
            OtAlert(
                controller_id=payload.controller_id,
                description=f"{payload.metric} reading {payload.value} exceeded threshold {threshold}",
                severity="high",
            )
        )
        db.add(SecurityEvent(source="ot_scada", event_type="ot_threshold_exceeded",
                              detail=f"Controller {controller.name}: {payload.metric}={payload.value}"))
    db.commit()
    db.refresh(reading)
    return reading


@ot_scada_router.get("/alerts", response_model=list[OtAlertResponse])
def list_ot_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(OtAlert).order_by(OtAlert.id.desc()).limit(200).all()


@ueba_router.post("/events", response_model=UebaEntityResponse)
def record_behavior_event(payload: UebaEventCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entity = db.query(UebaEntityProfile).filter(UebaEntityProfile.entity_name == payload.entity_name).first()
    if entity is None:
        entity = UebaEntityProfile(entity_name=payload.entity_name)
        db.add(entity)
        db.flush()

    new_baseline, anomaly_score = update_baseline_and_score(entity.baseline_json, payload.value)
    entity.baseline_json = new_baseline
    entity.risk_score = anomaly_score
    db.add(UebaBehaviorEvent(entity_id=entity.id, action=payload.action, anomaly_score=anomaly_score))

    if anomaly_score > 3:
        db.add(SecurityEvent(source="ueba", event_type="behavior_anomaly",
                              detail=f"{payload.entity_name} anomaly score {anomaly_score} on action '{payload.action}'"))
    db.commit()
    db.refresh(entity)
    return entity


@ueba_router.get("/entities", response_model=list[UebaEntityResponse])
def list_entities(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UebaEntityProfile).order_by(UebaEntityProfile.risk_score.desc()).all()


@swift_csp_router.get("/controls", response_model=list[SwiftControlWithStatus])
def list_swift_controls(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    controls = db.query(SwiftControl).all()
    result = []
    for control in controls:
        latest = (
            db.query(SwiftAssessment)
            .filter(SwiftAssessment.control_id == control.id)
            .order_by(SwiftAssessment.id.desc())
            .first()
        )
        result.append(
            SwiftControlWithStatus(
                id=control.id, control_code=control.control_code, title=control.title,
                category=control.category, status=latest.status if latest else "not_assessed",
            )
        )
    return result


@swift_csp_router.post("/assessments", dependencies=[Depends(require_role("analyst"))])
def assess_control(payload: SwiftAssessmentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    control = db.get(SwiftControl, payload.control_id)
    if control is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
    assessment = SwiftAssessment(control_id=payload.control_id, status=payload.status, notes=payload.notes)
    db.add(assessment)
    db.commit()
    log_action(db, user.id, "swift_control_assessed", "swift_csp", detail=f"{control.control_code} -> {payload.status}")
    return {"ok": True}


@aml_router.post("/screen", response_model=AmlScreenResult)
def screen(payload: AmlScreenRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entries = db.query(AmlSanctionsEntry).all()
    matched_entry, score = screen_name(payload.full_name, entries)
    db.add(
        AmlScreeningResult(
            query_name=payload.full_name,
            matched_entry_id=matched_entry.id if matched_entry and score >= 60 else None,
            match_score=score,
            screened_by_id=user.id,
        )
    )
    db.commit()
    return AmlScreenResult(
        query_name=payload.full_name,
        matched_name=matched_entry.full_name if matched_entry and score >= 60 else None,
        match_score=score,
        list_source=matched_entry.list_source if matched_entry and score >= 60 else None,
    )


@aml_router.get("/watchlist")
def list_watchlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(AmlSanctionsEntry).all()


@sector_monitor_router.get("/status", response_model=list[SectorStatusResponse])
def sector_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from datetime import datetime, timezone

    sectors = ["government", "banking", "payments", "health", "banking_software"]
    results = []
    for sector in sectors:
        row = db.query(SectorStatus).filter(SectorStatus.sector == sector).first()
        if row is None:
            row = SectorStatus(sector=sector, open_alerts=0, compliance_score=0.0)
            db.add(row)
            db.flush()
        row.updated_at = datetime.now(timezone.utc)
        results.append(row)
    db.commit()
    return results
