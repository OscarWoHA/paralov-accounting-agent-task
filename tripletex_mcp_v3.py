"""MCP server with a single Tripletex API tool + field validation.

The agent gets full API freedom. Validation catches bad field names
before they hit the API, saving round trips.
"""

import json
import logging
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MCP] %(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)

mcp = FastMCP("tripletex")

BASE_URL = os.environ.get("TX_BASE_URL", "")
TOKEN = os.environ.get("TX_TOKEN", "")


# ── Field validation sets (verified from live Tripletex API) ──────────

DTO_FIELDS = {
    "invoice": {"id", "version", "invoiceNumber", "invoiceDate", "customer", "creditedInvoice", "isCredited", "invoiceDueDate", "kid", "invoiceComment", "comment", "orders", "orderLines", "travelReports", "projectInvoiceDetails", "voucher", "deliveryDate", "amount", "amountCurrency", "amountExcludingVat", "amountExcludingVatCurrency", "amountRoundoff", "amountRoundoffCurrency", "amountOutstanding", "amountCurrencyOutstanding", "amountOutstandingTotal", "amountCurrencyOutstandingTotal", "sumRemits", "currency", "isCreditNote", "isCharged", "isApproved", "postings", "reminders", "invoiceRemarks", "invoiceRemark", "isPeriodizationPossible", "documentId"},
    "employee": {"id", "version", "firstName", "lastName", "displayName", "employeeNumber", "dateOfBirth", "email", "phoneNumberMobileCountry", "phoneNumberMobile", "phoneNumberHome", "phoneNumberWork", "nationalIdentityNumber", "dnumber", "internationalId", "bankAccountNumber", "iban", "bic", "creditorBankCountryId", "usesAbroadPayment", "userType", "allowInformationRegistration", "isContact", "isProxy", "comments", "address", "department", "employments", "holidayAllowanceEarned", "employeeCategory", "pictureId", "companyId"},
    "customer": {"id", "version", "name", "organizationNumber", "globalLocationNumber", "supplierNumber", "customerNumber", "isSupplier", "isCustomer", "isInactive", "accountManager", "department", "email", "invoiceEmail", "overdueNoticeEmail", "phoneNumber", "phoneNumberMobile", "description", "language", "displayName", "isPrivateIndividual", "singleCustomerInvoice", "invoiceSendMethod", "emailAttachmentType", "postalAddress", "physicalAddress", "deliveryAddress", "category1", "category2", "category3", "invoicesDueIn", "invoicesDueInType", "currency", "bankAccountPresentation", "ledgerAccount", "isFactoring", "discountPercentage", "website"},
    "supplier": {"id", "version", "name", "organizationNumber", "supplierNumber", "customerNumber", "isSupplier", "isCustomer", "isInactive", "email", "invoiceEmail", "overdueNoticeEmail", "phoneNumber", "phoneNumberMobile", "description", "isPrivateIndividual", "showProducts", "accountManager", "postalAddress", "physicalAddress", "deliveryAddress", "category1", "category2", "category3", "bankAccountPresentation", "currency", "ledgerAccount", "language", "isWholesaler", "displayName", "website"},
    "product": {"id", "version", "name", "number", "displayNumber", "description", "orderLineDescription", "ean", "elNumber", "nrfNumber", "costExcludingVatCurrency", "expenses", "expensesInPercent", "costPrice", "profit", "profitInPercent", "priceExcludingVatCurrency", "priceIncludingVatCurrency", "isInactive", "productUnit", "isStockItem", "stockOfGoods", "vatType", "currency", "department", "account", "discountPrice", "supplier", "weight", "weightUnit", "volume", "volumeUnit", "displayName"},
    "project": {"id", "version", "name", "number", "displayName", "description", "projectManager", "department", "mainProject", "startDate", "endDate", "customer", "isClosed", "isReadyForInvoicing", "isInternal", "isOffer", "isFixedPrice", "projectCategory", "deliveryAddress", "displayNameFormat", "reference", "externalAccountsNumber", "discountPercentage", "vatType", "fixedprice", "contributionMarginPercent", "numberOfSubProjects", "numberOfProjectParticipants", "orderLines", "currency", "markUpOrderLines", "markUpFeesEarned", "isPriceCeiling", "priceCeilingAmount", "projectHourlyRates", "participants", "contact", "attention", "invoiceComment", "invoicingPlan", "preliminaryInvoice", "projectActivities", "invoiceDueDate", "invoiceDueDateType", "accessType", "useProductNetPrice", "accountingDimensionValues"},
    "department": {"id", "version", "name", "departmentNumber", "departmentManager", "displayName", "isInactive", "businessActivityTypeId"},
    "posting": {"id", "version", "voucher", "date", "description", "account", "amortizationAccount", "amortizationStartDate", "amortizationEndDate", "customer", "supplier", "employee", "project", "product", "department", "vatType", "amount", "amountCurrency", "amountGross", "amountGrossCurrency", "currency", "closeGroup", "invoiceNumber", "termOfPayment", "row", "type", "externalRef", "systemGenerated", "matched", "freeAccountingDimension1", "freeAccountingDimension2", "freeAccountingDimension3"},
    "travelExpense": {"id", "version", "attestationSteps", "attestation", "project", "employee", "approvedBy", "completedBy", "rejectedBy", "department", "payslip", "vatType", "paymentCurrency", "travelDetails", "voucher", "attachment", "isCompleted", "isApproved", "completedDate", "approvedDate", "date", "travelAdvance", "fixedInvoicedAmount", "amount", "chargeableAmountCurrency", "paymentAmount", "chargeableAmount", "lowRateVAT", "mediumRateVAT", "highRateVAT", "paymentAmountCurrency", "number", "invoice", "title", "displayName", "perDiemCompensations", "mileageAllowances", "accommodationAllowances", "costs", "attachmentCount", "state", "actions", "type"},
    "employment": {"id", "version", "employee", "employmentId", "startDate", "endDate", "employmentEndReason", "division", "lastSalaryChangeDate", "noEmploymentRelationship", "isMainEmployer", "taxDeductionCode", "employmentDetails", "isRemoveAccessAtEmploymentEnded", "latestSalary"},
    "employmentDetails": {"id", "version", "employment", "date", "employmentType", "employmentForm", "remunerationType", "workingHoursScheme", "shiftDurationHours", "occupationCode", "percentageOfFullTimeEquivalent", "annualSalary", "hourlyWage", "payrollTaxMunicipalityId", "monthlySalary"},
}

# Map endpoint paths to DTO names for field validation
ENDPOINT_DTO_MAP = {
    "/invoice": "invoice",
    "/employee": "employee",
    "/customer": "customer",
    "/supplier": "supplier",
    "/product": "product",
    "/project": "project",
    "/department": "department",
    "/ledger/posting": "posting",
    "/travelExpense": "travelExpense",
    "/employee/employment": "employment",
    "/employee/employment/details": "employmentDetails",
}


def _validate_fields(endpoint: str, params: dict | None) -> str | None:
    """Validate ?fields= parameter against known DTOs. Returns error string or None."""
    if not params or "fields" not in params:
        return None

    # Find matching DTO
    dto_name = None
    for path, name in ENDPOINT_DTO_MAP.items():
        if endpoint.rstrip("/") == path or endpoint.startswith(path + "?") or endpoint.startswith(path + "/"):
            # Don't match sub-paths like /invoice/paymentType to invoice DTO
            remainder = endpoint[len(path):]
            if not remainder or remainder[0] in ("?", "/"):
                # Check it's not a deeper sub-resource
                if remainder and remainder[0] == "/" and not remainder[1:].isdigit():
                    subpath = path + remainder.split("?")[0]
                    if subpath in ENDPOINT_DTO_MAP:
                        dto_name = ENDPOINT_DTO_MAP[subpath]
                        break
                dto_name = name
                break

    if not dto_name or dto_name not in DTO_FIELDS:
        return None  # Unknown endpoint, skip validation

    valid = DTO_FIELDS[dto_name]
    # Parse fields, handling nested like account(number,name)
    requested = [f.split("(")[0].strip() for f in str(params["fields"]).split(",")]
    invalid = [f for f in requested if f and f != "*" and f not in valid]

    if invalid:
        return json.dumps({
            "status_code": 400,
            "validation_error": f"Invalid fields for {dto_name}: {', '.join(invalid)}. Valid: {', '.join(sorted(valid))}"
        })
    return None


# ── The single tool ───────────────────────────────────────────────────

@mcp.tool()
def tripletex(method: str, endpoint: str, params: dict | None = None, body: dict | list | None = None) -> str:
    """Make an HTTP request to the Tripletex v2 REST API.

    Args:
        method: GET, POST, PUT, or DELETE
        endpoint: API path like /employee, /invoice/123, /invoice/123/:payment, /ledger/voucher
        params: Query parameters — filters, field selection (?fields=id,name), pagination (?count=100&from=0)
        body: JSON body for POST/PUT

    Field selection: use ?fields=id,name,... to select fields. Nested fields use parentheses: account(number,name).
    Pagination: use ?count=N&from=M. Results: {"fullResultSize": N, "values": [...]} for lists, {"value": {...}} for single.
    References: {"id": N}. Dates: "YYYY-MM-DD".
    PUT action endpoints (/:payment, /:createCreditNote, /:deliver, /:reverse) take action data as query params, not body.
    """
    # Validate fields param before making the request
    if err := _validate_fields(endpoint, params):
        logger.warning(f"FIELD VALIDATION: {err}")
        return err

    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    url = f"{BASE_URL}{endpoint}"
    auth = ("0", TOKEN)

    body_str = json.dumps(body, ensure_ascii=False) if body else None
    logger.info(f">>> {method} {endpoint} params={params} body={body_str}")

    r = httpx.request(method=method, url=url, auth=auth, params=params, json=body if body else None, timeout=30.0)

    try:
        resp = r.json()
    except Exception:
        resp = r.text

    # Truncate large list responses
    if isinstance(resp, dict) and "values" in resp and isinstance(resp["values"], list) and len(resp["values"]) > 40:
        resp = {**resp, "values": resp["values"][:40], "_truncated": f"Showing 40 of {len(resp['values'])}"}

    logger.info(f"<<< {r.status_code}")

    result = json.dumps({"status_code": r.status_code, "body": resp}, ensure_ascii=False)
    return result[:15000] + '..."}' if len(result) > 15000 else result


# ── Setup helper (bank account + VAT) ─────────────────────────────────

@mcp.tool()
def setup(action: str) -> str:
    """Sandbox setup utilities. Call before invoicing or when needed.

    Actions:
      ensure_bank_account  — Checks account 1920 and sets bankAccountNumber if empty. MUST call before creating invoices.
      ensure_vat_registered — Registers for VAT if not already registered.
      whoami               — Returns company info (company ID needed for admin entitlements).
      init                 — Returns all common reference data in ONE call: bank account setup + voucherTypes + paymentTypes + departments. Call this FIRST to save multiple lookups.
    """
    if action == "ensure_bank_account":
        r = tripletex("GET", "/ledger/account", params={"number": "1920", "fields": "id,version,bankAccountNumber"})
        data = json.loads(r)
        if data.get("status_code") == 200:
            values = data.get("body", {}).get("values", [])
            if values and not values[0].get("bankAccountNumber"):
                acc = values[0]
                return tripletex("PUT", f"/ledger/account/{acc['id']}", body={
                    "id": acc["id"], "version": acc["version"], "bankAccountNumber": "28002111480"
                })
            elif values:
                return json.dumps({"status_code": 200, "message": "Bank account already configured", "body": values[0]})
        return r
    elif action == "ensure_vat_registered":
        r = tripletex("GET", "/ledger/vatSettings", params={"fields": "id,version,vatRegistrationStatus"})
        data = json.loads(r)
        if data.get("status_code") == 200:
            val = data.get("body", {}).get("value", {})
            if val and val.get("vatRegistrationStatus") != "VAT_REGISTERED":
                return tripletex("PUT", f"/ledger/vatSettings/{val['id']}", body={
                    "id": val["id"], "version": val["version"], "vatRegistrationStatus": "VAT_REGISTERED"
                })
            elif val:
                return json.dumps({"status_code": 200, "message": "Already VAT registered"})
        return r
    elif action == "whoami":
        return tripletex("GET", "/token/session/>whoAmI")
    elif action == "init":
        # One call that returns everything the agent commonly needs
        results = {}

        # 1. Ensure bank account
        bank_r = tripletex("GET", "/ledger/account", params={"number": "1920", "fields": "id,version,bankAccountNumber"})
        bank_data = json.loads(bank_r)
        if bank_data.get("status_code") == 200:
            values = bank_data.get("body", {}).get("values", [])
            if values and not values[0].get("bankAccountNumber"):
                acc = values[0]
                tripletex("PUT", f"/ledger/account/{acc['id']}", body={
                    "id": acc["id"], "version": acc["version"], "bankAccountNumber": "28002111480"
                })
                results["bankAccount"] = "configured"
            elif values:
                results["bankAccount"] = "already configured"

        # 2. Voucher types
        vt_r = tripletex("GET", "/ledger/voucherType", params={"fields": "id,name"})
        vt_data = json.loads(vt_r)
        if vt_data.get("status_code") == 200:
            results["voucherTypes"] = {v["name"]: v["id"] for v in vt_data.get("body", {}).get("values", [])}

        # 3. Invoice payment types (bypass validation by using direct HTTP)
        endpoint = "/invoice/paymentType"
        url = f"{BASE_URL}{endpoint}"
        r = httpx.get(url, auth=("0", TOKEN), params={"fields": "id,description"}, timeout=30.0)
        try:
            pt_resp = r.json()
        except Exception:
            pt_resp = {"values": []}
        pt_r = json.dumps({"status_code": r.status_code, "body": pt_resp})
        pt_data = json.loads(pt_r)
        if pt_data.get("status_code") == 200:
            results["paymentTypes"] = {v["description"]: v["id"] for v in pt_data.get("body", {}).get("values", [])}

        # 4. Departments
        dept_r = tripletex("GET", "/department", params={"fields": "id,name,departmentNumber"})
        dept_data = json.loads(dept_r)
        if dept_data.get("status_code") == 200:
            results["departments"] = {v["name"]: v["id"] for v in dept_data.get("body", {}).get("values", [])}

        # 5. Employees (first 10)
        emp_r = tripletex("GET", "/employee", params={"fields": "id,firstName,lastName,email", "count": "10"})
        emp_data = json.loads(emp_r)
        if emp_data.get("status_code") == 200:
            results["employees"] = [{"id": v["id"], "name": f"{v['firstName']} {v['lastName']}", "email": v.get("email","")} for v in emp_data.get("body", {}).get("values", [])]

        return json.dumps({"status_code": 200, "body": results}, ensure_ascii=False)
    else:
        return json.dumps({"error": f"Unknown action: {action}"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
