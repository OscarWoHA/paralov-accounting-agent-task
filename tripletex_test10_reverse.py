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

# The voucher we created: id=608818332
voucher_id = 608818332

# First verify it exists
r = pp("Verify voucher exists", client.get(f"/ledger/voucher/{voucher_id}", params={"fields": "id,number,date,description,reverseVoucher"}))

# Try to reverse it
r_rev = pp("TEST 10: Reverse voucher",
    client.put(f"/ledger/voucher/{voucher_id}/:reverse", params={"date": "2026-03-15"}))

if r_rev.status_code in (200, 201):
    rev_data = r_rev.json()
    print("\n  >> TEST 10 PASSED - Voucher successfully reversed!")
    if "value" in rev_data:
        rev_val = rev_data["value"]
        print(f"  >> Reversal voucher id: {rev_val.get('id')}")
        print(f"  >> Reversal voucher number: {rev_val.get('number')}")
        print(f"  >> Reversal date: {rev_val.get('date')}")
        print(f"  >> Reversal description: {rev_val.get('description')}")
else:
    print(f"\n  >> Reversal failed with status {r_rev.status_code}")
    # Try listing vouchers with date range to find our voucher
    r_list = pp("List vouchers in date range",
        client.get("/ledger/voucher", params={
            "fields": "id,number,date,description",
            "dateFrom": "2026-03-01",
            "dateTo": "2026-03-31",
            "count": 20
        }))
    if r_list.status_code == 200:
        vouchers = r_list.json().get("values", [])
        print(f"\n  >> Found {len(vouchers)} vouchers in March 2026:")
        for v in vouchers:
            print(f"     id={v['id']}, num={v.get('number','')}, date={v.get('date','')}, desc={v.get('description','')}")

        if vouchers:
            # Try reversing the first one
            vid = vouchers[0]["id"]
            r_rev2 = pp(f"Reverse voucher {vid}",
                client.put(f"/ledger/voucher/{vid}/:reverse", params={"date": "2026-03-15"}))

client.close()
