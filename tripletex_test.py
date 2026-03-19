import httpx
import json
import sys

BASE = "https://kkpqfuj-amager.tripletex.dev/v2"
AUTH = ("0", "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9")

client = httpx.Client(base_url=BASE, auth=AUTH, timeout=30)

def pp(label, r):
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"Status: {r.status_code}")
    try:
        d = r.json()
        print(json.dumps(d, indent=2, ensure_ascii=False)[:3000])
    except Exception:
        print(r.text[:2000])
    print(f"{'='*60}")
    return r

# -----------------------------------------------------------------
# SETUP
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# SETUP")
print("#"*60)

# 1) VAT settings
r = pp("GET /ledger/vatSettings", client.get("/ledger/vatSettings"))

# 2) Bank account on ledger account 1920
r = pp("GET /ledger/account 1920", client.get("/ledger/account", params={"number": 1920, "fields": "id,version,bankAccountNumber"}))
acct_data = r.json()
acct_list = acct_data.get("values", [])
if acct_list:
    acct = acct_list[0]
    acct_id = acct["id"]
    acct_version = acct["version"]
    bank_num = acct.get("bankAccountNumber")
    print(f"  Account 1920 id={acct_id}, version={acct_version}, bankAccountNumber={bank_num}")
    if not bank_num:
        r2 = pp("PUT bank account number on 1920",
                 client.put(f"/ledger/account/{acct_id}", json={
                     "id": acct_id,
                     "version": acct_version,
                     "bankAccountNumber": "28002111480"
                 }))
else:
    print("  WARNING: account 1920 not found")

# 3) Create customer
r = pp("POST /customer", client.post("/customer", json={
    "name": "Invoice Test AS",
    "isCustomer": True
}))
cust_id = r.json()["value"]["id"]
print(f"  Customer ID: {cust_id}")

# -----------------------------------------------------------------
# TEST 1: Invoice "eksklusiv MVA" (excluding VAT, VAT applies)
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 1: Invoice eksklusiv MVA")
print("#"*60)

invoice1_payload = {
    "invoiceDate": "2026-03-20",
    "invoiceDueDate": "2026-04-20",
    "orders": [{
        "orderDate": "2026-03-20",
        "deliveryDate": "2026-03-20",
        "customer": {"id": cust_id},
        "isPrioritizeAmountsIncludingVat": False,
        "orderLines": [{
            "description": "Consulting services excl VAT",
            "count": 1,
            "unitPriceExcludingVatCurrency": 28900,
            "vatType": {"id": 3}
        }]
    }]
}
r = pp("POST /invoice?sendToCustomer=true (excl VAT)",
       client.post("/invoice", params={"sendToCustomer": "true"}, json=invoice1_payload))
inv1 = r.json().get("value", {})
inv1_id = inv1.get("id")
inv1_excl = inv1.get("amountExcludingVat")
inv1_incl = inv1.get("amount")
print(f"  Invoice 1 ID: {inv1_id}")
print(f"  amountExcludingVat: {inv1_excl}  (expected 28900)")
print(f"  amount (incl VAT):  {inv1_incl}  (expected 36125)")
print(f"  TEST 1 PASS: {inv1_excl == 28900.0 and inv1_incl == 36125.0}")

# -----------------------------------------------------------------
# TEST 2: Invoice "inklusiv MVA" (including VAT)
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 2: Invoice inklusiv MVA")
print("#"*60)

invoice2_payload = {
    "invoiceDate": "2026-03-20",
    "invoiceDueDate": "2026-04-20",
    "orders": [{
        "orderDate": "2026-03-20",
        "deliveryDate": "2026-03-20",
        "customer": {"id": cust_id},
        "isPrioritizeAmountsIncludingVat": True,
        "orderLines": [{
            "description": "Consulting services incl VAT",
            "count": 1,
            "unitPriceIncludingVatCurrency": 36125,
            "vatType": {"id": 3}
        }]
    }]
}
r = pp("POST /invoice (incl VAT)",
       client.post("/invoice", params={"sendToCustomer": "false"}, json=invoice2_payload))
inv2 = r.json().get("value", {})
inv2_id = inv2.get("id")
inv2_excl = inv2.get("amountExcludingVat")
inv2_incl = inv2.get("amount")
print(f"  Invoice 2 ID: {inv2_id}")
print(f"  amountExcludingVat: {inv2_excl}  (expected 28900)")
print(f"  amount (incl VAT):  {inv2_incl}  (expected 36125)")
print(f"  TEST 2 PASS: {inv2_excl == 28900.0 and inv2_incl == 36125.0}")

# -----------------------------------------------------------------
# TEST 3: Invoice WITHOUT VAT (mva-fritt)
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 3: Invoice uten MVA (no VAT)")
print("#"*60)

invoice3_payload = {
    "invoiceDate": "2026-03-20",
    "invoiceDueDate": "2026-04-20",
    "orders": [{
        "orderDate": "2026-03-20",
        "deliveryDate": "2026-03-20",
        "customer": {"id": cust_id},
        "isPrioritizeAmountsIncludingVat": False,
        "orderLines": [{
            "description": "VAT-free goods",
            "count": 1,
            "unitPriceExcludingVatCurrency": 28900
        }]
    }]
}
r = pp("POST /invoice (no VAT)",
       client.post("/invoice", params={"sendToCustomer": "false"}, json=invoice3_payload))
inv3 = r.json().get("value", {})
inv3_id = inv3.get("id")
inv3_excl = inv3.get("amountExcludingVat")
inv3_incl = inv3.get("amount")
print(f"  Invoice 3 ID: {inv3_id}")
print(f"  amountExcludingVat: {inv3_excl}")
print(f"  amount (incl VAT):  {inv3_incl}")
print(f"  TEST 3 PASS: {inv3_excl == inv3_incl}  (amounts should be equal = no VAT)")

# -----------------------------------------------------------------
# TEST 4: Register full payment on invoice 1
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 4: Register payment on invoice 1")
print("#"*60)

r = pp("GET /invoice/paymentType", client.get("/invoice/paymentType", params={"fields": "id,description"}))
pay_types = r.json().get("values", [])
bank_pay_id = None
for pt in pay_types:
    desc = pt.get("description", "")
    print(f"  PaymentType: id={pt['id']} desc='{desc}'")
    if "bank" in desc.lower() or "betalt til bank" in desc.lower():
        bank_pay_id = pt["id"]

if bank_pay_id is None and pay_types:
    bank_pay_id = pay_types[0]["id"]
    print(f"  Fallback: using first payment type id={bank_pay_id}")

print(f"  Using payment type ID: {bank_pay_id}")

r = pp(f"PUT /invoice/{inv1_id}/:payment",
       client.put(f"/invoice/{inv1_id}/:payment", params={
           "paymentDate": "2026-03-20",
           "paymentTypeId": bank_pay_id,
           "paidAmount": 36125
       }))
pay_resp = r.json().get("value", {})
outstanding = pay_resp.get("amountOutstanding")
print(f"  amountOutstanding: {outstanding}  (expected 0)")
print(f"  TEST 4 PASS: {outstanding == 0.0}")

# -----------------------------------------------------------------
# TEST 5: Create credit note from invoice 3
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 5: Create credit note from invoice 3")
print("#"*60)

r = pp(f"PUT /invoice/{inv3_id}/:createCreditNote",
       client.put(f"/invoice/{inv3_id}/:createCreditNote", params={"date": "2026-03-20"}))
credit = r.json().get("value", {})
credit_id = credit.get("id")
is_credit = credit.get("isCreditNote")
print(f"  Credit note ID: {credit_id}")
print(f"  isCreditNote: {is_credit}")
print(f"  TEST 5 PASS: {is_credit == True}")

# -----------------------------------------------------------------
# TEST 6: Invoice with sendToCustomer=false, then send separately
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 6: Create invoice then send separately")
print("#"*60)

invoice6_payload = {
    "invoiceDate": "2026-03-20",
    "invoiceDueDate": "2026-04-20",
    "orders": [{
        "orderDate": "2026-03-20",
        "deliveryDate": "2026-03-20",
        "customer": {"id": cust_id},
        "isPrioritizeAmountsIncludingVat": False,
        "orderLines": [{
            "description": "Separate send test",
            "count": 1,
            "unitPriceExcludingVatCurrency": 5000,
            "vatType": {"id": 3}
        }]
    }]
}
r6_create = pp("POST /invoice?sendToCustomer=false",
       client.post("/invoice", params={"sendToCustomer": "false"}, json=invoice6_payload))
inv6 = r6_create.json().get("value", {})
inv6_id = inv6.get("id")
print(f"  Invoice 6 ID: {inv6_id}")

r6_send = pp(f"PUT /invoice/{inv6_id}/:send",
        client.put(f"/invoice/{inv6_id}/:send", params={"sendType": "EMAIL"}))
print(f"  Create status: {r6_create.status_code}")
print(f"  Send status:   {r6_send.status_code}")
print(f"  TEST 6 PASS: {r6_create.status_code in (200,201) and r6_send.status_code in (200,201)}")

# -----------------------------------------------------------------
# TEST 7: Verify payment type endpoints (INCOMING vs OUTGOING)
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# TEST 7: Payment type endpoints comparison")
print("#"*60)

r_in = pp("GET /invoice/paymentType (incoming)", client.get("/invoice/paymentType"))
r_out = pp("GET /ledger/paymentTypeOut (outgoing)", client.get("/ledger/paymentTypeOut"))

incoming_ids = {v["id"] for v in r_in.json().get("values", [])}
outgoing_ids = {v["id"] for v in r_out.json().get("values", [])}

print(f"  Incoming IDs: {sorted(incoming_ids)}")
print(f"  Outgoing IDs: {sorted(outgoing_ids)}")
print(f"  Sets are different: {incoming_ids != outgoing_ids}")
print(f"  Overlap:    {sorted(incoming_ids & outgoing_ids)}")
print(f"  In-only:    {sorted(incoming_ids - outgoing_ids)}")
print(f"  Out-only:   {sorted(outgoing_ids - incoming_ids)}")
print(f"  TEST 7 PASS: {incoming_ids != outgoing_ids}")

# -----------------------------------------------------------------
# SUMMARY
# -----------------------------------------------------------------
print("\n" + "#"*60)
print("# SUMMARY")
print("#"*60)
t1 = inv1_excl == 28900.0 and inv1_incl == 36125.0
t2 = inv2_excl == 28900.0 and inv2_incl == 36125.0
t3 = inv3_excl == inv3_incl
t4 = outstanding == 0.0
t5 = is_credit == True
t6 = r6_create.status_code in (200, 201) and r6_send.status_code in (200, 201)
t7 = incoming_ids != outgoing_ids

results = [
    ("TEST 1 - Excl VAT invoice",   t1),
    ("TEST 2 - Incl VAT invoice",   t2),
    ("TEST 3 - No VAT invoice",     t3),
    ("TEST 4 - Full payment",       t4),
    ("TEST 5 - Credit note",        t5),
    ("TEST 6 - Separate send",      t6),
    ("TEST 7 - Payment types diff", t7),
]
for name, passed in results:
    status = "PASS" if passed else "FAIL"
    print(f"  {status}: {name}")

all_pass = all(p for _, p in results)
print(f"\n  ALL TESTS PASSED: {all_pass}")

client.close()
