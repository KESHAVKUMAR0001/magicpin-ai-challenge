"""bot.py — Core entry point for message composition."""
from __future__ import annotations
from typing import Optional, Dict, Any
from app.composer import global_composer

def compose(
    category: Dict[str, Any],
    merchant: Dict[str, Any],
    trigger: Dict[str, Any],
    customer: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Composes a targeted WhatsApp engagement message.

    Inputs:
        category: dict (CategoryContext)
        merchant: dict (MerchantContext)
        trigger: dict (TriggerContext)
        customer: dict | None (CustomerContext)

    Returns:
        dict with keys: body, cta, send_as, suppression_key, rationale
    """
    return global_composer.compose(category, merchant, trigger, customer)

if __name__ == "__main__":
    import json
    sample_cat = {"slug": "dentists", "offer_catalog": [{"title": "Dental Cleaning @ ₹299"}]}
    sample_mer = {"identity": {"name": "Dr. Meera's Clinic", "owner_first_name": "Meera", "locality": "Lajpat Nagar"}}
    sample_trg = {"id": "trg_test_01", "kind": "research_digest", "payload": {"top_item": {"title": "Fluoride study", "source": "JIDA Oct 2026", "trial_n": 2100}}}
    
    print(json.dumps(compose(sample_cat, sample_mer, sample_trg), indent=2))
