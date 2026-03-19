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
    """Helper: create an order and return its ID."""
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

def create_invoice_from_order(order_id, inv_date="2026-03-20", due_date="2026-04-03",
                               send=False):
    """Helper: invoice an order."""
    url = "/invoice"
    if send:
        url += "?sendToCustomer=true"
    r = client.post(url, json={
        "invoiceDate": inv_date,
        "invoiceDueDate": due_date,
        "orders": [{"id": order_id}],
    })
    return r

# ── SETUP: Create a shared customer ──────────────────────────
print("\n" + "#"*60)
print("# SETUP: Creating shared customer")
print("#"*60)

cust_resp = client.post("/customer", json={
    "name": "AdvTest Kunde AS",
    "email": "adv-test@example.com",
    "invoiceEmail": "adv-test@example.com",
    "isCustomer": True,
})
pp("Create Customer", cust_resp)
customer_id = cust_resp.json()["value"]["id"]
print(f"\n>>> Customer ID: {customer_id}")


# ══════════════════════════════════════════════════════════════
# TEST 1: Partial Payment
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 1: Partial Payment")
print("#"*60)

oid1 = create_order(customer_id, [{
    "description": "Partial payment test item",
    "count": 1,
    "unitPriceExcludingVatCurrency": 10000,
    "vatType": {"id": 3},
}])

inv1_r = create_invoice_from_order(oid1, send=True)
pp("TEST1 - Create Invoice (10000 excl VAT)", inv1_r)
inv1_id = inv1_r.json()["value"]["id"]
inv1_data = inv1_r.json()["value"]
print(f">>> Invoice ID: {inv1_id}")
print(f">>> Amount (incl VAT): {inv1_data.get('amount')}")
print(f">>> Amount Outstanding: {inv1_data.get('amountOutstanding')}")

# Get payment types
pt_resp = client.get("/invoice/paymentType")
pp("TEST1 - GET payment types", pt_resp)
payment_types = pt_resp.json().get("values", [])
bank_pt = None
for pt in payment_types:
    desc = pt.get("description", "")
    print(f"  PaymentType: id={pt['id']}, description={desc}")
    if "bank" in desc.lower():
        bank_pt = pt["id"]
if bank_pt is None and payment_types:
    bank_pt = payment_types[0]["id"]
print(f">>> Using paymentType ID: {bank_pt}")

# Make partial payment of 5000
pay1 = client.put(f"/invoice/{inv1_id}/:payment", json={
    "paymentDate": "2026-03-20",
    "paymentTypeId": bank_pt,
    "paidAmount": 5000,
    "paidAmountCurrency": 5000,
})
pp("TEST1 - Partial payment (5000 of 12500)", pay1)

# Re-fetch invoice to check outstanding
inv1_check = client.get(f"/invoice/{inv1_id}")
pp("TEST1 - Invoice after partial payment", inv1_check)
inv1_after = inv1_check.json()["value"]
print(f">>> Amount Outstanding after 5000 payment: {inv1_after.get('amountOutstanding')}")
print(f">>> Expected: 7500 (12500 - 5000)")


# ══════════════════════════════════════════════════════════════
# TEST 2: Invoice with specific due date (30 days out)
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 2: Invoice with specific due date")
print("#"*60)

oid2 = create_order(customer_id, [{
    "description": "Due date test item",
    "count": 1,
    "unitPriceExcludingVatCurrency": 5000,
    "vatType": {"id": 3},
}])

inv2_r = create_invoice_from_order(oid2, due_date="2026-04-19")
pp("TEST2 - Create Invoice with due date 2026-04-19", inv2_r)
if inv2_r.status_code in (200, 201):
    inv2_data = inv2_r.json()["value"]
    print(f">>> invoiceDueDate returned: {inv2_data.get('invoiceDueDate')}")
    print(f">>> Expected: 2026-04-19")
    print(f">>> MATCH: {inv2_data.get('invoiceDueDate') == '2026-04-19'}")


# ══════════════════════════════════════════════════════════════
# TEST 3: Invoice with 15% VAT (middels sats)
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 3: Invoice with 15% VAT (middels sats)")
print("#"*60)

# First, look up what vatType IDs correspond to ~15%
print(">>> Looking up vatTypes near 15%...")
vt_resp = client.get("/ledger/vatType?from=0&count=300")
vt_all = vt_resp.json().get("values", [])
vat15_id = None
vat12_id = None
for vt in vt_all:
    pct = vt.get("percentage")
    name = vt.get("name", "")
    vid = vt.get("id")
    num = vt.get("number")
    if pct is not None and 14.5 <= pct <= 15.5:
        print(f"  15% candidate: id={vid}, number={num}, name={name}, pct={pct}%")
        if vat15_id is None:
            vat15_id = vid
    if pct is not None and 11.5 <= pct <= 12.5:
        print(f"  12% candidate: id={vid}, number={num}, name={name}, pct={pct}%")
        if vat12_id is None:
            vat12_id = vid

if vat15_id:
    oid3 = create_order(customer_id, [{
        "description": "Food product 15% VAT",
        "count": 1,
        "unitPriceExcludingVatCurrency": 10000,
        "vatType": {"id": vat15_id},
    }])
    if oid3:
        inv3_r = create_invoice_from_order(oid3)
        pp("TEST3 - Invoice with 15% VAT", inv3_r)
        if inv3_r.status_code in (200, 201):
            inv3_data = inv3_r.json()["value"]
            print(f">>> Total amount (incl VAT): {inv3_data.get('amount')}")
            print(f">>> Expected: 11500 (10000 + 15%)")
else:
    print(">>> No 15% vatType found. Trying vatType id=31 directly...")
    oid3 = create_order(customer_id, [{
        "description": "Food product 15% VAT (id=31)",
        "count": 1,
        "unitPriceExcludingVatCurrency": 10000,
        "vatType": {"id": 31},
    }])
    if oid3:
        inv3_r = create_invoice_from_order(oid3)
        pp("TEST3 - Invoice with vatType 31", inv3_r)
        if inv3_r.status_code in (200, 201):
            inv3_data = inv3_r.json()["value"]
            print(f">>> Total amount (incl VAT): {inv3_data.get('amount')}")


# ══════════════════════════════════════════════════════════════
# TEST 4: Invoice with 12% VAT (lav sats)
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 4: Invoice with 12% VAT (lav sats)")
print("#"*60)

if vat12_id:
    oid4 = create_order(customer_id, [{
        "description": "Transport 12% VAT",
        "count": 1,
        "unitPriceExcludingVatCurrency": 10000,
        "vatType": {"id": vat12_id},
    }])
    if oid4:
        inv4_r = create_invoice_from_order(oid4)
        pp("TEST4 - Invoice with 12% VAT", inv4_r)
        if inv4_r.status_code in (200, 201):
            inv4_data = inv4_r.json()["value"]
            print(f">>> Total amount (incl VAT): {inv4_data.get('amount')}")
            print(f">>> Expected: 11200 (10000 + 12%)")
else:
    print(">>> No 12% vatType found. Trying vatType id=32 and 33...")
    for try_id in [32, 33, 5, 6]:
        print(f"  Trying vatType id={try_id}...")
        oid4 = create_order(customer_id, [{
            "description": f"Transport 12% VAT (id={try_id})",
            "count": 1,
            "unitPriceExcludingVatCurrency": 10000,
            "vatType": {"id": try_id},
        }])
        if oid4:
            inv4_r = create_invoice_from_order(oid4)
            pp(f"TEST4 - Invoice with vatType {try_id}", inv4_r)
            if inv4_r.status_code in (200, 201):
                inv4_data = inv4_r.json()["value"]
                print(f">>> Total amount (incl VAT): {inv4_data.get('amount')}")
                break


# ══════════════════════════════════════════════════════════════
# TEST 5: Create order separately, then invoice it
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 5: Create order then invoice it")
print("#"*60)

order5_r = client.post("/order", json={
    "customer": {"id": customer_id},
    "orderDate": "2026-03-20",
    "deliveryDate": "2026-03-25",
    "orderLines": [{
        "description": "Order-to-invoice item A",
        "count": 2,
        "unitPriceExcludingVatCurrency": 3000,
        "vatType": {"id": 3},
    }, {
        "description": "Order-to-invoice item B",
        "count": 1,
        "unitPriceExcludingVatCurrency": 4000,
        "vatType": {"id": 3},
    }],
})
pp("TEST5 - Create Order", order5_r)
if order5_r.status_code in (200, 201):
    order5_id = order5_r.json()["value"]["id"]
    print(f">>> Order ID: {order5_id}")

    inv5_r = create_invoice_from_order(order5_id)
    pp("TEST5 - Invoice from Order", inv5_r)
    if inv5_r.status_code in (200, 201):
        inv5_data = inv5_r.json()["value"]
        print(f">>> Invoice ID: {inv5_data['id']}")
        print(f">>> Invoice amount: {inv5_data.get('amount')}")
        print(f">>> Expected: 12500 (2*3000 + 4000 = 10000 + 25% = 12500)")
        # Check order refs
        inv5_full = client.get(f"/invoice/{inv5_data['id']}?fields=*,orders(*)")
        if inv5_full.status_code == 200:
            orders_ref = inv5_full.json()["value"].get("orders", [])
            print(f">>> Orders referenced in invoice: {[o.get('id') for o in orders_ref]}")
            print(f">>> Original order ID was: {order5_id}")


# ══════════════════════════════════════════════════════════════
# TEST 6: Create reminder on unpaid invoice
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 6: Create reminder (purring) on unpaid invoice")
print("#"*60)

# Create a fresh unpaid invoice with a past due date
oid6 = create_order(customer_id, [{
    "description": "Overdue item for reminder test",
    "count": 1,
    "unitPriceExcludingVatCurrency": 8000,
    "vatType": {"id": 3},
}], order_date="2026-03-01")

if oid6:
    inv6_r = create_invoice_from_order(oid6, inv_date="2026-03-01", due_date="2026-03-15", send=True)
    pp("TEST6 - Create unpaid invoice (past due)", inv6_r)
    if inv6_r.status_code in (200, 201):
        inv6_id = inv6_r.json()["value"]["id"]
        print(f">>> Invoice ID for reminder: {inv6_id}")

        # Try createReminder
        rem6 = client.put(
            f"/invoice/{inv6_id}/:createReminder",
            params={"type": "REMINDER", "date": "2026-03-20", "dispatchType": "EMAIL"}
        )
        pp("TEST6 - Create Reminder", rem6)

        # Also try without params, in the body
        if rem6.status_code >= 400:
            print(">>> Trying with body params instead...")
            rem6b = client.put(
                f"/invoice/{inv6_id}/:createReminder",
                json={"type": "REMINDER", "date": "2026-03-20", "dispatchType": "EMAIL"}
            )
            pp("TEST6 - Reminder (body params)", rem6b)

        # Try GET to see if there's a reminder endpoint
        if rem6.status_code >= 400:
            print(">>> Checking /invoice/{id}/reminder endpoint...")
            rem6c = client.get(f"/reminder?invoiceId={inv6_id}")
            pp("TEST6 - GET reminders", rem6c)


# ══════════════════════════════════════════════════════════════
# TEST 7: Credit note on a PAID invoice
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 7: Credit note on PAID invoice")
print("#"*60)

oid7 = create_order(customer_id, [{
    "description": "Credit note test item",
    "count": 1,
    "unitPriceExcludingVatCurrency": 6000,
    "vatType": {"id": 3},
}])

if oid7:
    inv7_r = create_invoice_from_order(oid7, send=True)
    pp("TEST7 - Create Invoice", inv7_r)
    if inv7_r.status_code in (200, 201):
        inv7_id = inv7_r.json()["value"]["id"]
        inv7_amount = inv7_r.json()["value"].get("amount", 7500)
        print(f">>> Invoice ID: {inv7_id}, amount: {inv7_amount}")

        # Pay it fully
        pay7 = client.put(f"/invoice/{inv7_id}/:payment", json={
            "paymentDate": "2026-03-20",
            "paymentTypeId": bank_pt,
            "paidAmount": inv7_amount,
            "paidAmountCurrency": inv7_amount,
        })
        pp("TEST7 - Full Payment", pay7)

        # Verify fully paid
        inv7_check = client.get(f"/invoice/{inv7_id}")
        inv7_after = inv7_check.json()["value"]
        print(f">>> After payment - amountOutstanding: {inv7_after.get('amountOutstanding')}")

        # Now create credit note
        cn7 = client.put(f"/invoice/{inv7_id}/:createCreditNote", json={
            "comment": "Full credit on paid invoice test",
            "creditNoteEmail": "adv-test@example.com",
        })
        pp("TEST7 - Create Credit Note on PAID invoice", cn7)
        if cn7.status_code in (200, 201):
            cn7_data = cn7.json().get("value", {})
            print(f">>> Credit Note ID: {cn7_data.get('id')}")
            print(f">>> Credit Note amount: {cn7_data.get('amount')}")

            # Re-check original invoice
            inv7_final = client.get(f"/invoice/{inv7_id}")
            if inv7_final.status_code == 200:
                print(f">>> Original invoice amountOutstanding after credit: "
                      f"{inv7_final.json()['value'].get('amountOutstanding')}")
                print(f">>> Original invoice amountOutstandingTotal: "
                      f"{inv7_final.json()['value'].get('amountOutstandingTotal')}")


# ══════════════════════════════════════════════════════════════
# TEST 8: Invoice with discount on order line
# ══════════════════════════════════════════════════════════════
print("\n\n" + "#"*60)
print("# TEST 8: Invoice with 10% discount on order line")
print("#"*60)

oid8 = create_order(customer_id, [{
    "description": "Discounted item",
    "count": 1,
    "unitPriceExcludingVatCurrency": 10000,
    "vatType": {"id": 3},
    "discount": 10,
}])

if oid8:
    inv8_r = create_invoice_from_order(oid8)
    pp("TEST8 - Invoice with 10% discount", inv8_r)
    if inv8_r.status_code in (200, 201):
        inv8_data = inv8_r.json()["value"]
        print(f">>> Invoice total (incl VAT): {inv8_data.get('amount')}")
        print(f">>> Expected: 11250 (10000 - 10% = 9000, + 25% VAT = 11250)")

        # Check order line detail
        inv8_full = client.get(f"/invoice/{inv8_data['id']}?fields=*,orderLines(*)")
        if inv8_full.status_code == 200:
            lines = inv8_full.json()["value"].get("orderLines", [])
            for ln in lines:
                print(f"  OrderLine: unitPrice={ln.get('unitPriceExcludingVatCurrency')}, "
                      f"discount={ln.get('discount')}, "
                      f"amountExclVat={ln.get('amountExcludingVatCurrency')}, "
                      f"amountInclVat={ln.get('amountIncludingVatCurrency')}")
    else:
        # Discount might need to be on the order, not the invoice
        print(">>> Invoice failed; checking if order has discount preserved...")
        order8_check = client.get(f"/order/{oid8}?fields=*,orderLines(*)")
        if order8_check.status_code == 200:
            olines = order8_check.json()["value"].get("orderLines", [])
            for oln in olines:
                print(f"  Order line: discount={oln.get('discount')}, "
                      f"amountExcl={oln.get('amountExcludingVatCurrency')}")


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60)

client.close()
