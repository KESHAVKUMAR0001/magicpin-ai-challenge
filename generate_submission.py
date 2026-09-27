"""
Generate canonical submission.jsonl (30 test pairs) for magicpin AI Challenge Evaluation
"""
import os
import json
from pathlib import Path
from bot import compose

DATASET_DIR = Path(__file__).parent / "dataset"

def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    print("Generating submission.jsonl across 30 test scenarios...")
    
    # Load Seed Datasets
    merchants_seed = load_json(DATASET_DIR / "merchants_seed.json")
    triggers_seed = load_json(DATASET_DIR / "triggers_seed.json")
    customers_seed = load_json(DATASET_DIR / "customers_seed.json")
    
    # Index by ID
    merchants_by_id = {m["merchant_id"]: m for m in merchants_seed.get("merchants", [])}
    triggers_by_id = {t["id"]: t for t in triggers_seed.get("triggers", [])}
    customers_by_id = {c["customer_id"]: c for c in customers_seed.get("customers", [])}
    
    # Load Category Contexts
    categories = {}
    cat_dir = DATASET_DIR / "categories"
    if cat_dir.exists():
        for f in cat_dir.glob("*.json"):
            cat_data = load_json(f)
            categories[cat_data.get("slug", f.stem)] = cat_data

    # Generate 30 Test Scenarios
    submission_rows = []
    
    # If triggers list is shorter than 30, generate synthesis test items
    triggers_list = list(triggers_by_id.values())
    merchants_list = list(merchants_by_id.values())
    
    for i in range(1, 31):
        test_id = f"T{i:02d}"
        
        # Select trigger & merchant cleanly
        trg = triggers_list[(i - 1) % len(triggers_list)] if triggers_list else {
            "id": f"trg_{i}", "kind": "research_digest", "payload": {"top_item": {"title": "Clinical Trial", "source": "JIDA Oct 2026", "trial_n": 2100}}
        }
        
        mer_id = trg.get("payload", {}).get("merchant_id")
        merchant = merchants_by_id.get(mer_id) or (merchants_list[(i - 1) % len(merchants_list)] if merchants_list else {
            "merchant_id": f"m_{i}", "category_slug": "dentists",
            "identity": {"name": f"Clinic {i}", "owner_first_name": "Meera", "locality": "Lajpat Nagar", "city": "Delhi"},
            "performance": {"views": 2410, "ctr": 0.021}
        })
        
        cat_slug = merchant.get("category_slug", "dentists")
        category = categories.get(cat_slug) or {
            "slug": cat_slug,
            "offer_catalog": [{"title": "Dental Cleaning @ ₹299"}],
            "peer_stats": {"avg_ctr": 0.030}
        }
        
        cust_id = trg.get("payload", {}).get("customer_id")
        customer = customers_by_id.get(cust_id) if cust_id else None

        # Compose output
        output = compose(category, merchant, trg, customer)
        
        row = {
            "test_id": test_id,
            "body": output["body"],
            "cta": output["cta"],
            "send_as": output["send_as"],
            "suppression_key": output["suppression_key"],
            "rationale": output["rationale"]
        }
        submission_rows.append(row)

    # Write output JSONL
    out_path = Path(__file__).parent / "submission.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for row in submission_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(submission_rows)} test results into submission.jsonl!")

if __name__ == "__main__":
    main()
