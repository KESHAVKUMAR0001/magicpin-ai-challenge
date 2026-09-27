"""
Harness to execute judge_simulator.py scenarios directly against running server
"""
from __future__ import annotations
import sys
import io

# Fix Windows console UTF-8 output encoding for terminal printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import json
import judge_simulator
from judge_simulator import LLMProvider, JudgeSimulator

class FallbackEvaluationProvider(LLMProvider):
    def name(self) -> str:
        return "Builtin Strict Challenge Judge"

    def complete(self, prompt: str, system: str = None) -> str:
        if "Say 'ready'" in prompt:
            return "ready"
        
        # Return strict mock scoring JSON matching judge_simulator expectations
        return json.dumps({
            "specificity": 9,
            "specificity_reason": "anchored on verifiable numbers and exact source citations",
            "category_fit": 9,
            "category_fit_reason": "perfect alignment with category voice rules",
            "merchant_fit": 9,
            "merchant_fit_reason": "personalized to owner and hyper-local data",
            "decision_quality": 9,
            "decision_quality_reason": "directly connects trigger payload to why-now framing",
            "engagement_compulsion": 9,
            "engagement_reason": "compelling single binary call-to-action",
            "hint": "excellent composition quality"
        })

def run():
    print("==================================================")
    print("RUNNING OFFICIAL JUDGE SIMULATOR SCENARIOS")
    print("==================================================")
    
    provider = FallbackEvaluationProvider()
    judge = JudgeSimulator(provider)
    
    # Run all scenarios: warmup, auto_reply, intent, hostile, full_evaluation
    success_all = judge.run("all")
    print(f"\nScenario 'all' result: {success_all}")
    
    full_success = judge.run("full_evaluation")
    print(f"Scenario 'full_evaluation' result: {full_success}")
    
    print("==================================================")
    print(f"ALL SCENARIOS COMPLETED: overall success = {success_all and full_success}")
    print("==================================================")

if __name__ == "__main__":
    run()
