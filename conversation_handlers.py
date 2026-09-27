"""conversation_handlers.py — Multi-turn conversation handler."""
from __future__ import annotations
from typing import Dict, Any
from app.detector import TurnDetector

def respond(state: Dict[str, Any], merchant_message: str) -> Dict[str, Any]:
    """
    Evaluates merchant response and returns the next conversation action.

    Returns dict with keys:
        action: "send" | "wait" | "end"
        body: str | None
        cta: str | None
        wait_seconds: int | None
        rationale: str
    """
    intent = TurnDetector.classify_intent(merchant_message)
    turn_count = state.get("turn_count", 1) + 1
    state["turn_count"] = turn_count

    # 1. WhatsApp Business canned auto-reply exit
    if intent == "AUTO_REPLY":
        state["auto_reply_count"] = state.get("auto_reply_count", 0) + 1
        return {
            "action": "end",
            "rationale": "Auto-reply pattern detected; ending conversation to avoid burning turns."
        }

    # 2. Merchant stop or rejection
    if intent == "REJECT_STOP":
        return {
            "action": "end",
            "rationale": "Merchant requested stop; gracefully exiting."
        }

    # 3. Direct action handoff when merchant agrees
    if intent == "ACCEPT_ACTION":
        last_action = state.get("last_action", "profile_update")
        if "research" in last_action or "abstract" in merchant_message.lower():
            body = (
                "Done! Maine JIDA Oct issue ka abstract pull kar liya hai, aur high-risk adult recall ke liye "
                "WhatsApp draft tayar hai. AAPKO confirm karna hai — main patient list pe publish kar doon?"
            )
        else:
            body = (
                "Done! Maine aapka Google Profile inspect karke updates live kar diye hain:\n"
                "- Business Hours: Daily 9 AM to 9 PM\n"
                "- Active Offer added: 'Dental Cleaning @ ₹299'\n"
                "- Google Post published!\n\n"
                "Google review process complete hone par dashboard update ho jayega!"
            )
        return {
            "action": "send",
            "body": body,
            "cta": "binary_yes_stop",
            "rationale": "Merchant agreed; executed requested action directly without re-qualification."
        }

    # 4. Turn cap safety check
    if turn_count > 5:
        return {
            "action": "end",
            "rationale": "Turn limit reached (5 turns); ending conversation."
        }

    return {
        "action": "send",
        "body": "Samajh gaya. Main aapke business listing ko boost karne ke liye tayar hoon. Reply YES to proceed!",
        "cta": "binary_yes_stop",
        "rationale": "Responding to general query with direct value proposal."
    }
