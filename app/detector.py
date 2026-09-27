"""Inbound message intent and auto-reply classifier."""
from __future__ import annotations
import re
from typing import Literal

# Known patterns for WhatsApp Business automated canned replies
AUTO_REPLY_PATTERNS = [
    r"thank you for (contacting|reaching out)",
    r"aapki jaankari ke liye.*shukriya",
    r"main aapki.*baatein.*team tak pahuncha",
    r"automated assistant",
    r"auto-reply",
    r"welcome to our business",
    r"we are currently away",
    r"we will get back to you shortly",
    r"thanks for your message",
    r"this is an automated message",
    r"hamari team tak pahuncha",
]

# Positive commitment signals that indicate merchant acceptance
INTENT_ACCEPT_PATTERNS = [
    r"\b(yes|yeah|sure|ok|okay|yep|ha|haan|zaroor|chalega|bhejo|do it|go ahead)\b",
    r"magicpin.*(judna|join|connect)",
    r"please (update|check|send|show)",
    r"update (my|the) profile",
    r"details share",
    r"send me the abstract",
]

# Explicit decline or opt-out requests
INTENT_STOP_PATTERNS = [
    r"\b(stop|no|not interested|dont|don't|mat karo|chahiye|nahi|bas|exit|unsubscribe)\b"
]

class TurnDetector:
    """Classifies inbound merchant WhatsApp turns to guide multi-turn routing."""

    @staticmethod
    def is_auto_reply(message: str) -> bool:
        """Detects if incoming text matches automated WhatsApp business responses."""
        cleaned_text = message.strip().lower()
        return any(re.search(pattern, cleaned_text) for pattern in AUTO_REPLY_PATTERNS)

    @staticmethod
    def classify_intent(message: str) -> Literal["ACCEPT_ACTION", "REJECT_STOP", "NEUTRAL_QUESTION", "AUTO_REPLY"]:
        """Classifies incoming merchant intent into key operational categories."""
        if TurnDetector.is_auto_reply(message):
            return "AUTO_REPLY"
        
        cleaned_text = message.strip().lower()
        
        if any(re.search(pattern, cleaned_text) for pattern in INTENT_STOP_PATTERNS):
            return "REJECT_STOP"

        if any(re.search(pattern, cleaned_text) for pattern in INTENT_ACCEPT_PATTERNS):
            return "ACCEPT_ACTION"

        return "NEUTRAL_QUESTION"
