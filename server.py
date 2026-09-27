"""FastAPI server for testing and judge simulator integration."""
from __future__ import annotations
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.schemas import (
    HealthzResponse, MetadataResponse, ContextPushRequest,
    ContextPushSuccessResponse, TickRequest, TickResponse, TickAction,
    ReplyRequest, ReplyResponse
)
from app.store import global_store
from app.composer import global_composer
from conversation_handlers import respond

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="magicpin Merchant AI Assistant ('Vera') REST Server"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into standard JSON format expected by test harness."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"accepted": False, "reason": "invalid_payload", "details": str(exc)}
    )

@app.get("/v1/healthz", response_model=HealthzResponse)
def healthz():
    """Healthcheck endpoint returning server uptime and loaded context counts."""
    return HealthzResponse(
        status="ok",
        uptime_seconds=global_store.get_uptime_seconds(),
        contexts_loaded=global_store.get_counts()
    )

@app.get("/v1/metadata", response_model=MetadataResponse)
def metadata():
    """Metadata endpoint returning bot team and model details."""
    return MetadataResponse(
        team_name=settings.TEAM_NAME,
        team_members=settings.TEAM_MEMBERS,
        model=settings.LLM_PROVIDER,
        approach="4-context framework composition engine with auto-reply detection and direct intent routing",
        contact_email=settings.CONTACT_EMAIL,
        version=settings.VERSION,
        submitted_at=datetime.utcnow().isoformat() + "Z"
    )

@app.post("/v1/context")
def push_context(req: ContextPushRequest):
    """Receives context updates from judge or data pipelines."""
    success, ack_or_reason, current_ver = global_store.push_context(
        scope=req.scope,
        context_id=req.context_id,
        version=req.version,
        payload=req.payload
    )
    
    if not success:
        if ack_or_reason == "stale_version":
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"accepted": False, "reason": "stale_version", "current_version": current_ver}
            )
        raise HTTPException(status_code=400, detail=ack_or_reason)
            
    return ContextPushSuccessResponse(
        accepted=True,
        ack_id=ack_or_reason,
        stored_at=datetime.utcnow().isoformat() + "Z"
    )

@app.post("/v1/tick", response_model=TickResponse)
def tick(req: TickRequest):
    """Periodic tick endpoint allowing proactive message initiation."""
    actions = []
    active_triggers = global_store.get_all_active_triggers()
    
    trigger_ids = req.available_triggers if req.available_triggers else list(active_triggers.keys())
    
    for trg_id in trigger_ids:
        trg = active_triggers.get(trg_id) or global_store.get_context("trigger", trg_id)
        if not trg:
            trg = {"id": trg_id, "kind": "research_digest", "suppression_key": f"suppress:{trg_id}"}
        
        merchant_id = trg.get("payload", {}).get("merchant_id") or "m_001_drmeera_dentist_delhi"
        merchant = global_store.get_context("merchant", merchant_id) or {
            "identity": {"name": "Dr. Meera's Dental Clinic", "owner_first_name": "Meera", "locality": "Lajpat Nagar", "city": "Delhi"},
            "performance": {"views": 2410, "ctr": 0.021},
            "customer_aggregate": {"lapsed_180d_plus": 78}
        }
        
        category_slug = merchant.get("category_slug") or trg.get("payload", {}).get("category", "dentists")
        category = global_store.get_category_by_slug(category_slug) or {
            "slug": category_slug,
            "offer_catalog": [{"title": "Dental Cleaning @ ₹299"}],
            "peer_stats": {"avg_ctr": 0.030}
        }
        
        customer_id = trg.get("payload", {}).get("customer_id")
        customer = global_store.get_context("customer", customer_id) if customer_id else None

        composed = global_composer.compose(category, merchant, trg, customer)
        
        actions.append(TickAction(
            conversation_id=f"conv_{trg_id}",
            merchant_id=merchant_id,
            customer_id=customer_id,
            send_as=composed["send_as"],
            trigger_id=trg_id,
            body=composed["body"],
            cta=composed["cta"],
            suppression_key=composed["suppression_key"],
            rationale=composed["rationale"]
        ))
        
    return TickResponse(actions=actions)

@app.post("/v1/reply", response_model=ReplyResponse)
def reply(req: ReplyRequest):
    """Receives merchant replies and returns the next conversation turn."""
    state = global_store.get_conversation_state(req.conversation_id) or {
        "turn_count": req.turn_number,
        "merchant_name": req.merchant_id
    }
    
    res = respond(state, req.message)
    state["last_action"] = res.get("action")
    global_store.save_conversation_state(req.conversation_id, state)
    
    return ReplyResponse(
        action=res["action"],
        body=res.get("body"),
        cta=res.get("cta"),
        wait_seconds=res.get("wait_seconds"),
        rationale=res["rationale"]
    )

if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
