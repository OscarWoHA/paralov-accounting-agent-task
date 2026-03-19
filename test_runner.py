"""
Test runner that sends prompts to the /solve endpoint and verifies results against the sandbox API.
Usage: python test_runner.py [test_number]
"""

import httpx
import json
import sys
import time

SOLVE_URL = "http://localhost:1234/solve"
BASE = "https://kkpqfuj-amager.tripletex.dev/v2"
TOKEN = "eyJ0b2tlbklkIjoyMTQ3NjI4NDgyLCJ0b2tlbiI6IjBhYjc0Yjg1LWZiMDEtNGZkOC1hMWFiLWY5Nzk3MWZiYjA3NiJ9"
AUTH = ("0", TOKEN)

COMPLEX_TESTS = [
    {
        "id": 1,
        "name": "Create customer + invoice + payment (full flow)",
        "prompt": "Kunden Vestland AS (org.nr 947291502) har ein uteståande faktura på 15000 kr eksklusiv MVA for \"Konsulenttjenester\". Registrer full betaling på denne fakturaen.",
        "verify": lambda: verify_payment_flow("Vestland AS", 15000, 18750),
    },
    {
        "id": 2,
        "name": "Create employee with start date and admin role",
        "prompt": "Opprett en ny ansatt som heter Erik Bakke, født 12. januar 1988. E-post: erik.bakke@example.org, startdato 1. mai 2026. Han skal være kontoadministrator.",
        "verify": lambda: verify_employee_admin("Erik", "Bakke", "erik.bakke@example.org", "1988-01-12"),
    },
    {
        "id": 3,
        "name": "Create 3 departments (multiple entities)",
        "prompt": "Opprett tre avdelinger i Tripletex: \"Salg\", \"Utvikling\" og \"Support\".",
        "verify": lambda: verify_departments(["Salg", "Utvikling", "Support"]),
    },
    {
        "id": 4,
        "name": "Create supplier with address (Portuguese)",
        "prompt": "Registe o fornecedor Montanha Lda com número de organização 984527163. Endereço: Rua Principal 45, 0150 Oslo. E-mail: contato@montanha.no.",
        "verify": lambda: verify_supplier("Montanha Lda", "984527163"),
    },
    {
        "id": 5,
        "name": "Create project with PM (German, multi-step)",
        "prompt": "Erstellen Sie das Projekt \"Digitalisierung Nord\" verknüpft mit dem Kunden Nordlicht GmbH (Org.-Nr. 961438720). Projektleiter ist Max Fischer (max.fischer@example.org).",
        "verify": lambda: verify_project("Digitalisierung Nord", "Nordlicht GmbH"),
    },
    {
        "id": 6,
        "name": "Create and send invoice (French, excl VAT)",
        "prompt": "Créez et envoyez une facture au client Beaumont SA (n° org. 938274615) pour 42000 NOK HT. La facture concerne Services de conseil.",
        "verify": lambda: verify_invoice("Beaumont SA", 42000, with_vat=True),
    },
    {
        "id": 7,
        "name": "Create product with VAT (Spanish)",
        "prompt": "Cree el producto \"Auditoría financiera\" con número de producto 5521. El precio es 18500 NOK sin IVA, utilizando la tasa estándar del 25%.",
        "verify": lambda: verify_product("Auditoría financiera", "5521", 18500),
    },
    {
        "id": 8,
        "name": "Create travel expense with details (Nynorsk)",
        "prompt": "Opprett ei reiserekning for den tilsette med tittelen \"Kundemøte Stavanger\". Reisa gjekk frå Bergen til Stavanger den 15. mars 2026, avreise kl. 08:00 og retur kl. 18:00. Det var ein dagstur.",
        "verify": lambda: verify_travel_expense("Kundemøte Stavanger"),
    },
    {
        "id": 9,
        "name": "Do nothing",
        "prompt": "Do nothing.",
        "verify": lambda: {"passed": True, "detail": "No verification needed"},
    },
    {
        "id": 10,
        "name": "Create customer with full address (English)",
        "prompt": "Register the customer Highland Corp with organization number 972183456. Address: Fjordveien 88, 5003 Bergen. Email: info@highland.no. Phone: +4755123456.",
        "verify": lambda: verify_customer_with_address("Highland Corp", "972183456", "Fjordveien 88", "5003", "Bergen"),
    },
]


def find_by_name(endpoint, name, fields="id,name"):
    """Search and filter by exact name match."""
    r = httpx.get(f"{BASE}/{endpoint}", auth=AUTH, params={"fields": fields, "count": 100})
    return [v for v in r.json().get("values", []) if v.get("name") == name]


def verify_payment_flow(customer_name, amount_excl, amount_incl):
    """Verify customer, invoice, and payment were all created."""
    customers = find_by_name("customer", customer_name, "id,name")
    if not customers:
        return {"passed": False, "detail": f"Customer '{customer_name}' not found"}

    r2 = httpx.get(f"{BASE}/invoice", auth=AUTH, params={
        "invoiceDateFrom": "2026-01-01", "invoiceDateTo": "2026-12-31",
        "customerId": str(customers[0]["id"]), "fields": "id,amountExcludingVat,amount,amountOutstanding"
    })
    invoices = r2.json().get("values", [])
    if not invoices:
        return {"passed": False, "detail": "No invoice found for customer"}

    inv = invoices[-1]
    checks = []
    if abs(inv.get("amountExcludingVat", 0) - amount_excl) < 1:
        checks.append("amount_excl OK")
    else:
        checks.append(f"amount_excl WRONG: {inv.get('amountExcludingVat')} != {amount_excl}")
    if abs(inv.get("amountOutstanding", 999) - 0) < 1:
        checks.append("payment OK (outstanding=0)")
    else:
        checks.append(f"payment WRONG: outstanding={inv.get('amountOutstanding')}")

    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def verify_employee_admin(first, last, email, dob):
    r = httpx.get(f"{BASE}/employee", auth=AUTH, params={
        "firstName": first, "lastName": last, "fields": "id,firstName,lastName,email,dateOfBirth"
    })
    employees = r.json().get("values", [])
    if not employees:
        return {"passed": False, "detail": f"Employee {first} {last} not found"}

    emp = employees[-1]
    checks = []
    checks.append(f"name={'OK' if emp['firstName']==first and emp['lastName']==last else 'WRONG'}")
    checks.append(f"email={'OK' if emp.get('email')==email else 'WRONG:'+str(emp.get('email'))}")
    checks.append(f"dob={'OK' if emp.get('dateOfBirth')==dob else 'WRONG:'+str(emp.get('dateOfBirth'))}")

    # Check entitlements
    r2 = httpx.get(f"{BASE}/employee/entitlement", auth=AUTH, params={
        "employeeId": emp["id"], "fields": "entitlementId"
    })
    ent_ids = [e["entitlementId"] for e in r2.json().get("values", [])]
    checks.append(f"admin={'OK' if 1 in ent_ids else 'MISSING entitlement 1'}")

    # Check employment
    r3 = httpx.get(f"{BASE}/employee/employment", auth=AUTH, params={
        "employeeId": emp["id"], "fields": "id,startDate"
    })
    employments = r3.json().get("values", [])
    if employments:
        checks.append(f"startDate={'OK' if employments[0].get('startDate')=='2026-05-01' else 'WRONG:'+str(employments[0].get('startDate'))}")
    else:
        checks.append("employment=MISSING")

    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def verify_departments(names):
    r = httpx.get(f"{BASE}/department", auth=AUTH, params={"fields": "id,name,departmentNumber"})
    depts = {d["name"] for d in r.json().get("values", [])}
    found = [n for n in names if n in depts]
    missing = [n for n in names if n not in depts]
    passed = len(missing) == 0
    return {"passed": passed, "detail": f"Found: {found}, Missing: {missing}"}


def verify_supplier(name, org_nr):
    r = httpx.get(f"{BASE}/supplier", auth=AUTH, params={"fields": "id,name,organizationNumber,isSupplier", "count": 100})
    suppliers = [s for s in r.json().get("values", []) if s.get("name") == name]
    if not suppliers:
        return {"passed": False, "detail": f"Supplier '{name}' not found"}
    s = suppliers[-1]
    checks = [
        f"name={'OK' if s['name']==name else 'WRONG'}",
        f"orgNr={'OK' if s.get('organizationNumber')==org_nr else 'WRONG'}",
        f"isSupplier={'OK' if s.get('isSupplier') else 'WRONG'}",
    ]
    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def verify_project(project_name, customer_name):
    r = httpx.get(f"{BASE}/project", auth=AUTH, params={
        "fields": "id,name,projectManager(firstName,lastName),customer(name),startDate", "count": 100
    })
    projects = [p for p in r.json().get("values", []) if p.get("name") == project_name]
    if not projects:
        return {"passed": False, "detail": f"Project '{project_name}' not found"}
    p = projects[-1]
    checks = [
        f"name={'OK' if p['name']==project_name else 'WRONG'}",
        f"customer={'OK' if p.get('customer',{}).get('name')==customer_name else 'WRONG:'+str(p.get('customer',{}).get('name'))}",
        f"PM={'OK' if p.get('projectManager') else 'MISSING'}",
        f"startDate={'OK' if p.get('startDate') else 'MISSING'}",
    ]
    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def verify_invoice(customer_name, amount_excl, with_vat=False):
    r = httpx.get(f"{BASE}/customer", auth=AUTH, params={"name": customer_name, "fields": "id,name"})
    customers = r.json().get("values", [])
    if not customers:
        return {"passed": False, "detail": f"Customer '{customer_name}' not found"}

    r2 = httpx.get(f"{BASE}/invoice", auth=AUTH, params={
        "invoiceDateFrom": "2026-01-01", "invoiceDateTo": "2026-12-31",
        "customerId": str(customers[0]["id"]), "fields": "id,amountExcludingVat,amount"
    })
    invoices = r2.json().get("values", [])
    if not invoices:
        return {"passed": False, "detail": "No invoice found"}

    inv = invoices[-1]
    checks = [f"amountExcl={'OK' if abs(inv.get('amountExcludingVat',0)-amount_excl)<1 else 'WRONG:'+str(inv.get('amountExcludingVat'))}"]
    if with_vat:
        expected = amount_excl * 1.25
        checks.append(f"amountIncl={'OK' if abs(inv.get('amount',0)-expected)<1 else 'WRONG:'+str(inv.get('amount'))+'!='+str(expected)}")
    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def verify_product(name, number, price):
    r = httpx.get(f"{BASE}/product", auth=AUTH, params={"name": name, "fields": "id,name,number,priceExcludingVatCurrency,vatType(id,percentage)"})
    products = r.json().get("values", [])
    if not products:
        return {"passed": False, "detail": f"Product '{name}' not found"}
    p = products[0]
    checks = [
        f"name={'OK' if p['name']==name else 'WRONG'}",
        f"number={'OK' if str(p.get('number',''))==number else 'WRONG:'+str(p.get('number'))}",
        f"price={'OK' if abs(p.get('priceExcludingVatCurrency',0)-price)<1 else 'WRONG:'+str(p.get('priceExcludingVatCurrency'))}",
    ]
    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def verify_travel_expense(title):
    r = httpx.get(f"{BASE}/travelExpense", auth=AUTH, params={"fields": "id,title,travelDetails"})
    expenses = [e for e in r.json().get("values", []) if title in (e.get("title") or "")]
    if not expenses:
        return {"passed": False, "detail": f"Travel expense '{title}' not found"}
    return {"passed": True, "detail": f"Found travel expense ID {expenses[0]['id']}"}


def verify_customer_with_address(name, org_nr, street, postal_code, city):
    r = httpx.get(f"{BASE}/customer", auth=AUTH, params={
        "fields": "id,name,organizationNumber,email,phoneNumber,postalAddress(addressLine1,postalCode,city)", "count": 100
    })
    customers = [c for c in r.json().get("values", []) if c.get("name") == name]
    if not customers:
        return {"passed": False, "detail": f"Customer '{name}' not found"}
    c = customers[-1]
    addr = c.get("postalAddress", {})
    checks = [
        f"name={'OK' if c['name']==name else 'WRONG'}",
        f"orgNr={'OK' if c.get('organizationNumber')==org_nr else 'WRONG'}",
        f"street={'OK' if addr.get('addressLine1')==street else 'WRONG:'+str(addr.get('addressLine1'))}",
        f"postal={'OK' if addr.get('postalCode')==postal_code else 'WRONG:'+str(addr.get('postalCode'))}",
        f"city={'OK' if addr.get('city')==city else 'WRONG:'+str(addr.get('city'))}",
    ]
    passed = all("OK" in c for c in checks)
    return {"passed": passed, "detail": ", ".join(checks)}


def run_test(test):
    print(f"\n{'='*60}")
    print(f"TEST {test['id']}: {test['name']}")
    print(f"Prompt: {test['prompt'][:100]}...")
    print(f"{'='*60}")

    payload = {
        "prompt": test["prompt"],
        "files": [],
        "tripletex_credentials": {
            "base_url": BASE,
            "session_token": TOKEN,
        }
    }

    start = time.time()
    try:
        r = httpx.post(SOLVE_URL, json=payload, timeout=300)
        elapsed = time.time() - start
        print(f"Response: {r.status_code} in {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"ERROR: {e} after {elapsed:.1f}s")
        return False

    # Wait a moment for data to settle
    time.sleep(1)

    # Verify
    result = test["verify"]()
    status = "PASS" if result["passed"] else "FAIL"
    print(f"Verification: {status} — {result['detail']}")
    print(f"Efficiency: {elapsed:.1f}s")
    return result["passed"]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_ids = [int(x) for x in sys.argv[1:]]
        tests = [t for t in COMPLEX_TESTS if t["id"] in test_ids]
    else:
        tests = COMPLEX_TESTS

    passed = 0
    failed = 0
    for test in tests:
        if run_test(test):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"{'='*60}")
