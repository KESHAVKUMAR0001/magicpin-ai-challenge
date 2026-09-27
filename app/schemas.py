"""Pydantic schemas for context models and HTTP endpoints."""
from __future__ import annotations
from typing import Literal, Optional, Any, Dict, List
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Context Models (4-Context Framework)
# ---------------------------------------------------------------------------

class OfferTemplate(BaseModel):
    id: str
    title: str
    value: Optional[str] = None
    audience: Optional[str] = "all"
    type: Optional[str] = "service_at_price"

class VoiceProfile(BaseModel):
    tone: str = "peer_clinical"
    vocab_allowed: List[str] = Field(default_factory=list)
    vocab_taboo: List[str] = Field(default_factory=list)

class PeerStats(BaseModel):
    avg_rating: float = 4.4
    avg_reviews: int = 50
    avg_ctr: float = 0.030

class DigestItem(BaseModel):
    id: str
    kind: str
    title: str
    source: str
    summary: Optional[str] = None
    patient_segment: Optional[str] = None
    trial_n: Optional[int] = None

class CategoryContext(BaseModel):
    slug: str
    offer_catalog: List[OfferTemplate] = Field(default_factory=list)
    voice: VoiceProfile = Field(default_factory=VoiceProfile)
    peer_stats: PeerStats = Field(default_factory=PeerStats)
    digest: List[DigestItem] = Field(default_factory=list)
    patient_content_library: List[Dict[str, Any]] = Field(default_factory=list)
    seasonal_beats: List[Dict[str, Any]] = Field(default_factory=list)
    trend_signals: List[Dict[str, Any]] = Field(default_factory=list)

class Identity(BaseModel):
    name: str
    city: str
    locality: str
    verified: bool = True
    languages: List[str] = Field(default_factory=lambda: ["en", "hi"])
    owner_first_name: Optional[str] = None

class Subscription(BaseModel):
    status: str = "active"
    days_remaining: int = 30
    plan: str = "Pro"

class PerformanceSnapshot(BaseModel):
    window_days: int = 30
    views: int = 0
    calls: int = 0
    directions: int = 0
    ctr: float = 0.0
    delta_7d: Dict[str, float] = Field(default_factory=dict)

class MerchantOffer(BaseModel):
    id: str
    title: str
    status: str = "active"

class CustomerAggregate(BaseModel):
    total_unique_ytd: int = 0
    lapsed_180d_plus: int = 0
    retention_6mo_pct: float = 0.0
    high_risk_adult_count: Optional[int] = None

class MerchantContext(BaseModel):
    merchant_id: str
    category_slug: Optional[str] = None
    identity: Identity
    subscription: Subscription = Field(default_factory=Subscription)
    performance: PerformanceSnapshot = Field(default_factory=PerformanceSnapshot)
    offers: List[MerchantOffer] = Field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    customer_aggregate: CustomerAggregate = Field(default_factory=CustomerAggregate)
    signals: List[str] = Field(default_factory=list)

class TriggerContext(BaseModel):
    id: str
    scope: Literal["merchant", "customer"] = "merchant"
    kind: str
    source: Literal["external", "internal"] = "internal"
    payload: Dict[str, Any] = Field(default_factory=dict)
    urgency: int = 3
    suppression_key: str = ""
    expires_at: Optional[str] = None

class CustomerIdentity(BaseModel):
    name: str
    phone: Optional[str] = None
    language_pref: str = "hi-en mix"

class CustomerContext(BaseModel):
    customer_id: str
    merchant_id: str
    identity: CustomerIdentity
    relationship: Dict[str, Any] = Field(default_factory=dict)
    state: Literal["new", "active", "lapsed_soft", "lapsed_hard", "churned"] = "active"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    consent: Dict[str, Any] = Field(default_factory=dict)

# ---------------------------------------------------------------------------
# 2. Composition Output Model
# ---------------------------------------------------------------------------

class ComposedMessage(BaseModel):
    body: str
    cta: Literal["binary_yes_stop", "open_ended", "none"] = "open_ended"
    send_as: Literal["vera", "merchant_on_behalf"] = "vera"
    suppression_key: str
    rationale: str
    test_id: Optional[str] = None

# ---------------------------------------------------------------------------
# 3. HTTP API Endpoint Schemas
# ---------------------------------------------------------------------------

class HealthzResponse(BaseModel):
    status: str = "ok"
    uptime_seconds: int
    contexts_loaded: Dict[str, int]

class MetadataResponse(BaseModel):
    team_name: str
    team_members: List[str]
    model: str
    approach: str
    contact_email: str
    version: str
    submitted_at: str

class ContextPushRequest(BaseModel):
    scope: Literal["category", "merchant", "customer", "trigger"]
    context_id: str
    version: int
    delivered_at: str
    payload: Dict[str, Any]

class ContextPushSuccessResponse(BaseModel):
    accepted: bool = True
    ack_id: str
    stored_at: str

class ContextPushConflictResponse(BaseModel):
    accepted: bool = False
    reason: str = "stale_version"
    current_version: int

class TickAction(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    send_as: Literal["vera", "merchant_on_behalf"] = "vera"
    trigger_id: str
    template_name: Optional[str] = None
    template_params: Optional[List[str]] = None
    body: str
    cta: str
    suppression_key: str
    rationale: str

class TickRequest(BaseModel):
    now: str
    available_triggers: List[str]

class TickResponse(BaseModel):
    actions: List[TickAction]

class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    from_role: Literal["merchant", "customer"] = "merchant"
    message: str
    received_at: str
    turn_number: int

class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str
