import httpx
import json

BASE = "https://kkpqfuj-amager.tripletex.dev/v2"
AUTH = ("0", "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9")
HEADERS = {"Content-Type": "application/json"}

client = httpx.Client(base_url=BASE, auth=AUTH, headers=HEADERS, timeout=30)

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

def create_order(customer_id, lines, order_date="2026-03-20", delivery_date="2026-03-25"):
    r = client.post("/order", json={
        "customer": {"id": customer_id},
        "orderDate": order_date,
        "deliveryDate": delivery_date,
        "orderLines": lines,
    })
    if r.status_code not in (200, 201):
        pp("Order creation FAILED", r)
        return None
    oid = r.json()["value"]["id"]
    print(f"  [order created: {oid}]")
    return oid

def create_invoice_from_order(order_id, inv_date="2026-03-20", due_date="2026-04-03", send=False):
    url = "/invoice"
    if send:
        url += "?sendToCustomer=true"
    r = client.post(url, json={
        "invoiceDate": inv_date,
        "invoiceDueDate": due_date,
        "orders": [{"id": order_id}],
    })
    return r

customer_id = 108169644  # reuse from previous run
bank_pt = 32814532       # "Betalt til bank"

# ══════════════════════════════════════════════════════════════
# FIX TEST 1: Payment uses query params, not JSON body
# ══════════════════════════════════════════════════════════════
print("#"*60)
print("# FIX TEST 1: Partial Payment (query params)")
print("#"*60)

oid1 = create_order(customer_id, [{
    "description": "Partial payment test v2",
    "count": 1,
    "unitPriceExcludingVatCurrency": 10000,
    "vatType": {"id": 3},
}])

inv1_r = create_invoice_from_order(oid1, send=True)
pp("TEST1 - Create Invoice", inv1_r)
inv1_id = inv1_r.json()["value"]["id"]
inv1_amt = inv1_r.json()["value"]["amount"]
print(f">>> Invoice ID: {inv1_id}, amount: {inv1_amt}")

# Try payment as query params
pay1 = client.put(f"/invoice/{inv1_id}/:payment", params={
    "paymentDate": "2026-03-20",
    "paymentTypeId": bank_pt,
    "paidAmount": 5000,
    "paidAmountCurrency": 5000,
})
pp("TEST1 - Partial payment via query params", pay1)

if pay1.status_code >= 400:
    # Try form-encoded
    print(">>> Query params failed, trying URL-encoded form body...")
    pay1b = client.put(
        f"/invoice/{inv1_id}/:payment",
        content="paymentDate=2026-03-20&paymentTypeId=32814532&paidAmount=5000&paidAmountCurrency=5000",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    pp("TEST1 - Partial payment via form body", pay1b)

# Check result
inv1_check = client.get(f"/invoice/{inv1_id}")
inv1_after = inv1_check.json()["value"]
print(f">>> amountOutstanding: {inv1_after.get('amountOutstanding')}")
print(f">>> Expected: 7500")


# ══════════════════════════════════════════════════════════════
# FIX TEST 3 & 4: Use output VAT codes (31 for 15%, 32 for 12%)
# The issue was id=11 was picked first (input VAT). We need id=31, 32.
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# FIX TEST 3: 15% VAT with vatType id=31 (Utgående avgift, middels sats)")
print("#"*60)

oid3 = create_order(customer_id, [{
    "description": "Food product 15% MVA",
    "count": 1,
    "unitPriceExcludingVatCurrency": 10000,
    "vatType": {"id": 31},
}])
if oid3:
    inv3_r = create_invoice_from_order(oid3)
    pp("TEST3 - Invoice with 15% VAT (id=31)", inv3_r)
    if inv3_r.status_code in (200, 201):
        d = inv3_r.json()["value"]
        print(f">>> amount (incl VAT): {d.get('amount')}")
        print(f">>> amountExcludingVat: {d.get('amountExcludingVat')}")
        print(f">>> Expected: 11500 (10000 + 15%)")
        print(f">>> CORRECT: {d.get('amount') == 11500.0}")


print("\n\n" + "#"*60)
print("# FIX TEST 4: 12% VAT with vatType id=32 (Utgående avgift, lav sats)")
print("#"*60)

oid4 = create_order(customer_id, [{
    "description": "Transport service 12% MVA",
    "count": 1,
    "unitPriceExcludingVatCurrency": 10000,
    "vatType": {"id": 32},
}])
if oid4:
    inv4_r = create_invoice_from_order(oid4)
    pp("TEST4 - Invoice with 12% VAT (id=32)", inv4_r)
    if inv4_r.status_code in (200, 201):
        d = inv4_r.json()["value"]
        print(f">>> amount (incl VAT): {d.get('amount')}")
        print(f">>> amountExcludingVat: {d.get('amountExcludingVat')}")
        print(f">>> Expected: 11200 (10000 + 12%)")
        print(f">>> CORRECT: {d.get('amount') == 11200.0}")


# ══════════════════════════════════════════════════════════════
# FIX TEST 7: Credit note needs date param, pay first
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# FIX TEST 7: Credit note on PAID invoice")
print("#"*60)

oid7 = create_order(customer_id, [{
    "description": "Credit note test v2",
    "count": 1,
    "unitPriceExcludingVatCurrency": 6000,
    "vatType": {"id": 3},
}])

if oid7:
    inv7_r = create_invoice_from_order(oid7, send=True)
    pp("TEST7 - Create Invoice", inv7_r)
    inv7_id = inv7_r.json()["value"]["id"]
    inv7_amt = inv7_r.json()["value"]["amount"]
    print(f">>> Invoice ID: {inv7_id}, amount: {inv7_amt}")

    # Pay fully using query params
    pay7 = client.put(f"/invoice/{inv7_id}/:payment", params={
        "paymentDate": "2026-03-20",
        "paymentTypeId": bank_pt,
        "paidAmount": inv7_amt,
        "paidAmountCurrency": inv7_amt,
    })
    pp("TEST7 - Full payment", pay7)

    # Verify paid
    inv7_check = client.get(f"/invoice/{inv7_id}")
    inv7_after = inv7_check.json()["value"]
    print(f">>> amountOutstanding after payment: {inv7_after.get('amountOutstanding')}")

    # Credit note with date as query param
    cn7 = client.put(f"/invoice/{inv7_id}/:createCreditNote", params={
        "date": "2026-03-20",
        "comment": "Full credit on paid invoice",
        "creditNoteEmail": "adv-test@example.com",
    })
    pp("TEST7 - Credit Note on PAID invoice (query params)", cn7)

    if cn7.status_code in (200, 201):
        cn7_val = cn7.json().get("value", cn7.json())
        print(f">>> Credit note result: {cn7_val}")

        # Check original invoice state
        inv7_final = client.get(f"/invoice/{inv7_id}")
        if inv7_final.status_code == 200:
            f = inv7_final.json()["value"]
            print(f">>> Original invoice isCredited: {f.get('isCredited')}")
            print(f">>> Original invoice amountOutstanding: {f.get('amountOutstanding')}")
            print(f">>> Original invoice amountOutstandingTotal: {f.get('amountOutstandingTotal')}")

        # If we got a credit note ID (document), try to find the credit note invoice
        if isinstance(cn7_val, int):
            # It returned a document ID, search for credit note invoice
            print(f">>> Returned value (likely document ID): {cn7_val}")
            # Search recent invoices for this customer
            search = client.get(f"/invoice?customerId={customer_id}&invoiceDateFrom=2026-03-20&invoiceDateTo=2026-03-20&from=0&count=20")
            if search.status_code == 200:
                for inv in search.json().get("values", []):
                    if inv.get("isCreditNote"):
                        print(f">>> FOUND Credit Note Invoice: id={inv['id']}, "
                              f"invoiceNumber={inv.get('invoiceNumber')}, "
                              f"amount={inv.get('amount')}, "
                              f"creditedInvoice={inv.get('creditedInvoice')}")
    else:
        # Maybe it needs to be sent differently
        print(">>> Trying credit note with JSON body including date...")
        cn7b = client.put(f"/invoice/{inv7_id}/:createCreditNote", json={
            "date": "2026-03-20",
            "comment": "Full credit on paid invoice",
            "creditNoteEmail": "adv-test@example.com",
        })
        pp("TEST7 - Credit Note (JSON body with date)", cn7b)


print("\n\n" + "="*60)
print("FIX TESTS COMPLETE")
print("="*60)

client.close()
