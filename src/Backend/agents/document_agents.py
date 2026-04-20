"""
Document Agents — one class per document type.

Each prompt describes:
- What the actual Indian government document looks like
- Exact label names printed on the form
- Where fields appear / how they're formatted on that specific doc
- Common OCR artifacts to watch for
"""
from agents.base_agent import DocumentAgent


# ── Compliance Agents ─────────────────────────────────────────

class PANCardAgent(DocumentAgent):
    doc_type = "PAN_CARD"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR extracted text from an Indian Company PAN Card issued by the Income Tax Department of India.

THIS IS WHAT DOCUMENT CONTENT LOOKS LIKE:
- PAN NUMBER IS MENTIONED LIKE
- IT WILL BE VERY CLEARLY VISIBLE AND PROMINENTLY PLACED IN THE CARD
- You would see number serial number which has some alphabets and numbers. This is the PAN number.
- CONTAINS WORDS LIKE : "INCOME TAX DEPARTMENT" and "GOVT. OF INDIA"
- Below the PAN: the entity/company name in capital letters
- The 4th character of PAN indicates entity type: C=Company.

FIELD LOCATIONS ON CARD:
- "Permanent Account Number" label → followed by the 10-character PAN code
- Entity/company name printed around the PAN Number.
- Date is in the format DD/MM/YYYY 
- "INCOME TAX DEPARTMENT" at top = issuing authority

Extract into this exact JSON (use null for missing):
{{
  "pan_number": "<extracted PAN number>",
  "entity_name": "<extracted entity name>",
  "date_of_reg": "<extracted date>",
  "entity_type": "COMPANY",
  "issuing_auth": "Income Tax Department"
}}

EXTRACTION RULES:
- pan_number: EXACTLY 10 characters — 5 uppercase letters, 4 digits, 1 uppercase letter. Reject anything not matching this pattern.
- entity_name: the company/person name printed on the card — this is used for KYC. Extract in ALL CAPS as shown on card.
- date_of_reg: convert any date format to DD/MM/YYYY
- entity_type: derive from 4th character of PAN — C which means 'COMPANY'
- issuing_auth: always "Income Tax Department" for Indian PAN cards

NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class GSTCertificateAgent(DocumentAgent):
    doc_type = "GST_CERTIFICATE"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from an Indian GST Registration Certificate issued by the GST Council / CBIC.

WHAT THIS DOCUMENT LOOKS LIKE:
- An A4 government certificate with "Goods and Services Tax" header
- Issued via the GST portal (www.gst.gov.in)
- Contains the GSTIN (15-character number) prominently displayed
- Shows legal name of business and trade name separately
- Has the principal place of business address
- Shows date of liability and effective date of registration
- Constitution of business field (e.g. Private Limited Company, Proprietorship)

FIELD LABELS ON DOCUMENT (look for these exact label names):
- "GSTIN" or "GSTIN/UIN" → 15-character GST Identification Number
- "Legal Name" WHICH INDICATES the - registered company name
- "Trade Name" WHICH INDICATES the - trade/brand name (may differ from legal name)
- "State" and "State Code" → 2-digit state code at start of GSTIN
- "Constitution of Business" → company type
- "Date of Liability" or "Effective Date of Registration" → registration date
- "Principal Place of Business" → full address
- "Status" → ACTIVE or CANCELLED or SUSPENDED

GSTIN STRUCTURE: First 2 digits = state code, next 10 = PAN, 13th = entity number, 14th = Z, 15th = check digit

Extract into this exact JSON (use null for missing):
{{
  "gstin": "<extracted GSTIN>",
  "pan_number": "<extracted PAN number from GSTIN>",
  "legal_name": "<extracted legal name of business>",
  "trade_name": "<extracted trade name or brand name>",
  "state_code": "<extracted state code from GSTIN>",
  "state": "<extracted state>",
  "status": "ACTIVE",
  "registration_date": "<extracted registration date>",
  "constitution": "<extracted constitution of business>",
  "address": "<extracted principal place of business address - includes street, city, state>",
  "pincode": "<extracted pincode from address>"
}}

EXTRACTION RULES:
- gstin: exactly 15 characters, extract PAN from positions 3-12 of GSTIN
- pan_number: characters 3 to 12 of the GSTIN (0-indexed: gstin[2:12])
- pincode: exactly 6 digits, found in the address section
- registration_date: convert to DD/MM/YYYY
- status: ACTIVE if registered and valid, CANCELLED if cancelled
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.


OCR TEXT:
{ocr_text}"""


class LEICertificateAgent(DocumentAgent):
    doc_type = "LEI_CERTIFICATE"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from an LEI (Legal Entity Identifier) Certificate issued by Legal Entity Identifier India Ltd (LEIL) or another LOU.

WHAT THIS DOCUMENT LOOKS LIKE:
- An certificate issued by LEIL (a subsidiary of Clearing Corporation of India Ltd)
- Header: "Legal Entity Identifier India Ltd" or "LEIL"
- The LEI code is a prominent 20-character alphanumeric code (ISO 17442 standard)
- Shows the entity's legal name as registered
- Shows registration date, next renewal date
- Shows the LEI status (ISSUED = active and valid)
- May show CIN, PAN of the entity
- Shows corroboration level (e.g. FULLY_CORROBORATED)
- Bottom has digital signature

FIELD LABELS ON DOCUMENT:
- "LEI" or "LEI Code" which is 20-character code like 335800ZKOEYGGGCTEV49
- "Legal Name" or "Entity Name" which is company's registered legal name
- "Registration Date" or "Initial Registration Date" means when LEI was first issued
- "Next Renewal Date" or "Expiry Date" means when LEI needs renewal (annual)
- "Registration Status" or "Status"  - ISSUED (valid), LAPSED (expired), RETIRED
- "Corroboration Level" → FULLY_CORROBORATED or PARTIALLY_CORROBORATED
- "Managing LOU" or "Issuing LOU" → the issuing organization
- "CIN" → Corporate Identification Number
- "PAN" → Permanent Account Number

Extract into this exact JSON (use null for missing):
{{
  "lei_code": "<extracted LEI code>",
  "legal_name": "<extracted legal name>",
  "cin": "<extracted CIN>",
  "pan_number": "<extracted PAN number>",
  "status": "ACTIVE",
  "registration_date": "<extracted registration date>",
  "renewal_date": "<extracted renewal date>",
  "issuing_lou": "Legal Entity Identifier India Ltd",
  "country": "India"
}}

EXTRACTION RULES:
- lei_code: exactly 20 alphanumeric characters (letters and digits only, no spaces)
- cin: starts with U or L, then 5 digits, 2 state letters, 4 year digits, 3 letters, 6 digits
- status: use ACTIVE for ISSUED status, INACTIVE for LAPSED/RETIRED
- dates: convert to DD/MM/YYYY format
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class IncorporationCertificateAgent(DocumentAgent):
    doc_type = "INCORPORATION_CERTIFICATE"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR extracted text from a Certificate of Incorporation issued by the Ministry of Corporate Affairs (MCA), Government of India.

WHAT THIS DOCUMENT LOOKS LIKE:
- An official government certificate with the MCA logo and emblem of India
- Header: "Ministry of Corporate Affairs" and "Certificate of Incorporation"
- Issued by the Registrar of Companies (ROC) of the respective state
- Has a CIN (Corporate Identification Number) prominently displayed
- States the company name in full, the date of incorporation
- Mentions authorized capital
- Has the ROC office name (e.g. "Registrar of Companies, Chennai")
- Digital signature of the Registrar
- After Companies Act 2013: also shows PAN allotted

FIELD LABELS ON DOCUMENT:
- "Corporate Identity Number" or "CIN" is 21-character alphanumeric starting with U or L
- "Name of the Company" in full registered company name in CAPS
- "Date of Incorporation" means when company was legally formed
- "Authorized Capital" means maximum capital the company can raise (in Rs.)
- "Registered Office Address" or "Registered Address" means company's official address
- "State" means state where company is registered
- "Registrar of Companies" means the ROC office (e.g. ROC Chennai, ROC Mumbai)
- "PAN" → Permanent Account Number
- "Type of Company" - Private Limited, Public Limited, OPC, LLP

IMPORTANT: CIN STRUCTURE: U/L (listed/unlisted) + 5-digit industry code + 2-letter state code + 4-digit year + PTC/PLC/OPC + 6-digit serial

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "cin": "<extracted CIN>",
  "pan_number": "<extracted PAN number>",
  "date_of_incorp": "<extracted date of incorporation>",
  "company_type": "<extracted company type>",
  "authorized_capital": "<extracted authorized capital>",
  "state": "<extracted state>",
  "roc": "<extracted ROC office>",
  "address": "<extracted registered office address>",
  "pincode": "<extracted pincode from address>"
}}

EXTRACTION RULES:
- cin: starts with U or L followed by exactly 20 more characters
- pan_number: exactly 10 chars 
- date_of_incorp: convert to DD/MM/YYYY
- authorized_capital: digits only, no Rs symbol, no commas (e.g. 2500000 not Rs.25,00,000)
- pincode: exactly 6 digits from the address
- company_type: Private Limited Company, Public Limited Company, One Person Company, LLP, etc.
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class MOAAgent(DocumentAgent):
    doc_type = "MOA"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a Memorandum of Association (MOA) of an Indian company, filed with the Registrar of Companies under the Companies Act 2013.

WHAT THIS DOCUMENT LOOKS LIKE:
- A multi-page legal document starting with "MEMORANDUM OF ASSOCIATION"
- Contains numbered clauses (I, II, III, IV, V, VI):
  - Clause I (Name Clause): "The name of the Company is ___"
  - Clause II (Situation Clause): "The Registered Office of the Company will be situated in the State of ___"
  - Clause III (Objects Clause): lists main objects (A) and incidental/ancillary objects (B)
  - Clause IV (Liability Clause): states liability is limited
  - Clause V (Capital Clause): authorized share capital amount and division
  - Clause VI (Subscription Clause): founding subscriber names, addresses, shares taken
- Header may show CIN number
- Witnesses and notary at the end

FIELD LOCATIONS:
- Company name: Clause I — "The name of the Company is [NAME]"
- CIN: top header or preamble
- State: Clause II — "situated in the State of [STATE]"
- Address: Clause II or preamble
- Authorized capital: Clause V — "Rs.___ divided into ___ shares of Rs.___ each"
- Main objects: Clause III(A) — numbered list of actual business activities - MUST COVER ALL OBJECTS.
- Subscribers: Clause VI table — columns for Name, Father's Name, Address, Occupation, Shares subscribed

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "cin": "<extracted CIN>",
  "state": "<extracted state>",
  "address": "<extracted registered office address>",
  "pincode": "<extracted pincode from address>",
  "authorized_capital": "<extracted authorized capital>",
  "main_objects": [
    "<extracted main object 1>",
    "<extracted main object 2>",
    "<extracted main object 3>",
    "<extracted main object N>"
  ],
  "subscribers": [
    {{"name": "<extracted subscriber 1>", "shares": "<extracted shares 1>"}},
    {{"name": "<extracted subscriber 2>", "shares": "<extracted shares 2>"}}
  ]
}}

EXTRACTION RULES:
- company_name: full legal name exactly as written in Clause I
- cin: starts with U or L (may not be present in old MOAs)
- authorized_capital: total capital in rupees as digits only (e.g. 2500000 from Rs.25,00,000)
- main_objects: extract EVERY numbered business activity from Clause III(A). These are the "Principal Business Objects". Do not skip any. Each point must be a full, meaningful sentence. Return as a clean list of strings.
- subscribers: people listed at end who subscribed to MOA with their share counts
- pincode: 6-digit PIN from any address mentioned
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.


OCR TEXT:
{ocr_text}"""


class AOAAgent(DocumentAgent):
    doc_type = "AOA"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from the Articles of Association (AOA) of an Indian company, filed with the Registrar of Companies under the Companies Act 2013.

WHAT THIS DOCUMENT LOOKS LIKE:
- A multi-page legal document starting with "ARTICLES OF ASSOCIATION"
- Follows Table F (for private limited) or other tables under Companies Act 2013
- Contains numbered Articles covering: share capital, transfer of shares, meetings, votes, directors, accounts, dividends
- Key sections:
  - Preamble or Article 1: Company name and CIN
  - Share Capital Article: authorized capital amount and share structure
  - Directors Article: minimum and maximum number of directors allowed
  - First Directors Article: lists the initial/founding directors with their 8-digit DIN

FIELD LOCATIONS:
- Company name: preamble "The regulations contained herein shall apply to [COMPANY NAME]"
- CIN: top header or preamble
- Authorized capital: "The Authorized Share Capital of the Company is Rs.___ divided into ___ shares of Rs.___ each"
- Min directors: "The minimum number of Directors shall be ___" or "not less than ___"
- Max directors: "The maximum number of Directors shall not exceed ___" or "maximum of ___"
- First directors: table or list with Name and DIN columns — DIN is always an 8-digit number

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "cin": "<extracted CIN>",
  "authorized_capital": "<extracted authorized capital>",
  "min_directors": "<extracted min directors>",
  "max_directors": "<extracted max directors>",
  "directors": [
    {{"name": "<extracted director 1>", "din": "<extracted DIN 1>"}},
    {{"name": "<extracted director 2>", "din": "<extracted DIN 2>"}}
  ],
  "summary_clauses": [
    "<key clause 1 summary e.g. Restriction on share transfer>",
    "<key clause 2 summary e.g. Voting rights 1 share 1 vote>",
    "<key clause 3 summary e.g. Director powers for borrowing>",
    "<key clause 4 summary e.g. Audit and Dividend regulations>"
  ]
}}

EXTRACTION RULES:
- company_name: full registered name from preamble
- cin: starts with U or L (may not appear in older AOAs)
- authorized_capital: digits only, no Rs or commas (e.g. 2500000)
- min_directors, max_directors: digit strings only (e.g. "2", "15")
- directors: extract ALL first directors listed with their 8-digit DIN numbers
- DIN is always 8 digits — look for labels "DIN:", "Director Identification Number:"
- summary_clauses: extract high-level summaries of the most important Articles (Share transfer, Borrowing powers, Quorum for meetings, etc.).
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class RegisteredAddressAgent(DocumentAgent):
    doc_type = "REGISTERED_ADDRESS"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a Registered Address document — this could be Form INC-22 (Notice of Situation of Registered Office), a proof of registered address letter, or an MCA filing confirmation.

WHAT THIS DOCUMENT LOOKS LIKE:
- INC-22 is an MCA e-form filed when a company registers or changes its address
- Has the MCA21 portal header
- Contains SRN (Service Request Number) — a unique filing reference like G12345678
- Shows CIN, company name, the full registered office address
- Has date of filing and date of approval/acknowledgment
- May contain GSTIN, PAN, LEI of the company
- Status will be APPROVED (STP - Straight Through Processing) or PENDING

FIELD LABELS:
- "Corporate Identity Number (CIN)" → CIN of company
- "Name of the Company" → full legal name
- "Registered Office Address" → broken into: flat/door number, building name, street, area, city, state, PIN
- "Service Request Number" or "SRN" → e.g. G12345678
- "Date of Filing" → when the form was filed
- "Date of Approval" or "Acknowledgment Date" → when approved
- "Status" → APPROVED or PENDING
- "GSTIN", "PAN", "LEI" → if mentioned

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "cin": "<extracted CIN>",
  "pan_number": "<extracted PAN number>",
  "gstin": "<extracted GSTIN>",
  "lei": "<extracted LEI>",
  "address_line1": "<extracted address line 1>",
  "address_line2": "<extracted address line 2>",
  "area": "<extracted area>",
  "city": "<extracted city>",
  "state": "<extracted state>",
  "pincode": "<extracted pincode>",
  "srn": "<extracted SRN>",
  "filing_date": "<extracted filing date>",
  "approval_date": "<extracted approval date>",
  "status": "<extracted status>"
}}

EXTRACTION RULES:
- Split address carefully: address_line1 = door/flat/building number, address_line2 = street/road name, area = locality/colony
- pincode: exactly 6 digits
- cin: starts with U or L
- gstin: exactly 15 characters
- lei: exactly 20 alphanumeric characters
- srn: alphanumeric MCA service request number
- dates: DD/MM/YYYY format
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class ElectricityBillAgent(DocumentAgent):
    doc_type = "ELECTRICITY_BILL"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from an Indian commercial electricity bill issued by a state electricity distribution company (DISCOM).

WHAT THIS DOCUMENT LOOKS LIKE:
- An A4 bill from a state electricity board: TANGEDCO (Tamil Nadu), MSEDCL (Maharashtra), BESCOM (Karnataka), BSES/BYPL (Delhi), PSPCL (Punjab), KSEB (Kerala), TSSPDCL (Telangana), CESC (West Bengal), etc.
- Has the DISCOM logo and name at top
- Shows consumer name, consumer number / account number / CA number
- Service address where electricity is supplied
- Bill number, bill date, due date
- Billing period (e.g. March 2024 or 01/03/2024 to 31/03/2024)
- Units consumed in kWh
- Total amount payable
- Connection type: Commercial (LT Commercial / HT) or Residential (LT Domestic)

FIELD LABELS (vary by DISCOM):
- "Consumer Name" or "Name of Consumer" → company/person name on the account
- "Consumer Number" or "CA No." or "Account No." or "Service No." or "BP Number" → unique account ID
- DISCOM name in letterhead or logo → electricity provider
- "Service Address" or "Installation Address" or "Supply Address" → where electricity is supplied
- "Pin Code" or "Pincode" → 6-digit postal code in address
- "Bill No." or "Bill Number" or "Invoice No." or "Document No." → bill reference
- "Bill Date" or "Billing Date" or "Invoice Date" → date bill was generated
- "Due Date" or "Last Date of Payment" or "Payment Due By" → payment deadline
- "Billing Period" or "Bill Period" or "Period" → consumption period
- "Units Consumed" or "Net Units" or "Total Units" or "Energy Consumed (kWh)" → consumption
- "Total Amount" or "Net Amount Payable" or "Amount Due" or "Gross Amount" → total in Rs.

Extract into this exact JSON (use null for missing):
{{
  "consumer_name": "<extracted consumer name>",
  "consumer_number": "<extracted consumer number>",
  "discom": "<extracted discom>",
  "address": "<extracted address>",
  "pincode": "<extracted pincode>",
  "bill_number": "<extracted bill number>",
  "bill_date": "<extracted bill date>",
  "due_date": "<extracted due date>",
  "billing_period": "<extracted billing period>",
  "units_consumed": "<extracted units consumed>",
  "total_amount": "<extracted total amount>",
  "connection_type": "<extracted connection type>"
}}

EXTRACTION RULES:
- consumer_name: the name of account holder/company printed on the bill — used for KYC
- discom: the electricity board short name (TANGEDCO, MSEDCL, BESCOM, BSES, BYPL, PSPCL, KSEB, TSSPDCL, CESC)
- pincode: exactly 6 digits from the service address
- bill_date, due_date: convert to DD/MM/YYYY
- total_amount: digits and decimal only, no Rs or commas (e.g. 36500 or 36500.50)
- units_consumed: digits only
- connection_type: Commercial for business, Residential for home
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class TelephoneBillAgent(DocumentAgent):
    doc_type = "TELEPHONE_BILL"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from an Indian telephone or landline bill issued by a telecom provider.

WHAT THIS DOCUMENT LOOKS LIKE:
- A bill from BSNL, Airtel, Jio, MTNL, Vodafone/Vi, or another Indian telecom company
- Has the telecom company logo and name at top
- Shows account holder name (company name for commercial connections)
- Account number / customer ID / telephone number
- Billing address
- Bill number, bill date, due date, billing period
- Total charges breakdown: rental, call charges, internet, taxes, etc.
- Total amount payable
- Connection type: Landline (fixed line) primarily used for commercial KYC proof

FIELD LABELS (vary by provider):
- "Account Name" or "Customer Name" or "Subscriber Name" or "Name" → name on account
- "Account No." or "Customer ID" or "CA No." or "STD+Number" → account identifier
- "Telephone No." or "Fixed Line No." or "Directory Number" → the phone number with STD code
- Company letterhead → provider name (BSNL, Airtel, Jio, MTNL, Vodafone, Vi)
- "Billing Address" or "Service Address" or "Installation Address" → address on account
- "Pin Code" or "PIN" → 6-digit postal code
- "Bill No." or "Invoice No." or "Bill Reference" → bill identifier
- "Bill Date" or "Invoice Date" or "Statement Date" → date of issue
- "Due Date" or "Payment Due Date" or "Last Date" → payment deadline
- "Billing Period" or "Bill Period" or "Period of Bill" → e.g. March 2024
- "Total Amount" or "Amount Payable" or "Net Payable" or "Total Due" → total

Extract into this exact JSON (use null for missing):
{{
  "account_name": "<extracted account name>",
  "account_number": "<extracted account number>",
  "telephone_number": "<extracted telephone number>",
  "provider": "<extracted provider>",
  "address": "<extracted address>",
  "pincode": "<extracted pincode>",
  "bill_number": "<extracted bill number>",
  "bill_date": "<extracted bill date>",
  "due_date": "<extracted due date>",
  "billing_period": "<extracted billing period>",
  "total_amount": "<extracted total amount>",
  "connection_type": "<extracted connection type>"
}}

EXTRACTION RULES:
- account_name: company/person name — this is used for KYC address proof
- provider: telecom company name (BSNL, Airtel, Jio, MTNL, Vodafone, Vi, etc.)
- telephone_number: include STD code for landlines (e.g. 04423456789)
- pincode: exactly 6 digits from the billing address
- bill_date, due_date: convert to DD/MM/YYYY
- total_amount: digits only, no Rs or commas
- connection_type: Landline or Mobile
- Do NOT copy these example values — extract from the OCR text below

NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.


OCR TEXT:
{ocr_text}"""


# ── Fraud Agents ──────────────────────────────────────────────

class BoardOfDirectorsAgent(DocumentAgent):
    doc_type = "BOARD_OF_DIRECTORS"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a Board of Directors disclosure document — this could be Form DIR-12 (MCA filing), an Annual Report Board section, a KYC document listing all directors, or a director declaration form.

WHAT THIS DOCUMENT LOOKS LIKE:
- Lists all current directors of the company
- Each director entry: full name, DIN (8-digit Director Identification Number), designation, date of appointment, shareholding IN PERCENT %, residential address, PAN, DOB, nationality
- DIN is always exactly 8 digits (e.g. 00123456) — mandatory unique identifier for all Indian directors
- Designations: Managing Director, Whole-Time Director, Independent Director, Non-Executive Director, Director, Chairman, Additional Director
- May show shareholding as % (AS PERCENTAGE) or as number of shares
- Other directorships: list of other companies where this person is a director (mandatory MCA disclosure)
- If from Annual Report: tabular format with columns

FIELD LABELS:
- "Director Identification Number" or "DIN" → 8-digit number per director
- "Name of Director" or name column → full name in CAPS
- "PAN" → director's personal PAN (10 chars, different from company PAN)
- "Date of Birth" or "DOB" → director's birth date
- "Designation" or "Category" → their board role
- "Shareholding" or "PERCENTAGE (%) of Shares held" → their ownership stake
- "Residential Address" → director's home address
- "Nationality" → usually Indian
- "Other Directorships" or "Directorships in other companies" → comma-separated list

Extract into this JSON LIKE THIS (use null for missing):
{{
  "company_name": "<extracted company name>",
  "cin": "<extracted CIN>",
  "pan": "<extracted PAN>",
  "directors": [
    {{
      "name": "<extracted director name>",
      "din": "<extracted DIN>",
      "pan": "<extracted PAN>",
      "dob": "<extracted DOB>",
      "designation": "<extracted designation>",
      "shareholding": "<extracted shareholding>",
      "address": "<extracted address>",
      "nationality": "Indian",
      "other_directorships": "<extracted other directorships>"
    }},
    {{
      "name": "<extracted director-2 name>",
      "din": "<extracted DIN>",
      "pan": "<extracted PAN>",
      "dob": "<extracted DOB>",
      "designation": "<extracted designation>",
      "shareholding": "<extracted shareholding>",
      "address": "<extracted address>",
      "nationality": "Indian",
      "other_directorships":"<extracted other directorships>"
    }},
    {{
      "name": "<extracted director-N name>",
      "din": "<extracted DIN>",
      "pan": "<extracted PAN>",
      "dob": "<extracted DOB>",
      "designation": "<extracted designation>",
      "shareholding": "<extracted shareholding>",
      "address": "<extracted address>",
      "nationality": "Indian",
      "other_directorships":"<extracted other directorships>"
    }}
  ]
}}

NOTE - ABOVE IS JUST AN EXAMPLE STRUCTURE — EXTRACT ALL DIRECTORS FOUND IN THE DOCUMENT INTO THIS FORMAT, DO NOT LIMIT TO 3. USE null FOR ANY MISSING FIELDS. BUT STRICLTLY FOLLOW THE STRUCTURE SHOWN ABOVE.

EXTRACTION RULES:
- Extract ALL directors found in the document
- DIN: exactly 8 digits — critical identifier
- director pan: personal PAN of each director (10 chars), NOT the company PAN
- company pan: the company-level PAN if shown separately at top
- dob: convert to DD/MM/YYYY
- shareholding: MAY include % symbol (e.g. "51%")
- other_directorships: comma-separated company names, null if none or "NIL"
- Do NOT copy these example values — extract from the OCR text below

NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.


OCR TEXT:
{ocr_text}"""


class KMPListAgent(DocumentAgent):
    doc_type = "KMP_LIST"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a Key Managerial Personnel (KMP) disclosure document — an MCA filing, Annual Report section, or KYC KMP declaration.

WHAT THIS DOCUMENT LOOKS LIKE:
- Lists KMPs as defined under Companies Act 2013 Section 2(51)
- Mandatory KMPs: MD/CEO/Manager, Company Secretary (CS), Chief Financial Officer (CFO)
- Larger companies may also list: Chief Operating Officer, Chief Technology Officer, etc.
- Company Secretary has an ICSI membership number (format: A12345 for Associate, F12345 for Fellow)
- CFO/CEO may have PAN and DIN if also a director
- Tabular format: Name | Designation | DIN/PAN | Email | Phone

FIELD LABELS:
- "Name" → full name of KMP
- "Designation" → CEO, MD, CFO, Company Secretary, Manager, COO, etc.
- "DIN" → 8-digit number (if KMP is also a director)
- "PAN" → personal PAN of the KMP
- "Membership No." or "CS Membership" or "ICSI Membership" → for Company Secretary
- "Email" or "Email ID" → official email
- "Mobile" or "Phone" or "Contact No." → contact number

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "kmps": [
    {{
      "name": "<extracted KMP - 1 name>",
      "designation": "<extracted designation>",
      "id_numbers": "<extracted ID numbers>",
      "email": "<extracted email>",
      "phone": "<extracted phone>"
    }},
    {{
      "name": "<extracted KMP - 2 name>",
      "designation": "<extracted designation>",
      "id_numbers": "<extracted ID numbers in JSON {{\"DIN\": \"<extracted DIN>\", \"PAN\": \"<extracted PAN>\", \"CS Membership\": \"<extracted CS membership>\"}} - OR ANYOTHER EXTRACTED ID NUMBERS, SKIP IF NONE DONT PUT NULL>",
      "email": "<extracted email>",
      "phone": "<extracted phone>"
    }}
    ,
     {{
      "name": "<extracted KMP - n name>",
      "designation": "<extracted designation>",
      "id_numbers": "<extracted ID numbers>",
      "email": "<extracted email>",
      "phone": "<extracted phone>"
    }}
  ]
}}

NOTE: ABOVE IS JUST AN EXAMPLE STRUCTURE — EXTRACT ALL KMPs FOUND IN THE DOCUMENT INTO THIS FORMAT, DO NOT LIMIT TO 3. USE null FOR ANY MISSING FIELDS. BUT STRICTLY FOLLOW THE STRUCTURE SHOWN ABOVE.

EXTRACTION RULES:
- Extract ALL KMPs found in the document
- id_numbers: combine all identification numbers as a readable string (PAN, DIN, membership number)
- designation: use the exact title from the document
- Do NOT copy these example values — extract from the OCR text below

NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.


OCR TEXT:
{ocr_text}"""


class BeneficialOwnersAgent(DocumentAgent):
    doc_type = "BENEFICIAL_OWNERS"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a Beneficial Ownership / UBO Declaration document — Form BEN-1 (MCA filing), a KYC UBO declaration, or an RBI/PMLA-compliant beneficial owner disclosure.

WHAT THIS DOCUMENT LOOKS LIKE:
- Discloses individuals who ultimately own or control the company
- Under Companies Act 2013: persons holding 25%+ are Significant Beneficial Owners (SBO)
- Under PMLA/RBI for NBFCs: threshold may be 10% or 15%
- Shows direct holding % (shares held in own name) and indirect holding % (through other entities) separately
- Also lists related/intermediate entities (holding companies, group companies)
- Form BEN-1 structure: declarant details, nature of interest, % of shares/voting rights/dividend rights/control

FIELD LABELS:
- "Name of the Significant Beneficial Owner" → UBO's full name
- "PAN" → UBO's personal PAN card number (10 chars)
- "Direct Holding" or "Direct Shareholding %" → % held directly in own name
- "Indirect Holding" or "Indirect Shareholding %" → % held through intermediate entities
- "Total Effective Holding" or "Total Beneficial Interest" → combined %
- "Nature of Interest" → Direct, Indirect, or Both
- "Related Entity" or "Intermediate Entity" → companies through which indirect holding flows
- "Relationship" → Holding Company, Associate Company, Group Company, etc.

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "ubos": [
    {{
      "name": "<extracted UBO name>",
      "pan": "<extracted PAN>",
      "direct_holding": "<extracted direct holding>",
      "indirect_holding": "<extracted indirect holding>",
      "total_effective": "<extracted total effective>",
      "nature": "<extracted nature>"
    }}
  ],
  "related_entities": [
    {{
      "name": "<extracted related entity name>",
      "pan": "<extracted related entity PAN>",
      "relationship": "<extracted relationship>",
      "ownership_pct": "<extracted ownership percentage>"
    }}
  ]
}}

EXTRACTION RULES:
- Extract ALL UBOs listed — there may be multiple
- Extract ALL related/intermediate entities listed
- pan: 10-character personal PAN of each UBO (not company PAN)
- holdings: include % symbol (e.g. "51%", "14.5%")
- nature: Direct, Indirect, or Both
- related_entities: companies that hold shares in the applicant company
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


class PEPDeclarationAgent(DocumentAgent):
    doc_type = "PEP_DECLARATION"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a PEP (Politically Exposed Person) Declaration — required by RBI/SEBI for KYC compliance at NBFCs and banks.

WHAT THIS DOCUMENT LOOKS LIKE:
- A self-declaration form signed by directors/KMPs/UBOs
- Declares whether the signatory is a PEP (politically exposed person)
- PEP = current or former senior government officials, military officers, judiciary, senior executives of state-owned enterprises, and their immediate family/close associates
- FATCA section: declares US person status for tax purposes
- Each person signs a separate section or they appear in a table
- Language patterns: "I/We hereby declare that I am/am not a Politically Exposed Person"

FIELD LABELS:
- "Name" or "Full Name" → declarant's full name
- "Designation" → their role in the company
- "PEP Status" or "Are you a PEP?" → the key YES/NO answer
- "Family member of PEP?" → whether a family member is a PEP
- "Close Associate of PEP?" → whether a close associate is a PEP

HOW TO READ PEP STATUS:
- "I am NOT a Politically Exposed Person" → pep_status = "NOT A PEP"
- "I am a Politically Exposed Person" → pep_status = "PEP"
- "No" checked next to PEP → pep_status = "NOT A PEP"
- "Yes" checked next to PEP → pep_status = "PEP"
- Tick/check mark next to "Not a PEP" → pep_status = "NOT A PEP"

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "declarations": [
    {{
      "name": "<extracted declarant - 1 name>",
      "designation": "<extracted designation>",
      "pep_status": "<extracted PEP status - "PEP" or "NOT A PEP">",
      "family_pep": "<extracted family PEP status - Yes/No>",
      "associate_pep": "<extracted associate PEP status - Yes/No>"
    }},
    {{
      "name": "<extracted declarant - 2 name>",
      "designation": "<extracted designation>",
      "pep_status": "<extracted PEP status "PEP" or "NOT A PEP">",
      "family_pep": "<extracted family PEP status - Yes/No>",
      "associate_pep": "<extracted associate PEP status - Yes/No>"
    }}
,
    {{
      "name": "<extracted declarant - N name>",
      "designation": "<extracted designation>",
      "pep_status": "<extracted PEP status - "PEP" or "NOT A PEP">",
      "family_pep": "<extracted family PEP status - Yes/No>",
      "associate_pep": "<extracted associate PEP status - Yes/No>"
    }}
  ]
}}

NOTE: ABOVE IS JUST AN EXAMPLE STRUCTURE — EXTRACT ALL DECLARANTS FOUND & THEIR PEP STATUS STRICTLY FROM THE DOCUMENT INTO THIS FORMAT, DO NOT LIMIT TO 3. USE null FOR ANY MISSING FIELDS. BUT STRICTLY FOLLOW THE STRUCTURE SHOWN ABOVE.

EXTRACTION RULES:
- pep_status MUST be EXACTLY "PEP" or "NOT A PEP" — no other values
- Extract declarations for ALL persons listed
- family_pep: "Yes" or "No"
- associate_pep: "Yes" or "No"
- Do NOT copy these example values — extract from the OCR text below

NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.


OCR TEXT:
{ocr_text}"""


class RPTDocumentAgent(DocumentAgent):
    doc_type = "RPT_DOCUMENT"

    def _build_prompt(self, ocr_text: str) -> str:
        return f"""You are reading OCR text from a Related Party Transactions (RPT) disclosure — Annual Report RPT section, board resolution approving RPTs, Form AOC-2 (MCA filing), or standalone RPT disclosure.

WHAT THIS DOCUMENT LOOKS LIKE:
- Discloses transactions between the company and its related parties
- Related parties: directors, KMPs, their relatives, holding/subsidiary/associate companies, entities where director holds >2% shares
- Under Section 188 Companies Act: certain RPTs require board/shareholder approval
- Typically tabular: columns for related party, relationship, transaction type, amount, terms, arm's length status, approval
- Form AOC-2: specifically for material RPTs and non-arm's-length RPTs
- Risk indicators: unsecured loans to promoters/directors, below-market pricing, missing approvals

FIELD LABELS (table columns):
- "Name of the Related Party" or "Party" → entity or person name
- "Nature of Relationship" or "Relationship" → e.g. "Wholly Owned Subsidiary", "Director", "Relative of Director", "KMP", "Associate Company"
- "Nature/Type of Transaction" → e.g. "Loan Given", "Purchase of Goods", "Sale of Services", "Rent Paid", "Remuneration", "Security Deposit", "Corporate Guarantee"
- "Amount (Rs.)" or "Value" → transaction amount
- "Terms and Conditions" → interest rate, tenure, pricing basis (arm's length or not)
- "Approval" → Board resolution, Shareholder approval at AGM/EGM, Audit Committee
- "Remarks" or "Risk" → any flags

RISK ASSESSMENT:
- HIGH: loans to promoters/directors without collateral, non-arm's-length pricing, missing approvals, unexplained large transfers, corporate guarantees for group entities
- MEDIUM: approved inter-company loans, significant purchase/sale with group companies, lease with related parties
- LOW: standard director remuneration at approved levels, arm's-length routine transactions with full board/shareholder approval

Extract into this exact JSON (use null for missing):
{{
  "company_name": "<extracted company name>",
  "related_party_transactions": [
    {{
      "related_party": "<extracted related party name>",
      "relationship": "<extracted relationship>",
      "transaction_type": "<extracted transaction type>",
      "amount": "<extracted amount>",
      "terms": "<extracted terms>",
      "approval": "<extracted approval>",
      "risk_flag": "<extracted risk flag - HIGH/MEDIUM/LOW>"
    }},
    {{
      "related_party": "<extracted related party name>",
      "relationship": "<extracted relationship>",
      "transaction_type": "Managerial Remuneration",
      "amount": "<extracted amount>",
      "terms": "<extracted terms>",
      "approval": "<extracted approval>",
      "risk_flag": "<extracted risk flag - HIGH/MEDIUM/LOW>"
    }}
  ]
}}

NOTE: ABOVE IS JUST AN EXAMPLE STRUCTURE — EXTRACT ALL RPTs FOUND IN THE DOCUMENT INTO THIS FORMAT, DO NOT LIMIT TO 2. USE null FOR ANY MISSING FIELDS. BUT STRICTLY FOLLOW THE STRUCTURE SHOWN ABOVE.

EXTRACTION RULES:
- Extract ALL related party transactions listed
- amount: digits only, no Rs or commas (e.g. 5000000 not Rs.50,00,000)
- relationship: describe clearly including % of shareholding if mentioned
- risk_flag: HIGH / MEDIUM / LOW based on transaction risk profile described above
- Do NOT copy these example values — extract from the OCR text below


NOTE: GIVE ONLY THE JSON AS OUTPUT — DO NOT COPY ANY OF THE ABOVE EXAMPLE VALUES OR FIELD NAMES — EXTRACT FROM THE OCR TEXT BELOW AND OUTPUT ONLY THE JSON, NO MARKDOWN, NO EXPLANATION, NO EXTRA TEXT. JUST THE JSON OUTPUT.

OCR TEXT:
{ocr_text}"""


# ── Agent Registry ────────────────────────────────────────────

_AGENT_INSTANCES: dict[str, DocumentAgent] = {
    "PAN_CARD":                  PANCardAgent(),
    "GST_CERTIFICATE":           GSTCertificateAgent(),
    "LEI_CERTIFICATE":           LEICertificateAgent(),
    "INCORPORATION_CERTIFICATE": IncorporationCertificateAgent(),
    "MOA":                       MOAAgent(),
    "AOA":                       AOAAgent(),
    "REGISTERED_ADDRESS":        RegisteredAddressAgent(),
    "ELECTRICITY_BILL":          ElectricityBillAgent(),
    "TELEPHONE_BILL":            TelephoneBillAgent(),
    "BOARD_OF_DIRECTORS":        BoardOfDirectorsAgent(),
    "KMP_LIST":                  KMPListAgent(),
    "BENEFICIAL_OWNERS":         BeneficialOwnersAgent(),
    "PEP_DECLARATION":           PEPDeclarationAgent(),
    "RPT_DOCUMENT":              RPTDocumentAgent(),
}


def get_agent(doc_type: str) -> DocumentAgent | None:
    """Return the agent instance for a given doc_type, or None if unsupported."""
    return _AGENT_INSTANCES.get(doc_type)


async def extract_document(
    ocr_text: str,
    doc_type: str,
    confidence: float = 0.0,
) -> dict:
    """
    Convenience function — replaces old extract_fields_llm().
    Returns a plain dict compatible with existing DB storage.
    """
    agent = get_agent(doc_type)
    if agent is None:
        print(f"⚠️ No agent for doc_type: {doc_type}")
        return {}

    result = await agent.extract(ocr_text, confidence)
    return result.fields if result.status != "FAILED" else {}