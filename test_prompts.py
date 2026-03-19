"""
50 diverse test prompts for the Tripletex AI Competition.

Covers all 7 categories, 30 task types, 7 languages, and critical edge cases.
Each prompt includes: text, expected API sequence, scored checks, and pitfalls.
"""

TEST_PROMPTS = [

    # =========================================================================
    # CATEGORY 1: EMPLOYEES (8 prompts)
    # =========================================================================

    {
        "id": 1,
        "category": "Employees",
        "task_type": "Create employee (basic)",
        "language": "Norwegian Bokmål",
        "prompt": "Vi har en ny ansatt som heter Lars Hansen, født 15. mars 1990. Opprett ham som ansatt med e-post lars.hansen@example.no og startdato 1. juni 2026.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "POST /employee {firstName: 'Lars', lastName: 'Hansen', email: 'lars.hansen@example.no', dateOfBirth: '1990-03-15', userType: 'STANDARD', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/employment {employee: {id: EMP_ID}, startDate: '2026-06-01', isMainEmployer: true, taxDeductionCode: 'loennFraHovedarbeidsgiver', employmentDetails: [{date: '2026-06-01', ...}]}"
        ],
        "scored_checks": [
            "Employee exists with firstName='Lars', lastName='Hansen'",
            "Email matches 'lars.hansen@example.no'",
            "dateOfBirth = '1990-03-15'",
            "Employment record with startDate = '2026-06-01'"
        ],
        "pitfalls": [
            "Forgetting to look up department ID first (required field)",
            "Parsing Norwegian date '15. mars 1990' incorrectly",
            "Forgetting the POST /employee/employment for the start date (separate endpoint)",
            "Not setting allowInformationRegistration: true"
        ]
    },

    {
        "id": 2,
        "category": "Employees",
        "task_type": "Create employee (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Vi har ein ny tilsett som heiter Kari Berge, fødd 22. august 1985. Opprett ho som tilsett med e-post kari.berge@example.no og startdato 15. april 2026.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "POST /employee {firstName: 'Kari', lastName: 'Berge', email: 'kari.berge@example.no', dateOfBirth: '1985-08-22', userType: 'STANDARD', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/employment {employee: {id: EMP_ID}, startDate: '2026-04-15', ...}"
        ],
        "scored_checks": [
            "Employee exists with correct name",
            "dateOfBirth = '1985-08-22'",
            "Email correct",
            "Employment with startDate = '2026-04-15'"
        ],
        "pitfalls": [
            "Not recognizing 'tilsett' (Nynorsk) = 'ansatt' (Bokmål) = employee",
            "Parsing 'fødd' (Nynorsk for born)",
            "Same API endpoints for both Norwegian variants"
        ]
    },

    {
        "id": 3,
        "category": "Employees",
        "task_type": "Create employee with admin role",
        "language": "English",
        "prompt": "Create a new employee named Sarah Johnson, born 5. July 1988, with email sarah.johnson@example.org. She should have administrator access.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /employee {firstName: 'Sarah', lastName: 'Johnson', email: 'sarah.johnson@example.org', dateOfBirth: '1988-07-05', userType: 'EXTENDED', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/entitlement {employee: {id: EMP_ID}, entitlementId: 1, customer: {id: COMPANY_ID}}"
        ],
        "scored_checks": [
            "Employee exists with correct name and email",
            "userType = 'EXTENDED'",
            "Has entitlement with entitlementId=1 (admin)"
        ],
        "pitfalls": [
            "Using userType 'STANDARD' instead of 'EXTENDED' (admin requires EXTENDED)",
            "Using customer ID instead of company ID in entitlement 'customer' field",
            "Not knowing entitlementId 1 = admin",
            "Forgetting that the 'customer' field in entitlement = COMPANY_ID from whoAmI"
        ]
    },

    {
        "id": 4,
        "category": "Employees",
        "task_type": "Create employee (Spanish)",
        "language": "Spanish",
        "prompt": "Tenemos un nuevo empleado llamado Carlos Mendoza, nacido el 12. enero 1993. Créelo como empleado con el correo carlos.mendoza@example.org y fecha de inicio 10. marzo 2026.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "POST /employee {firstName: 'Carlos', lastName: 'Mendoza', email: 'carlos.mendoza@example.org', dateOfBirth: '1993-01-12', userType: 'STANDARD', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/employment {employee: {id: EMP_ID}, startDate: '2026-03-10', ...}"
        ],
        "scored_checks": [
            "Employee exists with name 'Carlos Mendoza'",
            "dateOfBirth = '1993-01-12'",
            "Employment startDate = '2026-03-10'"
        ],
        "pitfalls": [
            "Parsing Spanish date format '12. enero 1993'",
            "Recognizing 'empleado' = employee, 'fecha de inicio' = start date"
        ]
    },

    {
        "id": 5,
        "category": "Employees",
        "task_type": "Create employee (French)",
        "language": "French",
        "prompt": "Nous avons un nouvel employé nommé Pierre Dupont, né le 3. septembre 1979. Créez-le comme employé avec l'e-mail pierre.dupont@example.org et la date de début 1. mai 2026.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "POST /employee {firstName: 'Pierre', lastName: 'Dupont', email: 'pierre.dupont@example.org', dateOfBirth: '1979-09-03', userType: 'STANDARD', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/employment {employee: {id: EMP_ID}, startDate: '2026-05-01', ...}"
        ],
        "scored_checks": [
            "Employee exists with name 'Pierre Dupont'",
            "dateOfBirth = '1979-09-03'",
            "Employment startDate = '2026-05-01'"
        ],
        "pitfalls": [
            "Parsing French date: '3. septembre 1979'",
            "Recognizing 'employé' = employee, 'date de début' = start date"
        ]
    },

    {
        "id": 6,
        "category": "Employees",
        "task_type": "Create employee with project manager role",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett den ansatte Erik Lund, født 7. november 1984, e-post erik.lund@example.no. Han skal være prosjektleder.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /employee {firstName: 'Erik', lastName: 'Lund', email: 'erik.lund@example.no', dateOfBirth: '1984-11-07', userType: 'EXTENDED', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/entitlement {employee: {id: EMP_ID}, entitlementId: 45, customer: {id: COMPANY_ID}}",
            "POST /employee/entitlement {employee: {id: EMP_ID}, entitlementId: 10, customer: {id: COMPANY_ID}}"
        ],
        "scored_checks": [
            "Employee exists with correct name",
            "userType = 'EXTENDED'",
            "Has entitlementId=45 (AUTH_CREATE_PROJECT, prerequisite)",
            "Has entitlementId=10 (AUTH_PROJECT_MANAGER)"
        ],
        "pitfalls": [
            "Forgetting the prerequisite entitlement 45 before granting 10",
            "Using STANDARD userType (project manager needs EXTENDED)",
            "Only granting entitlement 10 without the prerequisite 45"
        ]
    },

    {
        "id": 7,
        "category": "Employees",
        "task_type": "Create employee (German)",
        "language": "German",
        "prompt": "Wir haben einen neuen Mitarbeiter namens Hans Müller, geboren am 18. Februar 1991. Erstellen Sie ihn als Mitarbeiter mit der E-Mail hans.mueller@example.org und Startdatum 1. Juli 2026.",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "POST /employee {firstName: 'Hans', lastName: 'Müller', email: 'hans.mueller@example.org', dateOfBirth: '1991-02-18', userType: 'STANDARD', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/employment {employee: {id: EMP_ID}, startDate: '2026-07-01', ...}"
        ],
        "scored_checks": [
            "Employee exists with name 'Hans Müller'",
            "Email = 'hans.mueller@example.org'",
            "Employment startDate = '2026-07-01'"
        ],
        "pitfalls": [
            "Parsing German date: '18. Februar 1991'",
            "Handling special character 'ü' in lastName correctly",
            "Recognizing 'Mitarbeiter' = employee, 'Startdatum' = start date"
        ]
    },

    {
        "id": 8,
        "category": "Employees",
        "task_type": "Update employee contact info",
        "language": "English",
        "prompt": "Update the employee Ella Harris's email to ella.newemail@example.org.",
        "expected_api_calls": [
            "GET /employee?firstName=Ella&lastName=Harris&fields=id,version,firstName,lastName,dateOfBirth,email",
            "PUT /employee/{id} {id: ID, version: VERSION, firstName: 'Ella', lastName: 'Harris', dateOfBirth: '...', email: 'ella.newemail@example.org'}"
        ],
        "scored_checks": [
            "Employee 'Ella Harris' now has email 'ella.newemail@example.org'"
        ],
        "pitfalls": [
            "Not including version in PUT request (required for optimistic locking)",
            "Not including required fields (firstName, lastName, dateOfBirth) in PUT body",
            "Finding the wrong employee if multiple exist"
        ]
    },

    # =========================================================================
    # CATEGORY 2: CUSTOMERS & PRODUCTS (10 prompts)
    # =========================================================================

    {
        "id": 9,
        "category": "Customers & Products",
        "task_type": "Create customer with address (Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett kunden Fjordvik AS med organisasjonsnummer 912345678. Adressen er Havnegata 45, 5003 Bergen. E-post: post@fjordvik.no.",
        "expected_api_calls": [
            "POST /customer {name: 'Fjordvik AS', organizationNumber: '912345678', isCustomer: true, email: 'post@fjordvik.no', postalAddress: {addressLine1: 'Havnegata 45', postalCode: '5003', city: 'Bergen'}}"
        ],
        "scored_checks": [
            "Customer exists with name 'Fjordvik AS'",
            "organizationNumber = '912345678'",
            "isCustomer = true",
            "email = 'post@fjordvik.no'",
            "postalAddress.addressLine1 = 'Havnegata 45'",
            "postalAddress.postalCode = '5003'",
            "postalAddress.city = 'Bergen'"
        ],
        "pitfalls": [
            "Not setting isCustomer: true (defaults to false!)",
            "Using 'address' instead of 'postalAddress'",
            "Putting full address in a single field instead of structured"
        ]
    },

    {
        "id": 10,
        "category": "Customers & Products",
        "task_type": "Create customer (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Opprett kunden Vestfjord AS med organisasjonsnummer 987654321. Adressa er Fjellvegen 12, 6800 Førde. E-post: post@vestfjord.no.",
        "expected_api_calls": [
            "POST /customer {name: 'Vestfjord AS', organizationNumber: '987654321', isCustomer: true, email: 'post@vestfjord.no', postalAddress: {addressLine1: 'Fjellvegen 12', postalCode: '6800', city: 'Førde'}}"
        ],
        "scored_checks": [
            "Customer exists with name 'Vestfjord AS'",
            "organizationNumber = '987654321'",
            "isCustomer = true",
            "postalAddress correct"
        ],
        "pitfalls": [
            "'Adressa' (Nynorsk) vs 'Adressen' (Bokmål) — same meaning",
            "Not setting isCustomer: true"
        ]
    },

    {
        "id": 11,
        "category": "Customers & Products",
        "task_type": "Create supplier (Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Registrer leverandøren Dalheim AS med organisasjonsnummer 892196753. E-post: faktura@dalheim.no.",
        "expected_api_calls": [
            "POST /supplier {name: 'Dalheim AS', organizationNumber: '892196753', isSupplier: true, email: 'faktura@dalheim.no'}"
        ],
        "scored_checks": [
            "Supplier exists with name 'Dalheim AS'",
            "organizationNumber = '892196753'",
            "isSupplier = true",
            "email = 'faktura@dalheim.no'"
        ],
        "pitfalls": [
            "CRITICAL: Using POST /customer instead of POST /supplier",
            "Not setting isSupplier: true (defaults to false!)",
            "Confusing leverandør (supplier) with kunde (customer)"
        ]
    },

    {
        "id": 12,
        "category": "Customers & Products",
        "task_type": "Create supplier (Portuguese)",
        "language": "Portuguese",
        "prompt": "Registe o fornecedor Floresta Lda com número de organização 981154614. E-mail: faktura@florestalda.no.",
        "expected_api_calls": [
            "POST /supplier {name: 'Floresta Lda', organizationNumber: '981154614', isSupplier: true, email: 'faktura@florestalda.no'}"
        ],
        "scored_checks": [
            "Supplier exists with name 'Floresta Lda'",
            "isSupplier = true",
            "organizationNumber correct"
        ],
        "pitfalls": [
            "Recognizing 'fornecedor' (Portuguese) = supplier",
            "Must use POST /supplier not POST /customer"
        ]
    },

    {
        "id": 13,
        "category": "Customers & Products",
        "task_type": "Create supplier (English)",
        "language": "English",
        "prompt": "Register the supplier Northwave Ltd with organization number 949044378. Email: faktura@northwaveltd.no.",
        "expected_api_calls": [
            "POST /supplier {name: 'Northwave Ltd', organizationNumber: '949044378', isSupplier: true, email: 'faktura@northwaveltd.no'}"
        ],
        "scored_checks": [
            "Supplier exists with name 'Northwave Ltd'",
            "isSupplier = true"
        ],
        "pitfalls": [
            "CRITICAL: Must use /supplier endpoint, not /customer",
            "Not setting isSupplier: true"
        ]
    },

    {
        "id": 14,
        "category": "Customers & Products",
        "task_type": "Create supplier (French)",
        "language": "French",
        "prompt": "Enregistrez le fournisseur Beaumont SARL avec le numéro d'organisation 934567890. E-mail: contact@beaumont.fr.",
        "expected_api_calls": [
            "POST /supplier {name: 'Beaumont SARL', organizationNumber: '934567890', isSupplier: true, email: 'contact@beaumont.fr'}"
        ],
        "scored_checks": [
            "Supplier exists with name 'Beaumont SARL'",
            "isSupplier = true"
        ],
        "pitfalls": [
            "Recognizing 'fournisseur' (French) = supplier",
            "Must use /supplier not /customer"
        ]
    },

    {
        "id": 15,
        "category": "Customers & Products",
        "task_type": "Create product (Bokmål, eksklusiv MVA)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett produktet \"Konsulenttime\" med produktnummer 1001. Prisen er 1500 kr eksklusiv MVA, og standard MVA-sats på 25 % skal brukes.",
        "expected_api_calls": [
            "POST /product {name: 'Konsulenttime', number: '1001', priceExcludingVatCurrency: 1500.00, vatType: {id: 3}}"
        ],
        "scored_checks": [
            "Product exists with name 'Konsulenttime'",
            "number = '1001'",
            "priceExcludingVatCurrency = 1500.00",
            "vatType.id = 3 (25%)"
        ],
        "pitfalls": [
            "'produktnummer' = number field (string, not int)",
            "'eksklusiv MVA' means price is before VAT but VAT still applies",
            "Must set vatType: {id: 3} for 25% MVA"
        ]
    },

    {
        "id": 16,
        "category": "Customers & Products",
        "task_type": "Create product (Portuguese, sem IVA)",
        "language": "Portuguese",
        "prompt": "Crie o produto \"Design web\" com número de produto 4775. O preço é 27300 NOK sem IVA, utilizando a taxa padrão de 25 %.",
        "expected_api_calls": [
            "POST /product {name: 'Design web', number: '4775', priceExcludingVatCurrency: 27300.00, vatType: {id: 3}}"
        ],
        "scored_checks": [
            "Product exists with name 'Design web'",
            "number = '4775'",
            "priceExcludingVatCurrency = 27300.00",
            "vatType.id = 3"
        ],
        "pitfalls": [
            "TRICKY: 'sem IVA' literally means 'without VAT' but combined with 'taxa padrão de 25%' means the price is EXCLUDING VAT but VAT still applies at 25%",
            "Must NOT confuse 'sem IVA' (price without VAT included) with 'isento de IVA' (VAT-exempt)",
            "This is the Portuguese equivalent of 'eksklusiv MVA'"
        ]
    },

    {
        "id": 17,
        "category": "Customers & Products",
        "task_type": "Create product (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Opprett produktet \"Analyserapport\" med produktnummer 3637. Prisen er 31900 kr eksklusiv MVA, og standard MVA-sats på 25 % skal nyttast.",
        "expected_api_calls": [
            "POST /product {name: 'Analyserapport', number: '3637', priceExcludingVatCurrency: 31900.00, vatType: {id: 3}}"
        ],
        "scored_checks": [
            "Product exists with name 'Analyserapport'",
            "number = '3637'",
            "priceExcludingVatCurrency = 31900.00",
            "vatType.id = 3"
        ],
        "pitfalls": [
            "'skal nyttast' (Nynorsk) = 'shall be used'",
            "Same API as Bokmål"
        ]
    },

    {
        "id": 18,
        "category": "Customers & Products",
        "task_type": "Create customer (Spanish)",
        "language": "Spanish",
        "prompt": "Registre al cliente Solaris SL con número de organización 923456781. La dirección es Calle Mayor 15, 0150 Oslo. Correo: info@solaris.no.",
        "expected_api_calls": [
            "POST /customer {name: 'Solaris SL', organizationNumber: '923456781', isCustomer: true, email: 'info@solaris.no', postalAddress: {addressLine1: 'Calle Mayor 15', postalCode: '0150', city: 'Oslo'}}"
        ],
        "scored_checks": [
            "Customer exists with name 'Solaris SL'",
            "isCustomer = true",
            "postalAddress correct",
            "email correct"
        ],
        "pitfalls": [
            "Recognizing 'cliente' (Spanish) = customer",
            "'dirección' = address → postalAddress"
        ]
    },

    # =========================================================================
    # CATEGORY 3: INVOICING (12 prompts)
    # =========================================================================

    {
        "id": 19,
        "category": "Invoicing",
        "task_type": "Create and send invoice (Bokmål, eksklusiv MVA)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett og send en faktura til kunden Nordhav AS (org.nr 876520427) på 7850 kr eksklusiv MVA. Fakturaen gjelder Analyserapport.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "PUT /ledger/vatSettings (if not registered)",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "PUT /ledger/account/{id} (if bank number empty)",
            "POST /customer {name: 'Nordhav AS', organizationNumber: '876520427', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {invoiceDate: 'today', invoiceDueDate: 'today', orders: [{customer: {id: CUST_ID}, orderDate: 'today', deliveryDate: 'today', isPrioritizeAmountsIncludingVat: false, orderLines: [{description: 'Analyserapport', count: 1, unitPriceExcludingVatCurrency: 7850, vatType: {id: 3}}]}]}"
        ],
        "scored_checks": [
            "Invoice exists for customer 'Nordhav AS'",
            "Invoice line description = 'Analyserapport'",
            "Amount excluding VAT = 7850",
            "VAT type = 25% (vatType 3)",
            "Invoice has been sent"
        ],
        "pitfalls": [
            "Not registering for VAT first (vatSettings)",
            "Not setting up bank account 1920",
            "'eksklusiv MVA' → isPrioritizeAmountsIncludingVat: false + unitPriceExcludingVatCurrency",
            "Not setting isCustomer: true on customer creation"
        ]
    },

    {
        "id": 20,
        "category": "Invoicing",
        "task_type": "Create and send invoice (inklusiv MVA)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett og send en faktura til kunden Storfjell AS (org.nr 934567890) på 12500 kr inklusiv MVA. Fakturaen gjelder Prosjektledelse.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "PUT /ledger/account/{id} (if needed)",
            "POST /customer {name: 'Storfjell AS', organizationNumber: '934567890', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {invoiceDate: 'today', invoiceDueDate: 'today', orders: [{customer: {id: CUST_ID}, orderDate: 'today', deliveryDate: 'today', isPrioritizeAmountsIncludingVat: true, orderLines: [{description: 'Prosjektledelse', count: 1, unitPriceIncludingVatCurrency: 12500, vatType: {id: 3}}]}]}"
        ],
        "scored_checks": [
            "Invoice exists for customer 'Storfjell AS'",
            "Amount including VAT = 12500",
            "isPrioritizeAmountsIncludingVat = true",
            "vatType = 25%"
        ],
        "pitfalls": [
            "CRITICAL: 'inklusiv MVA' means total INCLUDING VAT",
            "Must use unitPriceIncludingVatCurrency (not Excluding)",
            "Must set isPrioritizeAmountsIncludingVat: true",
            "Still needs vatType: {id: 3} — VAT is included in the price, not absent"
        ]
    },

    {
        "id": 21,
        "category": "Invoicing",
        "task_type": "Create invoice (uten MVA / VAT-exempt)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett og send en faktura til kunden Nordlys AS (org.nr 945678901) på 5000 kr uten MVA. Fakturaen gjelder Frivillig arbeid.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "POST /customer {name: 'Nordlys AS', organizationNumber: '945678901', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {invoiceDate: 'today', invoiceDueDate: 'today', orders: [{customer: {id: CUST_ID}, orderDate: 'today', deliveryDate: 'today', orderLines: [{description: 'Frivillig arbeid', count: 1, unitPriceExcludingVatCurrency: 5000}]}]}"
        ],
        "scored_checks": [
            "Invoice exists for customer 'Nordlys AS'",
            "Amount = 5000",
            "No VAT applied (vatType omitted or VAT-exempt type)"
        ],
        "pitfalls": [
            "'uten MVA' = NO VAT AT ALL → omit vatType entirely",
            "Different from 'eksklusiv MVA' which STILL HAS VAT",
            "May or may not need VAT registration depending on sandbox state"
        ]
    },

    {
        "id": 22,
        "category": "Invoicing",
        "task_type": "Create and send invoice (German, ohne MwSt)",
        "language": "German",
        "prompt": "Erstellen und senden Sie eine Rechnung an den Kunden Grünfeld GmbH (Org.-Nr. 974406322) über 6650 NOK ohne MwSt. Die Rechnung betrifft Beratungsstunden.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "PUT /ledger/account/{id} (if needed)",
            "POST /customer {name: 'Grünfeld GmbH', organizationNumber: '974406322', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., isPrioritizeAmountsIncludingVat: false, orderLines: [{description: 'Beratungsstunden', count: 1, unitPriceExcludingVatCurrency: 6650, vatType: {id: 3}}]}"
        ],
        "scored_checks": [
            "Invoice exists for 'Grünfeld GmbH'",
            "Amount excluding VAT = 6650",
            "Description = 'Beratungsstunden'",
            "vatType = 25%"
        ],
        "pitfalls": [
            "TRICKY: 'ohne MwSt' in German COULD mean VAT-exempt OR price-excluding-VAT",
            "In competition context, 'ohne MwSt' typically means 'price is stated without VAT included' (= eksklusiv MVA), NOT VAT-exempt",
            "Must apply 25% VAT unless explicitly told 'MwSt-frei' or 'steuerfrei'"
        ]
    },

    {
        "id": 23,
        "category": "Invoicing",
        "task_type": "Create and send invoice (Portuguese, sem IVA)",
        "language": "Portuguese",
        "prompt": "Crie e envie uma fatura ao cliente Porto Alegre Lda (org. nº 826870192) por 22700 NOK sem IVA. A fatura refere-se a Design web.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "POST /customer {name: 'Porto Alegre Lda', organizationNumber: '826870192', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., isPrioritizeAmountsIncludingVat: false, orderLines: [{description: 'Design web', count: 1, unitPriceExcludingVatCurrency: 22700, vatType: {id: 3}}]}"
        ],
        "scored_checks": [
            "Invoice exists for 'Porto Alegre Lda'",
            "Amount excluding VAT = 22700",
            "vatType = 25%"
        ],
        "pitfalls": [
            "'sem IVA' = without VAT in price (NOT VAT-exempt) → use eksklusiv MVA pattern",
            "Must still apply vatType: {id: 3}"
        ]
    },

    {
        "id": 24,
        "category": "Invoicing",
        "task_type": "Create and send invoice (French, HT)",
        "language": "French",
        "prompt": "Créez et envoyez une facture au client Château Blanc SARL (org. nº 918765432) de 15400 NOK HT. La facture concerne Développement logiciel.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "POST /customer {name: 'Château Blanc SARL', organizationNumber: '918765432', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., isPrioritizeAmountsIncludingVat: false, orderLines: [{description: 'Développement logiciel', count: 1, unitPriceExcludingVatCurrency: 15400, vatType: {id: 3}}]}"
        ],
        "scored_checks": [
            "Invoice for 'Château Blanc SARL'",
            "Amount HT (excluding VAT) = 15400",
            "vatType = 25%"
        ],
        "pitfalls": [
            "'HT' (Hors Taxes) = excluding tax = eksklusiv MVA",
            "'TTC' (Toutes Taxes Comprises) would mean inklusiv MVA",
            "Must still apply VAT type 3"
        ]
    },

    {
        "id": 25,
        "category": "Invoicing",
        "task_type": "Register payment on invoice (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Kunden Elvdal AS (org.nr 963143230) har ein uteståande faktura på 19600 kr eksklusiv MVA for \"Datarådgjeving\". Registrer full betaling på denne fakturaen.",
        "expected_api_calls": [
            "GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920&fields=id,version,bankAccountNumber",
            "PUT /ledger/account/{id} (if needed)",
            "POST /customer {name: 'Elvdal AS', organizationNumber: '963143230', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., orderLines: [{description: 'Datarådgjeving', unitPriceExcludingVatCurrency: 19600, vatType: {id: 3}}]}",
            "GET /invoice/paymentType?fields=id,description",
            "PUT /invoice/{id}/:payment?paymentDate=today&paymentTypeId=PT_ID&paidAmount=24500"
        ],
        "scored_checks": [
            "Invoice exists for 'Elvdal AS'",
            "Invoice is marked as paid",
            "Payment amount = 24500 (19600 * 1.25 with 25% VAT)",
            "Payment type = incoming bank payment"
        ],
        "pitfalls": [
            "CRITICAL: paidAmount must be total INCLUDING VAT: 19600 * 1.25 = 24500",
            "'uteståande' (Nynorsk) = 'utestående' (Bokmål) = outstanding",
            "Must create invoice first, then register payment",
            "Must use /invoice/paymentType (incoming), NOT /ledger/paymentTypeOut (outgoing)",
            "Full payment = the entire invoice amount"
        ]
    },

    {
        "id": 26,
        "category": "Invoicing",
        "task_type": "Register payment (English)",
        "language": "English",
        "prompt": "The customer Oakridge Corp (org no. 951234567) has an outstanding invoice for 35000 NOK excluding VAT for \"IT Consulting\". Register full payment on this invoice.",
        "expected_api_calls": [
            "GET /ledger/vatSettings",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920",
            "POST /customer {name: 'Oakridge Corp', organizationNumber: '951234567', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., unitPriceExcludingVatCurrency: 35000, vatType: {id: 3}}",
            "GET /invoice/paymentType?fields=id,description",
            "PUT /invoice/{id}/:payment?paymentDate=today&paymentTypeId=PT_ID&paidAmount=43750"
        ],
        "scored_checks": [
            "Invoice exists, is paid",
            "Payment amount = 43750 (35000 * 1.25)",
            "Customer 'Oakridge Corp' exists"
        ],
        "pitfalls": [
            "paidAmount = 35000 * 1.25 = 43750 (must include VAT)",
            "Must create the invoice first before registering payment"
        ]
    },

    {
        "id": 27,
        "category": "Invoicing",
        "task_type": "Credit note on invoice (Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett en kreditnota på den siste fakturaen til kunden Havbris AS (org.nr 946293199).",
        "expected_api_calls": [
            "GET /invoice?customerName=Havbris&fields=id,invoiceNumber&count=1&sorting=-invoiceNumber",
            "PUT /invoice/{id}/:createCreditNote?date=today"
        ],
        "scored_checks": [
            "Credit note exists linked to the original invoice",
            "Credit note date is today"
        ],
        "pitfalls": [
            "Must find existing invoice first (not create new one)",
            "Use PUT /:createCreditNote, not POST",
            "If no invoice exists for this customer, may need to create one first"
        ]
    },

    {
        "id": 28,
        "category": "Invoicing",
        "task_type": "Credit note (Spanish)",
        "language": "Spanish",
        "prompt": "Emita una nota de crédito sobre la última factura del cliente Montaña SL (org. nº 967891234).",
        "expected_api_calls": [
            "GET /invoice?customerName=Montaña&fields=id,invoiceNumber&count=1&sorting=-invoiceNumber",
            "PUT /invoice/{id}/:createCreditNote?date=today"
        ],
        "scored_checks": [
            "Credit note exists for the invoice",
            "Correct invoice targeted"
        ],
        "pitfalls": [
            "'nota de crédito' (Spanish) = credit note",
            "'factura' = invoice",
            "Need to search for existing invoice"
        ]
    },

    {
        "id": 29,
        "category": "Invoicing",
        "task_type": "Invoice with inklusiv MVA (French TTC)",
        "language": "French",
        "prompt": "Créez et envoyez une facture au client Rivière SA (org. nº 923478901) de 18750 NOK TTC. La facture concerne Formation professionnelle.",
        "expected_api_calls": [
            "GET /ledger/vatSettings",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920",
            "POST /customer {name: 'Rivière SA', organizationNumber: '923478901', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., isPrioritizeAmountsIncludingVat: true, orderLines: [{description: 'Formation professionnelle', unitPriceIncludingVatCurrency: 18750, vatType: {id: 3}}]}"
        ],
        "scored_checks": [
            "Invoice total including VAT = 18750",
            "isPrioritizeAmountsIncludingVat = true"
        ],
        "pitfalls": [
            "'TTC' (Toutes Taxes Comprises) = inklusiv MVA = INCLUDING VAT",
            "Must use unitPriceIncludingVatCurrency, not Excluding",
            "Still needs vatType: {id: 3}"
        ]
    },

    {
        "id": 30,
        "category": "Invoicing",
        "task_type": "Invoice with Spanish sin IVA",
        "language": "Spanish",
        "prompt": "Cree y envíe una factura al cliente Sierra Alta SL (org. nº 941234567) por 9200 NOK sin IVA. La factura es por Servicios de consultoría.",
        "expected_api_calls": [
            "GET /ledger/vatSettings",
            "PUT /ledger/vatSettings (if needed)",
            "GET /ledger/account?number=1920",
            "POST /customer {name: 'Sierra Alta SL', organizationNumber: '941234567', isCustomer: true}",
            "POST /invoice?sendToCustomer=true {..., isPrioritizeAmountsIncludingVat: false, orderLines: [{description: 'Servicios de consultoría', unitPriceExcludingVatCurrency: 9200, vatType: {id: 3}}]}"
        ],
        "scored_checks": [
            "Invoice for 'Sierra Alta SL'",
            "Amount excluding VAT = 9200",
            "25% VAT applied"
        ],
        "pitfalls": [
            "'sin IVA' = without VAT in price (eksklusiv MVA), NOT VAT-exempt",
            "'exento de IVA' would mean truly VAT-exempt",
            "Must still apply vatType 3"
        ]
    },

    # =========================================================================
    # CATEGORY 4: TRAVEL EXPENSES (5 prompts)
    # =========================================================================

    {
        "id": 31,
        "category": "Travel Expenses",
        "task_type": "Create travel expense (Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Registrer en reiseregning for den ansatte med tittel \"Kundemøte i Bergen\".",
        "expected_api_calls": [
            "GET /token/session/>whoAmI?fields=employeeId",
            "POST /travelExpense {employee: {id: EMP_ID}, title: 'Kundemøte i Bergen'}"
        ],
        "scored_checks": [
            "Travel expense exists with title 'Kundemøte i Bergen'",
            "Linked to correct employee"
        ],
        "pitfalls": [
            "Need to identify which employee — use whoAmI or search",
            "'reiseregning' = travel expense"
        ]
    },

    {
        "id": 32,
        "category": "Travel Expenses",
        "task_type": "Create travel expense (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Registrer ei reiserekning for den tilsette med tittel \"Seminar i Stavanger\".",
        "expected_api_calls": [
            "GET /token/session/>whoAmI?fields=employeeId",
            "POST /travelExpense {employee: {id: EMP_ID}, title: 'Seminar i Stavanger'}"
        ],
        "scored_checks": [
            "Travel expense exists with title 'Seminar i Stavanger'"
        ],
        "pitfalls": [
            "'reiserekning' (Nynorsk) = 'reiseregning' (Bokmål) = travel expense",
            "'tilsette' = 'ansatte' = employee"
        ]
    },

    {
        "id": 33,
        "category": "Travel Expenses",
        "task_type": "Delete travel expense (English)",
        "language": "English",
        "prompt": "Delete the travel expense report titled \"Conference Oslo\".",
        "expected_api_calls": [
            "GET /travelExpense?fields=id,title",
            "DELETE /travelExpense/{id}"
        ],
        "scored_checks": [
            "Travel expense 'Conference Oslo' no longer exists (204 on delete)"
        ],
        "pitfalls": [
            "Must search for the travel expense by title first",
            "DELETE returns 204 No Content on success, not 200",
            "If multiple travel expenses match, delete the correct one"
        ]
    },

    {
        "id": 34,
        "category": "Travel Expenses",
        "task_type": "Create travel expense (German)",
        "language": "German",
        "prompt": "Registrieren Sie eine Reisekostenabrechnung für den aktuellen Mitarbeiter mit dem Titel \"Kundentermin München\".",
        "expected_api_calls": [
            "GET /token/session/>whoAmI?fields=employeeId",
            "POST /travelExpense {employee: {id: EMP_ID}, title: 'Kundentermin München'}"
        ],
        "scored_checks": [
            "Travel expense exists with title 'Kundentermin München'"
        ],
        "pitfalls": [
            "'Reisekostenabrechnung' (German) = travel expense report",
            "'aktuellen Mitarbeiter' = current employee → use whoAmI"
        ]
    },

    {
        "id": 35,
        "category": "Travel Expenses",
        "task_type": "Delete travel expense (Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Slett reiseregningen med tittel \"Prosjektbesøk Tromsø\".",
        "expected_api_calls": [
            "GET /travelExpense?fields=id,title",
            "DELETE /travelExpense/{id}"
        ],
        "scored_checks": [
            "Travel expense no longer exists"
        ],
        "pitfalls": [
            "'Slett' = Delete",
            "Must search and find the correct travel expense",
            "Ensure exact title match"
        ]
    },

    # =========================================================================
    # CATEGORY 5: PROJECTS (6 prompts)
    # =========================================================================

    {
        "id": 36,
        "category": "Projects",
        "task_type": "Create project with new PM (English)",
        "language": "English",
        "prompt": "Create the project \"Upgrade Silveroak\" linked to the customer Silveroak Ltd (org no. 937657250). The project manager is Alice Smith (alice.smith@example.org).",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /customer {name: 'Silveroak Ltd', organizationNumber: '937657250', isCustomer: true}",
            "POST /employee {firstName: 'Alice', lastName: 'Smith', email: 'alice.smith@example.org', dateOfBirth: '1990-01-01', userType: 'EXTENDED', allowInformationRegistration: true, department: {id: DEPT_ID}}",
            "POST /employee/entitlement {employee: {id: EMP_ID}, entitlementId: 45, customer: {id: COMPANY_ID}}",
            "POST /employee/entitlement {employee: {id: EMP_ID}, entitlementId: 10, customer: {id: COMPANY_ID}}",
            "POST /project {name: 'Upgrade Silveroak', projectManager: {id: EMP_ID}, customer: {id: CUST_ID}, startDate: 'today'}"
        ],
        "scored_checks": [
            "Project 'Upgrade Silveroak' exists",
            "Linked to customer 'Silveroak Ltd'",
            "Project manager is 'Alice Smith'",
            "Customer has isCustomer=true",
            "Employee has PM entitlements (45, 10)"
        ],
        "pitfalls": [
            "Must create employee BEFORE project (PM is required)",
            "PM needs EXTENDED userType + entitlements 45 and 10",
            "Must set dateOfBirth on employee even if not given (use reasonable default)",
            "entitlement 'customer' field = company ID, not the customer entity",
            "Project requires startDate"
        ]
    },

    {
        "id": 37,
        "category": "Projects",
        "task_type": "Create project (German)",
        "language": "German",
        "prompt": "Erstellen Sie das Projekt \"Migration Eichenhof\" verknüpft mit dem Kunden Eichenhof GmbH (Org.-Nr. 953914123). Projektleiter ist Hannah Weber (hannah.weber@example.org).",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /customer {name: 'Eichenhof GmbH', organizationNumber: '953914123', isCustomer: true}",
            "POST /employee {firstName: 'Hannah', lastName: 'Weber', email: 'hannah.weber@example.org', ...}",
            "POST /employee/entitlement {entitlementId: 45, ...}",
            "POST /employee/entitlement {entitlementId: 10, ...}",
            "POST /project {name: 'Migration Eichenhof', projectManager: {id: EMP_ID}, customer: {id: CUST_ID}, startDate: 'today'}"
        ],
        "scored_checks": [
            "Project 'Migration Eichenhof' exists",
            "Linked to 'Eichenhof GmbH'",
            "PM is 'Hannah Weber'"
        ],
        "pitfalls": [
            "'Projektleiter' (German) = project manager",
            "'Kunden' = customer (not supplier)",
            "Same complex sequence as English variant"
        ]
    },

    {
        "id": 38,
        "category": "Projects",
        "task_type": "Create project (Norwegian Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett prosjektet \"Implementering Havglimt\" knyttet til kunden Havglimt AS (org.nr 962345678). Prosjektleder er Jonas Berg (jonas.berg@example.no).",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /customer {name: 'Havglimt AS', organizationNumber: '962345678', isCustomer: true}",
            "POST /employee {firstName: 'Jonas', lastName: 'Berg', email: 'jonas.berg@example.no', ...}",
            "POST /employee/entitlement {entitlementId: 45, ...}",
            "POST /employee/entitlement {entitlementId: 10, ...}",
            "POST /project {name: 'Implementering Havglimt', projectManager: {id: EMP_ID}, customer: {id: CUST_ID}, startDate: 'today'}"
        ],
        "scored_checks": [
            "Project 'Implementering Havglimt' exists",
            "Customer linked",
            "PM = 'Jonas Berg'"
        ],
        "pitfalls": [
            "'prosjektleder' = project manager",
            "Must create employee, assign entitlements, then create project"
        ]
    },

    {
        "id": 39,
        "category": "Projects",
        "task_type": "Create project (French)",
        "language": "French",
        "prompt": "Créez le projet \"Refonte Beaumont\" lié au client Beaumont SARL (org. nº 934567890). Le chef de projet est Marie Laurent (marie.laurent@example.org).",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /customer {name: 'Beaumont SARL', organizationNumber: '934567890', isCustomer: true}",
            "POST /employee {firstName: 'Marie', lastName: 'Laurent', email: 'marie.laurent@example.org', ...}",
            "POST /employee/entitlement {entitlementId: 45, ...}",
            "POST /employee/entitlement {entitlementId: 10, ...}",
            "POST /project {name: 'Refonte Beaumont', projectManager: {id: EMP_ID}, customer: {id: CUST_ID}, startDate: 'today'}"
        ],
        "scored_checks": [
            "Project 'Refonte Beaumont' exists",
            "Client 'Beaumont SARL' linked",
            "PM = 'Marie Laurent'"
        ],
        "pitfalls": [
            "'chef de projet' (French) = project manager",
            "'client' (French) = customer, NOT supplier"
        ]
    },

    {
        "id": 40,
        "category": "Projects",
        "task_type": "Create project (Portuguese)",
        "language": "Portuguese",
        "prompt": "Crie o projeto \"Expansão Floresta\" ligado ao cliente Floresta Lda (org. nº 971234567). O gestor de projeto é João Silva (joao.silva@example.org).",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /customer {name: 'Floresta Lda', organizationNumber: '971234567', isCustomer: true}",
            "POST /employee {firstName: 'João', lastName: 'Silva', email: 'joao.silva@example.org', ...}",
            "POST /employee/entitlement {entitlementId: 45, ...}",
            "POST /employee/entitlement {entitlementId: 10, ...}",
            "POST /project {name: 'Expansão Floresta', projectManager: {id: EMP_ID}, customer: {id: CUST_ID}, startDate: 'today'}"
        ],
        "scored_checks": [
            "Project 'Expansão Floresta' exists",
            "Customer linked",
            "PM = 'João Silva'"
        ],
        "pitfalls": [
            "'gestor de projeto' (Portuguese) = project manager",
            "Special characters in name: 'João', 'Expansão'"
        ]
    },

    {
        "id": 41,
        "category": "Projects",
        "task_type": "Create project (Spanish)",
        "language": "Spanish",
        "prompt": "Cree el proyecto \"Transformación Digital\" vinculado al cliente Montaña SL (org. nº 956789012). El jefe de proyecto es Pablo García (pablo.garcia@example.org).",
        "expected_api_calls": [
            "GET /department?fields=id,name",
            "GET /token/session/>whoAmI?fields=companyId,employeeId",
            "POST /customer {name: 'Montaña SL', organizationNumber: '956789012', isCustomer: true}",
            "POST /employee {firstName: 'Pablo', lastName: 'García', email: 'pablo.garcia@example.org', ...}",
            "POST /employee/entitlement {entitlementId: 45, ...}",
            "POST /employee/entitlement {entitlementId: 10, ...}",
            "POST /project {name: 'Transformación Digital', projectManager: {id: EMP_ID}, customer: {id: CUST_ID}, startDate: 'today'}"
        ],
        "scored_checks": [
            "Project 'Transformación Digital' exists",
            "Customer 'Montaña SL' linked",
            "PM = 'Pablo García'"
        ],
        "pitfalls": [
            "'jefe de proyecto' (Spanish) = project manager",
            "'vinculado al cliente' = linked to customer"
        ]
    },

    # =========================================================================
    # CATEGORY 6: CORRECTIONS (5 prompts)
    # =========================================================================

    {
        "id": 42,
        "category": "Corrections",
        "task_type": "Credit note on existing invoice (English)",
        "language": "English",
        "prompt": "Issue a credit note on the most recent invoice in the system.",
        "expected_api_calls": [
            "GET /invoice?count=1&sorting=-invoiceNumber&fields=id,invoiceNumber",
            "PUT /invoice/{id}/:createCreditNote?date=today"
        ],
        "scored_checks": [
            "Credit note created",
            "Linked to correct invoice"
        ],
        "pitfalls": [
            "Must find the most recent invoice first",
            "If no invoices exist, may need to inform that or create one first",
            "Use sorting=-invoiceNumber to get the latest"
        ]
    },

    {
        "id": 43,
        "category": "Corrections",
        "task_type": "Reverse voucher (Norwegian Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Reverser det siste bilaget i systemet.",
        "expected_api_calls": [
            "GET /ledger/voucher?count=1&sorting=-number&fields=id,number",
            "PUT /ledger/voucher/{id}/:reverse"
        ],
        "scored_checks": [
            "Voucher has been reversed",
            "Reversal voucher created"
        ],
        "pitfalls": [
            "'bilag' = voucher",
            "'reverser' = reverse",
            "Use /:reverse endpoint, not DELETE",
            "Must find the latest voucher first"
        ]
    },

    {
        "id": 44,
        "category": "Corrections",
        "task_type": "Delete incorrect entry (English)",
        "language": "English",
        "prompt": "Delete the travel expense report titled \"Wrong Entry\" that was created by mistake.",
        "expected_api_calls": [
            "GET /travelExpense?fields=id,title",
            "DELETE /travelExpense/{id}"
        ],
        "scored_checks": [
            "Travel expense 'Wrong Entry' no longer exists"
        ],
        "pitfalls": [
            "Must search for the specific travel expense",
            "DELETE returns 204, not 200",
            "For invoices, use credit note instead of delete"
        ]
    },

    {
        "id": 45,
        "category": "Corrections",
        "task_type": "Credit note (German, Gutschrift)",
        "language": "German",
        "prompt": "Erstellen Sie eine Gutschrift für die letzte Rechnung im System.",
        "expected_api_calls": [
            "GET /invoice?count=1&sorting=-invoiceNumber&fields=id,invoiceNumber",
            "PUT /invoice/{id}/:createCreditNote?date=today"
        ],
        "scored_checks": [
            "Gutschrift (credit note) created"
        ],
        "pitfalls": [
            "'Gutschrift' (German) = credit note",
            "'Rechnung' = invoice"
        ]
    },

    {
        "id": 46,
        "category": "Corrections",
        "task_type": "Reverse voucher (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Reverser det siste bilaget som er registrert.",
        "expected_api_calls": [
            "GET /ledger/voucher?count=1&sorting=-number&fields=id,number",
            "PUT /ledger/voucher/{id}/:reverse"
        ],
        "scored_checks": [
            "Voucher reversed successfully"
        ],
        "pitfalls": [
            "'bilag' same in Nynorsk and Bokmål",
            "'registrert' = registered"
        ]
    },

    # =========================================================================
    # CATEGORY 7: DEPARTMENTS (4 prompts)
    # =========================================================================

    {
        "id": 47,
        "category": "Departments",
        "task_type": "Create three departments (Norwegian Bokmål)",
        "language": "Norwegian Bokmål",
        "prompt": "Opprett tre avdelinger i Tripletex: \"Økonomi\", \"Markedsføring\" og \"Kvalitetskontroll\".",
        "expected_api_calls": [
            "GET /department?fields=id,departmentNumber&count=100",
            "POST /department {name: 'Økonomi', departmentNumber: NEXT_NUM}",
            "POST /department {name: 'Markedsføring', departmentNumber: NEXT_NUM+1}",
            "POST /department {name: 'Kvalitetskontroll', departmentNumber: NEXT_NUM+2}"
        ],
        "scored_checks": [
            "Department 'Økonomi' exists",
            "Department 'Markedsføring' exists",
            "Department 'Kvalitetskontroll' exists",
            "Each has unique departmentNumber"
        ],
        "pitfalls": [
            "Must assign UNIQUE departmentNumbers (can't reuse existing ones)",
            "Need to check existing departments first to find available numbers",
            "All three must be created — partial success is partial score"
        ]
    },

    {
        "id": 48,
        "category": "Departments",
        "task_type": "Create three departments (German)",
        "language": "German",
        "prompt": "Erstellen Sie drei Abteilungen in Tripletex: \"Økonomi\", \"Regnskap\" und \"Kvalitetskontroll\".",
        "expected_api_calls": [
            "GET /department?fields=id,departmentNumber&count=100",
            "POST /department {name: 'Økonomi', departmentNumber: NEXT_NUM}",
            "POST /department {name: 'Regnskap', departmentNumber: NEXT_NUM+1}",
            "POST /department {name: 'Kvalitetskontroll', departmentNumber: NEXT_NUM+2}"
        ],
        "scored_checks": [
            "Department 'Økonomi' exists",
            "Department 'Regnskap' exists",
            "Department 'Kvalitetskontroll' exists"
        ],
        "pitfalls": [
            "Prompt is in German but department NAMES are in Norwegian — must use exact names as given",
            "'Abteilungen' (German) = departments",
            "Unique departmentNumber required for each"
        ]
    },

    {
        "id": 49,
        "category": "Departments",
        "task_type": "Create three departments (Nynorsk)",
        "language": "Norwegian Nynorsk",
        "prompt": "Opprett tre avdelingar i Tripletex: \"Økonomi\", \"Administrasjon\" og \"Innkjøp\".",
        "expected_api_calls": [
            "GET /department?fields=id,departmentNumber&count=100",
            "POST /department {name: 'Økonomi', departmentNumber: NEXT_NUM}",
            "POST /department {name: 'Administrasjon', departmentNumber: NEXT_NUM+1}",
            "POST /department {name: 'Innkjøp', departmentNumber: NEXT_NUM+2}"
        ],
        "scored_checks": [
            "Department 'Økonomi' exists",
            "Department 'Administrasjon' exists",
            "Department 'Innkjøp' exists"
        ],
        "pitfalls": [
            "'avdelingar' (Nynorsk) vs 'avdelinger' (Bokmål) = departments",
            "Must use exact department names as specified"
        ]
    },

    {
        "id": 50,
        "category": "Departments",
        "task_type": "Create department + enable module (English)",
        "language": "English",
        "prompt": "Create a department called \"Engineering\" and enable the Smart Project module.",
        "expected_api_calls": [
            "GET /department?fields=id,departmentNumber&count=100",
            "POST /department {name: 'Engineering', departmentNumber: NEXT_NUM}",
            "POST /company/salesmodules {name: 'SMART_PROJECT'}"
        ],
        "scored_checks": [
            "Department 'Engineering' exists",
            "SMART_PROJECT module is enabled"
        ],
        "pitfalls": [
            "Module name must be the exact enum: 'SMART_PROJECT' (not 'Smart Project')",
            "Department requires unique departmentNumber",
            "These are two independent operations — department + module"
        ]
    },
]


# =========================================================================
# Summary statistics
# =========================================================================

def print_summary():
    """Print a summary of test prompt coverage."""
    from collections import Counter

    categories = Counter(p["category"] for p in TEST_PROMPTS)
    languages = Counter(p["language"] for p in TEST_PROMPTS)
    task_types = Counter(p["task_type"] for p in TEST_PROMPTS)

    print(f"Total test prompts: {len(TEST_PROMPTS)}")
    print(f"\n--- By Category ---")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")

    print(f"\n--- By Language ---")
    for lang, count in languages.most_common():
        print(f"  {lang}: {count}")

    print(f"\n--- Unique Task Types: {len(task_types)} ---")
    for tt, count in task_types.most_common():
        print(f"  {tt}: {count}")

    # Edge cases covered
    print(f"\n--- Critical Edge Cases Covered ---")
    edge_cases = [
        "eksklusiv MVA (prompts 15, 17, 19, 25)",
        "inklusiv MVA (prompt 20)",
        "uten MVA (prompt 21)",
        "ohne MwSt (prompt 22)",
        "sem IVA (prompts 16, 23)",
        "HT (French, prompt 24)",
        "TTC (French, prompt 29)",
        "sin IVA (Spanish, prompt 30)",
        "Supplier vs Customer distinction (prompts 11-14 vs 9-10, 18)",
        "Multiple entities at once - 3 departments (prompts 47-49)",
        "Admin role (prompt 3)",
        "Project manager role (prompt 6)",
        "Start date on employee (prompts 1, 2, 4, 5, 7)",
        "Address on customer (prompts 9, 10, 18)",
        "Payment registration (prompts 25, 26)",
        "Credit notes (prompts 27, 28, 42, 45)",
        "Voucher reversal (prompts 43, 46)",
        "Travel expense delete (prompts 33, 35, 44)",
        "Nynorsk variations (prompts 2, 10, 17, 32, 46, 49)",
        "Department + module enable (prompt 50)",
    ]
    for ec in edge_cases:
        print(f"  - {ec}")


if __name__ == "__main__":
    print_summary()
