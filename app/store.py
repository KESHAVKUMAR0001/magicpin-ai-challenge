"""In-memory thread-safe store for contexts and active conversations."""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

class ContextStore:
    """Stores context layers (category, merchant, customer, trigger) and conversation state."""

    def __init__(self):
        self._lock = threading.RLock()
        self._start_time = datetime.utcnow()
        
        # Scoped storage: scope -> context_id -> {"version": int, "payload": dict, "updated_at": str}
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {
            "category": {},
            "merchant": {},
            "customer": {},
            "trigger": {}
        }
        
        # Conversation history tracking for multi-turn dialogues
        self._conversations: Dict[str, Dict[str, Any]] = {}

    def get_uptime_seconds(self) -> int:
        """Returns uptime in seconds since store initialization."""
        return int((datetime.utcnow() - self._start_time).total_seconds())

    def get_counts(self) -> Dict[str, int]:
        """Returns total loaded context objects per scope."""
        with self._lock:
            return {
                scope: len(self._store[scope])
                for scope in ["category", "merchant", "customer", "trigger"]
            }

    def push_context(self, scope: str, context_id: str, version: int, payload: dict) -> Tuple[bool, str, Optional[int]]:
        """
        Stores or updates a context object atomically.
        
        Returns:
            (success: bool, ack_id_or_reason: str, current_version: Optional[int])
        """
        if scope not in self._store:
            return False, "invalid_scope", None

        with self._lock:
            existing = self._store[scope].get(context_id)
            if existing:
                current_ver = existing["version"]
                # Reject stale updates with lower version numbers
                if version < current_ver:
                    return False, "stale_version", current_ver
                # Accept identical version re-push as idempotent no-op
                elif version == current_ver:
                    ack_id = f"ack_{context_id}_v{version}"
                    return True, ack_id, current_ver

            # Save or replace higher version atomically
            self._store[scope][context_id] = {
                "version": version,
                "payload": payload,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            ack_id = f"ack_{context_id}_v{version}"
            return True, ack_id, version

    def get_context(self, scope: str, context_id: str) -> Optional[dict]:
        """Retrieves payload for a specific scope and context_id."""
        with self._lock:
            entry = self._store.get(scope, {}).get(context_id)
            return entry["payload"] if entry else None

    def get_category_by_slug(self, slug: str) -> Optional[dict]:
        """Retrieves category context by slug matching."""
        with self._lock:
            if slug in self._store["category"]:
                return self._store["category"][slug]["payload"]
            for entry in self._store["category"].values():
                payload = entry["payload"]
                if payload.get("slug") == slug:
                    return payload
            return None

    def get_all_active_triggers(self) -> Dict[str, dict]:
        """Returns all loaded trigger contexts."""
        with self._lock:
            return {cid: entry["payload"] for cid, entry in self._store["trigger"].items()}

    def get_conversation_state(self, conv_id: str) -> Optional[dict]:
        """Retrieves active conversation state by conversation_id."""
        with self._lock:
            return self._conversations.get(conv_id)

    def save_conversation_state(self, conv_id: str, state: dict):
        """Saves conversation state."""
        with self._lock:
            self._conversations[conv_id] = state

global_store = ContextStore()
