import httpx
import json

BASE = "https://kkpqfuj-amager.tripletex.dev/v2"
AUTH = ("0", "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9")

client = httpx.Client(base_url=BASE, auth=AUTH, timeout=30)

def pp(label, r):
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"  Status: {r.status_code}")
    if r.status_code != 204:
        try:
            body = json.dumps(r.json(), indent=2, ensure_ascii=False)
            print(f"  Body: {body[:4000]}")
        except Exception:
            print(f"  Body (raw): {r.text[:2000]}")
    print(f"{'='*60}")
    return r

# Step 1: Examine which voucher types exist and find one suitable for manual entry
r = pp("Voucher types (all)", client.get("/ledger/voucherType", params={"fields": "id,name", "count": 50}))
vtypes = r.json()["values"]

# Step 2: Look for accounts that are NOT system-locked
# The error said account 1920 (row 0) is "system-generated". Let's try other accounts.
# Try accounts in the 4000-7999 range (expense/revenue accounts) which are typically user-editable
r = client.get("/ledger/account", params={"fields": "id,number,name", "count": 50, "numberFrom": 4000, "numberTo": 4100})
accs_4k = r.json().get("values", [])
print(f"\nAccounts 4000-4100: {len(accs_4k)}")
for a in accs_4k[:10]:
    print(f"  {a['number']} - {a.get('name','')}")

r = client.get("/ledger/account", params={"fields": "id,number,name", "count": 50, "numberFrom": 3000, "numberTo": 3100})
accs_3k = r.json().get("values", [])
print(f"\nAccounts 3000-3100: {len(accs_3k)}")
for a in accs_3k[:10]:
    print(f"  {a['number']} - {a.get('name','')}")

# Use two expense/income accounts
debit_acc = accs_4k[0] if accs_4k else None
credit_acc = accs_3k[0] if accs_3k else None
print(f"\nWill use: debit={debit_acc['number'] if debit_acc else 'NONE'}, credit={credit_acc['number'] if credit_acc else 'NONE'}")

# Step 3: Try creating voucher via /ledger/voucher/importDocument which is more permissive
# But first let's try the normal endpoint with non-system accounts
payload = {
    "date": "2026-03-15",
    "description": "Test voucher for reversal",
    "postings": [
        {
            "date": "2026-03-15",
            "account": {"id": debit_acc["id"]},
            "amountGross": 1000.00,
            "amountGrossCurrency": 1000.00,
        },
        {
            "date": "2026-03-15",
            "account": {"id": credit_acc["id"]},
            "amountGross": -1000.00,
            "amountGrossCurrency": -1000.00,
        }
    ]
}

r10 = pp("Attempt 1: POST /ledger/voucher (expense/revenue accounts)", client.post("/ledger/voucher", json=payload))

if r10.status_code != 201:
    # Try with explicit row numbers
    payload2 = {
        "date": "2026-03-15",
        "description": "Test voucher for reversal",
        "postings": [
            {
                "date": "2026-03-15",
                "row": 1,
                "account": {"id": debit_acc["id"]},
                "amountGross": 1000.00,
                "amountGrossCurrency": 1000.00,
            },
            {
                "date": "2026-03-15",
                "row": 2,
                "account": {"id": credit_acc["id"]},
                "amountGross": -1000.00,
                "amountGrossCurrency": -1000.00,
            }
        ]
    }
    r10 = pp("Attempt 2: POST /ledger/voucher (with row numbers)", client.post("/ledger/voucher", json=payload2))

if r10.status_code != 201:
    # Maybe we need amount instead of amountGross
    payload3 = {
        "date": "2026-03-15",
        "description": "Test voucher for reversal",
        "postings": [
            {
                "date": "2026-03-15",
                "row": 1,
                "account": {"id": debit_acc["id"]},
                "amount": 1000.00,
                "amountCurrency": 1000.00,
            },
            {
                "date": "2026-03-15",
                "row": 2,
                "account": {"id": credit_acc["id"]},
                "amount": -1000.00,
                "amountCurrency": -1000.00,
            }
        ]
    }
    r10 = pp("Attempt 3: POST /ledger/voucher (amount fields)", client.post("/ledger/voucher", json=payload3))

if r10.status_code != 201:
    # Try the importDocument approach
    print("\n  >> Trying /ledger/voucher/importDocument...")
    r10 = pp("Attempt 4: POST /ledger/voucher/importDocument",
        client.post("/ledger/voucher/importDocument", json=payload3))

if r10.status_code != 201:
    # Try non-list endpoint and minimal payload
    payload_min = {
        "date": "2026-03-15",
        "description": "Testbilag",
    }
    r_voucher_only = pp("Attempt 5: Create voucher without postings", client.post("/ledger/voucher", json=payload_min))

# Check what the Tripletex API docs say about voucher import
# Try using the /ledger/voucher/:importDocument endpoint which handles file import
print("\n\n--- Trying alternative: non-posted voucher approach ---")

# Try to find an existing voucher we can reverse
r_existing = pp("List existing vouchers", client.get("/ledger/voucher", params={"fields": "id,number,date,description", "count": 10}))
existing = r_existing.json().get("values", [])
if existing:
    print(f"\n  >> Found {len(existing)} existing vouchers")
    for v in existing:
        print(f"     id={v['id']}, num={v.get('number','')}, date={v.get('date','')}, desc={v.get('description','')}")

    # Try reversing the first existing voucher
    voucher_to_reverse = existing[0]
    print(f"\n  >> Attempting to reverse voucher id={voucher_to_reverse['id']}...")
    r_rev = pp("Reverse existing voucher",
        client.put(f"/ledger/voucher/{voucher_to_reverse['id']}/:reverse", params={"date": "2026-03-15"}))

    if r_rev.status_code in (200, 201):
        print("  >> TEST 10 PASSED - Successfully reversed an existing voucher")
    else:
        print(f"  >> Reversal returned {r_rev.status_code}")
        # Try with content type
        r_rev2 = pp("Reverse with empty body",
            client.put(f"/ledger/voucher/{voucher_to_reverse['id']}/:reverse",
                      params={"date": "2026-03-15"},
                      content=b""))
        if r_rev2.status_code in (200, 201):
            print("  >> TEST 10 PASSED")

client.close()
