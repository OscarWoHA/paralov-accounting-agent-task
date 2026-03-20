"""Run external test prompts through the /solve endpoint and track results."""

import httpx
import json
import sys
import time

SOLVE_URL = "http://localhost:1234/solve"
BASE = "https://kkpqfuj-amager.tripletex.dev/v2"
TOKEN = "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9"
AUTH = ("0", TOKEN)

def run_test(test):
    prompt = test["prompt"]
    test_id = test["id"]
    category = test["category"]
    lang = test["language"]
    tier = test["tier"]

    print(f"[{test_id:3d}] T{tier} {category:20s} {lang:20s} | {prompt[:70]}...")

    payload = {
        "prompt": prompt,
        "files": [],
        "tripletex_credentials": {"base_url": BASE, "session_token": TOKEN}
    }

    start = time.time()
    try:
        r = httpx.post(SOLVE_URL, json=payload, timeout=300)
        elapsed = time.time() - start
        status = "OK" if r.status_code == 200 else f"ERR:{r.status_code}"
    except Exception as e:
        elapsed = time.time() - start
        status = f"TIMEOUT/ERR"

    print(f"       -> {status} in {elapsed:.1f}s")
    return {"id": test_id, "status": status, "time": round(elapsed, 1), "category": category, "tier": tier}


if __name__ == "__main__":
    with open("external.json") as f:
        tests = json.load(f)

    # Parse args: specific IDs or "all" or "tricky"
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            selected = tests
        elif sys.argv[1] == "tricky":
            tricky_ids = [9,15,22,23,24,25,27,28,44,45,46,47,48,57,58,59,60,66,67,68,69,70,71,72,79,89,90,95,98]
            selected = [t for t in tests if t["id"] in tricky_ids]
        else:
            ids = [int(x) for x in sys.argv[1:]]
            selected = [t for t in tests if t["id"] in ids]
    else:
        # Default: run first 10
        selected = tests[:10]

    print(f"Running {len(selected)} tests...\n")

    results = []
    for test in selected:
        result = run_test(test)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(results)} tests run")
    total_time = sum(r["time"] for r in results)
    print(f"Total time: {total_time:.0f}s, Avg: {total_time/len(results):.1f}s")

    # Save results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to test_results.json")
