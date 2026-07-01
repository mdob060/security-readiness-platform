from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.auth import User
from app.models.intelligence import AiMessage, Conversation, FederationPeer, Ioc, SharedIndicator, SoarDecision, ThreatActor
from app.schemas.intelligence import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    FederationPeerCreate,
    FederationPeerResponse,
    IocCreate,
    IocResponse,
    SoarDecisionResponse,
    SoarDecisionReview,
    ThreatActorResponse,
)
from app.services.audit import log_action
from app.services.ollama_client import generate_response

ai_brain_router = APIRouter(prefix="/api/ai-brain", tags=["ai-brain"])
automation_router = APIRouter(prefix="/api/automation", tags=["automation"])
threat_intel_router = APIRouter(prefix="/api/threat-intel", tags=["threat-intel"])
federation_router = APIRouter(prefix="/api/federation", tags=["federation"])


@ai_brain_router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.id.desc()).all()


@ai_brain_router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.conversation_id:
        conversation = db.get(Conversation, payload.conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    else:
        conversation = Conversation(user_id=user.id, title=payload.message[:60])
        db.add(conversation)
        db.flush()

    history = [
        {"role": m.role, "content": m.content}
        for m in db.query(AiMessage).filter(AiMessage.conversation_id == conversation.id).order_by(AiMessage.id)
    ]

    db.add(AiMessage(conversation_id=conversation.id, role="user", content=payload.message))
    answer, used_llm = generate_response(payload.message, history)
    db.add(AiMessage(conversation_id=conversation.id, role="assistant", content=answer))
    db.commit()

    return ChatResponse(conversation_id=conversation.id, answer=answer, used_local_llm=used_llm)


@automation_router.get("/decisions", response_model=list[SoarDecisionResponse])
def list_decisions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SoarDecision).order_by(SoarDecision.id.desc()).limit(200).all()


@automation_router.post(
    "/decisions/{decision_id}/review",
    response_model=SoarDecisionResponse,
    dependencies=[Depends(require_role("analyst"))],
)
def review_decision(
    decision_id: int,
    payload: SoarDecisionReview,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone

    decision = db.get(SoarDecision, decision_id)
    if decision is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Decision not found")
    decision.status = "approved" if payload.approve else "rejected"
    decision.reviewed_by_id = user.id
    decision.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    log_action(db, user.id, "soar_decision_reviewed", "automation", detail=f"{decision_id} -> {decision.status}")
    return decision


@threat_intel_router.get("/actors", response_model=list[ThreatActorResponse])
def list_actors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ThreatActor).order_by(ThreatActor.name).all()


@threat_intel_router.get("/iocs", response_model=list[IocResponse])
def list_iocs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Ioc).order_by(Ioc.id.desc()).limit(500).all()


@threat_intel_router.post("/iocs", response_model=IocResponse, dependencies=[Depends(require_role("analyst"))])
def create_ioc(payload: IocCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ioc = Ioc(**payload.model_dump())
    db.add(ioc)
    db.commit()
    db.refresh(ioc)
    return ioc


@federation_router.get("/peers", response_model=list[FederationPeerResponse])
def list_peers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FederationPeer).order_by(FederationPeer.id.desc()).all()


@federation_router.post("/peers", response_model=FederationPeerResponse, dependencies=[Depends(require_role("admin"))])
def create_peer(payload: FederationPeerCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    peer = FederationPeer(**payload.model_dump())
    db.add(peer)
    db.commit()
    db.refresh(peer)
    return peer


@federation_router.get("/taxii2/collections")
def taxii_collections(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Minimal STIX/TAXII 2.1-style collection listing backed by local IOCs."""
    ioc_count = db.query(Ioc).count()
    return {
        "collections": [
            {
                "id": "dira-local-iocs",
                "title": "Dir'a Local Indicators",
                "can_read": True,
                "can_write": False,
                "media_types": ["application/stix+json;version=2.1"],
                "object_count": ioc_count,
            }
        ]
    }


@federation_router.get("/taxii2/collections/dira-local-iocs/objects")
def taxii_objects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    iocs = db.query(Ioc).order_by(Ioc.id.desc()).limit(500).all()
    pattern_map = {"ip": "ipv4-addr", "domain": "domain-name", "hash": "file", "url": "url"}
    objects = [
        {
            "type": "indicator",
            "id": f"indicator--dira-{ioc.id}",
            "created": ioc.created_at.isoformat(),
            "pattern": f"[{pattern_map.get(ioc.ioc_type, 'x')}:value = '{ioc.value}']",
            "pattern_type": "stix",
            "confidence": ioc.confidence,
        }
        for ioc in iocs
    ]
    return {"objects": objects}
