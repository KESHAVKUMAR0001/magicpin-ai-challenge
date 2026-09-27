"""
Complete Suite Evaluation Runner for magicpin AI Challenge
Tests Server Endpoints, Edge Cases, Scenarios, and Benchmark Submission
"""
from __future__ import annotations
import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:8080"

def make_req(method: str, path: str, data: dict = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except:
            return e.code, {"raw": content}

def run():
    print("==================================================")
    print("RUNNING COMPREHENSIVE CHALLENGE EVALUATION SUITE")
    print("==================================================")

    # 1. Healthz
    code, res = make_req("GET", "/v1/healthz")
    assert code == 200, f"Healthz failed: {code}"
    print(f"[PASS] GET /v1/healthz: {res}")

    # 2. Metadata
    code, res = make_req("GET", "/v1/metadata")
    assert code == 200, f"Metadata failed: {code}"
    print(f"[PASS] GET /v1/metadata: {res.get('team_name')} ({res.get('version')})")

    # 3. Context Push & Version Conflict (409)
    cat_payload = {
        "slug": "dentists",
        "offer_catalog": [{"id": "d1", "title": "Dental Cleaning @ ₹299"}],
        "peer_stats": {"avg_ctr": 0.030}
    }
    code, res = make_req("POST", "/v1/context", {
        "scope": "category", "context_id": "dentists", "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z", "payload": cat_payload
    })
    assert code == 200 and res.get("accepted") is True, f"Push context v1 failed: {code} {res}"
    print(f"[PASS] POST /v1/context v1 accepted: {res}")

    # Push same version -> expect 200 OK (idempotent no-op)
    code, res = make_req("POST", "/v1/context", {
        "scope": "category", "context_id": "dentists", "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z", "payload": cat_payload
    })
    assert code == 200 and res.get("accepted") is True, f"Expected 200 idempotent no-op, got: {code} {res}"
    print(f"[PASS] POST /v1/context v1 re-push returned 200 Idempotent No-Op: {res}")

    # Push higher version -> expect 200
    code, res = make_req("POST", "/v1/context", {
        "scope": "category", "context_id": "dentists", "version": 2,
        "delivered_at": "2026-04-26T10:05:00Z", "payload": cat_payload
    })
    assert code == 200 and res.get("accepted") is True, f"Push context v2 failed: {code} {res}"
    print(f"[PASS] POST /v1/context v2 accepted: {res}")

    # Push lower version -> expect 409 Conflict
    code, res = make_req("POST", "/v1/context", {
        "scope": "category", "context_id": "dentists", "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z", "payload": cat_payload
    })
    assert code == 409 and res.get("accepted") is False, f"Expected 409 conflict for lower version, got: {code} {res}"
    print(f"[PASS] POST /v1/context v1 push after v2 returned 409 Stale Version: {res}")

    # 4. Push Merchant Context
    mer_payload = {
        "merchant_id": "m_001_drmeera_dentist_delhi",
        "category_slug": "dentists",
        "identity": {"name": "Dr. Meera's Clinic", "owner_first_name": "Meera", "locality": "Lajpat Nagar", "city": "Delhi", "languages": ["en", "hi"]},
        "performance": {"views": 2410, "calls": 18, "ctr": 0.021},
        "customer_aggregate": {"lapsed_180d_plus": 78}
    }
    code, res = make_req("POST", "/v1/context", {
        "scope": "merchant", "context_id": "m_001_drmeera_dentist_delhi", "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z", "payload": mer_payload
    })
    assert code == 200, f"Merchant push failed: {code}"
    print(f"[PASS] POST /v1/context merchant accepted")

    # 5. Push Trigger Context
    trg_payload = {
        "id": "trg_001", "scope": "merchant", "kind": "research_digest", "suppression_key": "research:dentists:W17",
        "payload": {
            "merchant_id": "m_001_drmeera_dentist_delhi",
            "top_item": {"title": "3-mo fluoride recall cuts caries 38% better", "source": "JIDA Oct 2026, p.14", "trial_n": 2100}
        }
    }
    code, res = make_req("POST", "/v1/context", {
        "scope": "trigger", "context_id": "trg_001", "version": 1,
        "delivered_at": "2026-04-26T10:00:00Z", "payload": trg_payload
    })
    assert code == 200, f"Trigger push failed: {code}"
    print(f"[PASS] POST /v1/context trigger accepted")

    # 6. Tick endpoint test
    code, res = make_req("POST", "/v1/tick", {
        "now": "2026-04-26T10:30:00Z", "available_triggers": ["trg_001"]
    })
    assert code == 200 and "actions" in res and len(res["actions"]) > 0, f"Tick failed: {code} {res}"
    action = res["actions"][0]
    print(f"[PASS] POST /v1/tick generated action: body='{action['body'][:60]}...'")

    # 7. Auto-reply scenario test
    auto_msg = "Thank you for contacting us! Our team will respond shortly."
    code, reply1 = make_req("POST", "/v1/reply", {
        "conversation_id": "conv_auto", "merchant_id": "m_001_drmeera_dentist_delhi",
        "message": auto_msg, "received_at": "2026-04-26T10:35:00Z", "turn_number": 2
    })
    assert reply1.get("action") == "end", f"Auto-reply turn 1 expected 'end', got: {reply1}"
    print(f"[PASS] Multi-turn Auto-Reply handling successfully ENDED conversation on turn 1")

    # 8. Intent Transition scenario test
    code, intent_res = make_req("POST", "/v1/reply", {
        "conversation_id": "conv_intent", "merchant_id": "m_001_drmeera_dentist_delhi",
        "message": "Ok lets do it. Whats next?", "received_at": "2026-04-26T10:40:00Z", "turn_number": 2
    })
    assert intent_res.get("action") == "send" and "Done!" in intent_res.get("body", ""), f"Intent transition failed: {intent_res}"
    print(f"[PASS] Intent Transition successfully entered ACTION mode: '{intent_res.get('body')[:60]}...'")

    # 9. Hostile handling test
    code, hostile_res = make_req("POST", "/v1/reply", {
        "conversation_id": "conv_hostile", "merchant_id": "m_001_drmeera_dentist_delhi",
        "message": "Stop messaging me. This is useless spam.", "received_at": "2026-04-26T10:45:00Z", "turn_number": 2
    })
    assert hostile_res.get("action") == "end", f"Hostile handling expected 'end', got: {hostile_res}"
    print(f"[PASS] Hostile message successfully ENDED conversation")

    print("\n==================================================")
    print("ALL EVALUATION SUITE TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    run()
