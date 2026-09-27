"""Unit tests for bot composition and multi-turn handlers."""
from __future__ import annotations
import unittest
from bot import compose
from conversation_handlers import respond
from app.detector import TurnDetector
from app.store import ContextStore

class TestVeraBot(unittest.TestCase):
    def test_compose_research_digest_specificity(self):
        category = {
            "slug": "dentists",
            "offer_catalog": [{"title": "Dental Cleaning @ ₹299"}]
        }
        merchant = {
            "identity": {"name": "Dr. Meera's Clinic", "owner_first_name": "Meera", "locality": "Lajpat Nagar", "city": "Delhi"},
            "performance": {"views": 2410, "ctr": 0.021}
        }
        trigger = {
            "id": "trg_01",
            "kind": "research_digest",
            "suppression_key": "suppress_01",
            "payload": {
                "top_item": {
                    "title": "3-mo fluoride recall cuts caries 38% better",
                    "source": "JIDA Oct 2026, p.14",
                    "trial_n": 2100
                }
            }
        }
        
        result = compose(category, merchant, trigger)
        self.assertEqual(result["send_as"], "vera")
        self.assertIn("JIDA Oct 2026, p.14", result["body"])
        self.assertIn("2100", result["body"])
        self.assertIn("Meera", result["body"])
        self.assertEqual(result["cta"], "open_ended")

    def test_auto_reply_detection(self):
        msg = "Aapki jaankari ke liye bahut-bahut shukriya. Main aapki yeh sabhi baatein team tak pahuncha deti hoon."
        self.assertTrue(TurnDetector.is_auto_reply(msg))
        
        state = {"turn_count": 1, "auto_reply_count": 1}
        response = respond(state, msg)
        self.assertEqual(response["action"], "end")

    def test_intent_handoff_immediate_action(self):
        msg = "Mujhe magicpin se judna hai, please update my profile"
        state = {"turn_count": 1}
        response = respond(state, msg)
        self.assertEqual(response["action"], "send")
        self.assertIn("Done!", response["body"])

    def test_context_store_version_conflict(self):
        store = ContextStore()
        ok, ack, ver = store.push_context("category", "dentists", 1, {"slug": "dentists"})
        self.assertTrue(ok)
        
        # Lower version re-push returns stale_version conflict
        ok2, reason, ver2 = store.push_context("category", "dentists", 0, {"slug": "dentists"})
        self.assertFalse(ok2)
        self.assertEqual(reason, "stale_version")
        self.assertEqual(ver2, 1)

if __name__ == "__main__":
    unittest.main()
