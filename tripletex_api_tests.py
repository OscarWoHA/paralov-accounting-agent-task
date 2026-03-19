import httpx
import json
import sys

BASE_URL = "https://kkpqfuj-amager.tripletex.dev/v2"
AUTH = ("0", "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9")

results = []

def report(test_num, title, passed, details=""):
    status = "PASS" if passed else "FAIL"
    results.append((test_num, title, status, details))
    print(f"\n{'='*70}")
    print(f"TEST {test_num}: {title} => [{status}]")
    if details:
        print(f"  {details}")
    print(f"{'='*70}")

def pp(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)

client = httpx.Client(base_url=BASE_URL, auth=AUTH, timeout=30.0)

# ============================================================
# TEST 1: Create customer with full address
# ============================================================
print("\n>>> TEST 1: Create customer with full address")
payload = {
    "name": "Skogheim AS",
    "organizationNumber": "893718729",
    "isCustomer": True,
    "email": "post@skogheim.no",
    "postalAddress": {
        "addressLine1": "Storgata 111",
        "postalCode": "7010",
        "city": "Trondheim"
    }
}
r = client.post("/customer", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    addr = val.get("postalAddress", {})
    addr_ok = (
        addr.get("addressLine1") == "Storgata 111"
        and addr.get("postalCode") == "7010"
        and addr.get("city") == "Trondheim"
    )
    report(1, "Create customer with full address",
           addr_ok,
           f"postalAddress match: {addr_ok} | addressLine1={addr.get('addressLine1')}, postalCode={addr.get('postalCode')}, city={addr.get('city')}")
else:
    report(1, "Create customer with full address", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 2: Create customer without address (minimal)
# ============================================================
print("\n>>> TEST 2: Create customer without address (minimal)")
payload = {
    "name": "Minimal AS",
    "isCustomer": True
}
r = client.post("/customer", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")
report(2, "Create customer without address (minimal)",
       r.status_code == 201,
       f"HTTP {r.status_code}")

# ============================================================
# TEST 3: Create supplier
# ============================================================
print("\n>>> TEST 3: Create supplier")
payload = {
    "name": "Dalheim AS",
    "organizationNumber": "892196753",
    "isSupplier": True,
    "email": "faktura@dalheim.no"
}
r = client.post("/supplier", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    is_supplier = val.get("isSupplier", None)
    is_customer = val.get("isCustomer", None)
    ok = is_supplier == True and is_customer == False
    report(3, "Create supplier",
           ok,
           f"isSupplier={is_supplier}, isCustomer={is_customer}")
else:
    report(3, "Create supplier", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 4: Create entity that is BOTH customer AND supplier
# ============================================================
print("\n>>> TEST 4: Create entity that is BOTH customer AND supplier")
payload = {
    "name": "Both AS",
    "isCustomer": True,
    "isSupplier": True
}
r = client.post("/customer", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    is_cust = val.get("isCustomer", None)
    is_supp = val.get("isSupplier", None)
    ok = is_cust == True and is_supp == True
    report(4, "Create entity BOTH customer AND supplier",
           ok,
           f"isCustomer={is_cust}, isSupplier={is_supp}")
else:
    report(4, "Create entity BOTH customer AND supplier", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 5: Create product with VAT
# ============================================================
print("\n>>> TEST 5: Create product with VAT")
payload = {
    "name": "Analyserapport",
    "number": "3637",
    "priceExcludingVatCurrency": 31900,
    "vatType": {"id": 3}
}
r = client.post("/product", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    price_incl = val.get("priceIncludingVatCurrency", None)
    expected = 39875.0  # 31900 * 1.25
    ok = price_incl is not None and abs(float(price_incl) - expected) < 0.01
    report(5, "Create product with VAT",
           ok,
           f"priceIncludingVatCurrency={price_incl}, expected={expected}")
else:
    report(5, "Create product with VAT", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 6: Create product WITHOUT VAT
# ============================================================
print("\n>>> TEST 6: Create product WITHOUT VAT")
payload = {
    "name": "Gratis tjeneste",
    "priceExcludingVatCurrency": 5000
}
r = client.post("/product", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    vat_type = val.get("vatType", None)
    vat_id = None
    if vat_type and isinstance(vat_type, dict):
        vat_id = vat_type.get("id", None)
    # Accept: no vatType, vatType is None, or vatType id is 0
    ok = vat_type is None or vat_id == 0 or vat_id is None
    report(6, "Create product WITHOUT VAT",
           ok,
           f"vatType={vat_type}")
else:
    report(6, "Create product WITHOUT VAT", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 7: Create product with number as string
# ============================================================
print("\n>>> TEST 7: Create product with number as string")
payload = {
    "name": "String Number Product",
    "number": "4775",
    "priceExcludingVatCurrency": 100
}
r = client.post("/product", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")
report(7, "Create product with number as string",
       r.status_code == 201,
       f"HTTP {r.status_code} - number field accepted as string")

# ============================================================
# TEST 8: Create customer with physicalAddress AND postalAddress
# ============================================================
print("\n>>> TEST 8: Create customer with physicalAddress AND postalAddress")
payload = {
    "name": "DualAddr AS",
    "isCustomer": True,
    "postalAddress": {
        "addressLine1": "Postboks 22",
        "postalCode": "0101",
        "city": "Oslo"
    },
    "physicalAddress": {
        "addressLine1": "Kongens gate 5",
        "postalCode": "0153",
        "city": "Oslo"
    }
}
r = client.post("/customer", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    postal = val.get("postalAddress", {})
    physical = val.get("physicalAddress", {})
    postal_ok = postal.get("addressLine1") == "Postboks 22" and postal.get("postalCode") == "0101"
    physical_ok = physical.get("addressLine1") == "Kongens gate 5" and physical.get("postalCode") == "0153"
    ok = postal_ok and physical_ok
    report(8, "Create customer with physicalAddress AND postalAddress",
           ok,
           f"postalAddress OK={postal_ok} (addressLine1={postal.get('addressLine1')}), physicalAddress OK={physical_ok} (addressLine1={physical.get('addressLine1')})")
else:
    report(8, "Create customer with physicalAddress AND postalAddress", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 9: Verify isCustomer defaults to false
# ============================================================
print("\n>>> TEST 9: Verify isCustomer defaults to false")
payload = {
    "name": "Default Test"
    # deliberately omitting isCustomer
}
r = client.post("/customer", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    is_cust = val.get("isCustomer", "MISSING")
    report(9, "Verify isCustomer defaults to false",
           is_cust == False,
           f"isCustomer={is_cust} (expected False)")
else:
    # Even a non-201 is informative
    report(9, "Verify isCustomer defaults to false", False, f"HTTP {r.status_code}: {r.text[:300]}")

# ============================================================
# TEST 10: Verify isSupplier defaults to false on /supplier
# ============================================================
print("\n>>> TEST 10: Verify isSupplier defaults to false on /supplier")
payload = {
    "name": "Supplier Default"
    # deliberately omitting isSupplier
}
r = client.post("/supplier", json=payload)
print(f"  Status: {r.status_code}")
body = r.json()
print(f"  Response: {pp(body)}")

if r.status_code == 201:
    val = body.get("value", body)
    is_supp = val.get("isSupplier", "MISSING")
    report(10, "Verify isSupplier defaults to false on /supplier",
           is_supp == False,
           f"isSupplier={is_supp} (expected False)")
else:
    report(10, "Verify isSupplier defaults to false on /supplier", False, f"HTTP {r.status_code}: {r.text[:300]}")

client.close()

# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n\n" + "="*70)
print("FINAL SUMMARY")
print("="*70)
pass_count = sum(1 for r in results if r[2] == "PASS")
fail_count = sum(1 for r in results if r[2] == "FAIL")
for num, title, status, details in results:
    marker = "PASS" if status == "PASS" else "FAIL"
    print(f"  TEST {num:>2}: [{marker}] {title}")
    if details:
        print(f"           {details}")
print(f"\nTotal: {pass_count} passed, {fail_count} failed out of {len(results)} tests")
