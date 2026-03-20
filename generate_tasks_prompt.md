You are generating test tasks for an AI accounting agent competition called "NM i AI" (Norwegian AI Championship). The agent receives a task prompt and must execute it using the Tripletex accounting API.

## Competition Details
- 30 unique task types across 7 categories
- Each task has 56 variants (7 languages x 8 data sets)
- Languages: Norwegian Bokmal, Norwegian Nynorsk, English, Spanish, Portuguese, German, French
- The agent gets a fresh empty Tripletex sandbox for each task
- Scored field-by-field on correctness + efficiency bonus for minimal API calls

## Task Categories and What They Test

**1. Employees** (Tier 1)
- Create employee with name, email, date of birth, start date
- Create employee as administrator (kontoadministrator)
- Update employee contact info (phone, address)
- Possible checks: name, email, dateOfBirth, startDate, admin role assigned

**2. Customers & Products** (Tier 1)
- Register customer with org number, address, email, phone
- Register supplier (leverandor) -- different from customer!
- Create product with product number, price, VAT rate
- Possible checks: name, orgNumber, address fields, email, isCustomer/isSupplier, product number, price, vatType

**3. Invoicing** (Tier 2)
- Create and send invoice to a customer (with amount excl/incl VAT)
- Register full or partial payment on an invoice
- Create credit note for an invoice
- Possible checks: customer correct, amount excl VAT, amount incl VAT, VAT applied, payment registered, outstanding = 0

**4. Travel Expenses** (Tier 1-2)
- Create travel expense report for an employee
- Add costs (hotel, taxi, flights) to travel expense
- Delete a travel expense
- Possible checks: title, employee, travel details, costs, amounts

**5. Projects** (Tier 2)
- Create project linked to customer with a project manager
- Possible checks: project name, customer linked, PM assigned, start date

**6. Corrections** (Tier 2-3)
- Delete or reverse incorrect entries
- Create credit note to cancel an invoice
- Possible checks: entity deleted, voucher reversed, credit note exists

**7. Departments** (Tier 1)
- Create one or multiple departments
- Enable accounting modules
- Possible checks: department names, department numbers

## Rules for Generating Tasks
1. Each task is a single prompt in one of the 7 languages
2. Use realistic Norwegian company names (end in AS, ASA) or international names (Ltd, GmbH, SA, Lda)
3. Organization numbers are 9 digits
4. Amounts are in NOK (kr)
5. VAT phrasing varies by language:
   - "eksklusiv MVA" / "excluding VAT" / "ohne MwSt" / "HT" / "sin IVA" / "sem IVA" = price BEFORE VAT, VAT still applies at 25%
   - "inklusiv MVA" / "including VAT" / "TTC" / "brutto" / "con IVA" / "com IVA" = price INCLUDES VAT
   - "uten mva" / "mva-fritt" / "VAT-exempt" = NO VAT at all
6. Nynorsk uses "ein" not "en", "tilsett" not "ansatt", "reiserekning" not "reiseregning", "avdelingar" not "avdelinger"
7. Some tasks are multi-step: e.g., "register payment on an invoice" requires creating customer -> invoice -> payment
8. Some tasks ask for multiple entities: "Create 3 departments"
9. Dates use European format: "15. mars 2026" or "15. March 2026"

## Generate 100 diverse test tasks

For each task, provide:
```json
{
  "id": 1,
  "category": "Invoicing",
  "language": "Norwegian Bokmal",
  "tier": 2,
  "prompt": "the actual task prompt text",
  "expected_entities": "brief description of what should be created"
}
```

Requirements:
- Cover ALL 7 categories proportionally (more invoicing since it's Tier 2-3)
- Use ALL 7 languages (at least 10 per language)
- Include simple single-step tasks AND complex multi-step tasks
- Include edge cases: addresses, phone numbers, VAT variations, multiple entities, specific dates
- Include tasks that test tricky distinctions: supplier vs customer, excl vs incl VAT, employee start date vs birth date
- Vary company names, amounts, product names, employee names across cultures
- Include some "do nothing" or minimal tasks
- Make amounts realistic (1000-500000 NOK range)

Generate all 100 tasks now.
