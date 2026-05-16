import re
import io
import time
import pytesseract
from PIL import Image
import validators

# ─────────────────────────────────────────────
#  KEYWORD MASTER LIST  (used for classification)
# ─────────────────────────────────────────────
DOCUMENT_CATEGORIES = {
    "KYC Document": {
        "pan", "aadhaar", "aadhar", "voter", "passport", "date of birth", "dob",
        "permanent account", "name", "kyc", "know your customer", "identity proof",
        "id proof", "photo id", "photograph", "signature", "nationality",
        "father name", "mother name", "gender", "male", "female",
        "uid", "unique identification", "biometric", "fingerprint",
        "iris", "face", "enrollment", "enrolment", "resident",
        "nric", "national id", "identification number",
    },
    "Loan Application": {
        "loan application", "loan amount", "loan purpose", "applicant",
        "co-applicant", "emi", "repayment", "name", "home loan", "personal loan",
        "car loan", "vehicle loan", "education loan", "gold loan", "business loan",
        "mortgage", "tenure", "rate of interest", "interest rate", "principal",
        "disbursement", "sanction", "guarantor", "collateral", "security",
        "ltv", "loan to value", "processing fee", "prepayment", "foreclosure",
        "nach", "ecs", "auto debit", "standing instruction", "repayment mode",
        "loan account", "loan number", "application number", "reference number",
        "down payment", "margin", "subsidy", "pmay", "pradhan mantri",
    },
    "Bank Statement": {
        "balance", "opening balance", "closing balance", "bank statement",
        "transaction", "debit", "credit", "ifsc", "name", "account statement",
        "account number", "account holder", "savings account", "current account",
        "overdraft", "neft", "rtgs", "imps", "upi", "chq", "cheque",
        "atm", "pos", "withdrawal", "deposit", "transfer", "payment",
        "interest credit", "bank charges", "service charge", "gst",
        "available balance", "ledger balance", "passbook", "mini statement",
        "statement period", "branch", "micr", "swift", "bic",
        "salary credit", "emi debit", "loan emi", "utility bill",
    },
    "Income Certificate": {
        "income", "salary", "form 16", "itr", "tax return", "employer", "name",
        "income certificate", "income proof", "salary slip", "pay slip", "payslip",
        "pay stub", "gross salary", "net salary", "basic salary", "hra",
        "house rent allowance", "da", "dearness allowance", "ta", "travel allowance",
        "medical allowance", "special allowance", "bonus", "incentive", "overtime",
        "pf", "provident fund", "esi", "professional tax", "tds", "income tax",
        "ctc", "cost to company", "annual income", "monthly income",
        "net monthly salary", "take home", "in hand salary",
        "form 16a", "16b", "26as", "assessment year", "financial year",
        "pan", "employer pan", "tan", "traces",
    },
    "Credit Card Details": {
        "credit score", "civil score", "swift code", "name",
        "cibil", "experian", "equifax", "crif", "credit bureau",
        "credit report", "credit history", "credit limit", "available credit",
        "outstanding balance", "minimum due", "payment due", "due date",
        "card number", "card holder", "cardholder", "expiry", "cvv",
        "reward points", "cashback", "statement date", "billing cycle",
        "credit utilization", "credit enquiry", "hard enquiry", "soft enquiry",
        "default", "npa", "write off", "settled", "dpd", "days past due",
    },
    "Address Proof": {
        "residence", "address proof", "electricity bill", "water bill",
        "gas bill", "rent agreement", "utility", "name",
        "residential address", "permanent address", "current address",
        "house number", "flat number", "floor", "building", "society",
        "street", "road", "lane", "nagar", "colony", "sector", "block",
        "district", "state", "pin code", "pincode", "postal code", "zip",
        "municipality", "panchayat", "corporation", "ward", "taluk",
        "tehsil", "mandal", "village", "city", "town",
        "telephone bill", "broadband bill", "internet bill", "cable bill",
        "ration card", "driving licence", "voter id", "passport",
        "bank passbook", "lease agreement", "licence agreement",
        "consumer number", "meter number", "connection number",
        "bill number", "bill date", "due date", "amount due",
        "units consumed", "reading", "sanctioned load",
    },
    "Birth Certificate": {
        "birth certificate", "date of birth", "municipal corporation",
        "registrar of births", "name",
        "born on", "place of birth", "birth place", "hospital",
        "nursing home", "maternity", "child name", "baby name",
        "father name", "mother name", "parents", "guardian",
        "registration number", "certificate number", "serial number",
        "birth registration", "civil registration", "vital statistics",
        "gender", "sex", "male", "female", "weight at birth",
        "time of birth", "nationality", "religion",
    },
    "Education Certificate": {
        "marksheet", "degree", "diploma", "university", "board of education",
        "passing certificate", "name",
        "marks", "marks obtained", "maximum marks", "percentage",
        "grade", "cgpa", "sgpa", "gpa", "result", "pass", "fail",
        "distinction", "first class", "second class", "division",
        "roll number", "registration number", "enrollment number",
        "subject", "course", "programme", "stream", "branch",
        "semester", "year", "annual", "exam", "examination",
        "board", "cbse", "icse", "state board", "matriculation",
        "10th", "12th", "graduation", "post graduation", "phd",
        "bachelor", "master", "btech", "mtech", "bsc", "msc",
        "ba", "ma", "bcom", "mcom", "mba", "bba",
        "school", "college", "institute", "institution", "academy",
        "principal", "controller of examinations", "registrar",
        "convocation", "transcript", "provisional certificate",
    },
    "Property Document": {
        "sale deed", "property", "registration", "stamp duty", "plot number",
        "survey number", "name",
        "property document", "title deed", "conveyance deed",
        "gift deed", "will", "partition deed", "power of attorney",
        "agreement to sell", "sale agreement", "purchase agreement",
        "property tax", "house tax", "mutation", "khata", "patta",
        "encumbrance certificate", "ec", "occupancy certificate", "oc",
        "completion certificate", "building plan", "layout plan",
        "carpet area", "built up area", "super built up area",
        "floor", "flat", "apartment", "villa", "bungalow", "plot",
        "land", "site", "khata number", "pid number", "assessment number",
        "ward", "zone", "locality", "sub registrar", "registrar office",
        "buyer", "seller", "vendor", "purchaser", "transferor", "transferee",
        "consideration amount", "market value", "guidance value",
        "circle rate", "ready reckoner", "document number",
    },
    "Employment Proof": {
        "offer letter", "appointment letter", "employee id", "designation",
        "hr", "company letterhead", "name",
        "employment proof", "experience letter", "relieving letter",
        "service certificate", "joining letter", "confirmation letter",
        "increment letter", "promotion letter", "transfer letter",
        "employment contract", "work order",
        "employee name", "employee code", "staff id", "badge number",
        "department", "division", "reporting manager", "date of joining",
        "date of relieving", "last working day", "notice period",
        "company name", "organisation", "organization", "firm",
        "registered office", "corporate office", "hr department",
        "human resources", "payroll", "compensation", "remuneration",
        "probation", "permanent", "contractual", "full time", "part time",
    },
    "Photo ID": {
        "photograph", "driving licence", "identity card", "name",
        "driving license", "dl number", "licence number", "license number",
        "vehicle class", "rto", "regional transport office",
        "blood group", "height", "address",
        "employee card", "student id", "college id", "school id",
        "pan card", "aadhaar card", "voter id card", "ration card",
        "arms licence", "firearms licence",
        "id number", "card number", "identity number",
        "valid upto", "valid till", "expiry date", "date of issue",
        "issuing authority", "issued by", "issued at",
    },
    "Tax Document": {
        "income tax", "itr", "form 16", "form 26as", "assessment year",
        "financial year", "tax return", "tds", "tax deducted at source",
        "advance tax", "self assessment tax", "refund", "tax payable",
        "gross total income", "deductions", "80c", "80d", "hra exemption",
        "standard deduction", "tax slab", "surcharge", "cess",
        "pan", "acknowledgement number", "efiling", "itr1", "itr2",
        "itr3", "itr4", "schedule", "computation of income",
        "salary income", "house property", "capital gains",
        "business income", "other sources", "exempt income",
        "total income", "total tax", "tax paid",
    },
    "Insurance Document": {
        "insurance", "policy", "policy number", "insured", "insurer",
        "premium", "sum assured", "sum insured", "coverage",
        "life insurance", "health insurance", "motor insurance",
        "general insurance", "term plan", "endowment", "ulip",
        "claim", "maturity", "nominee", "beneficiary",
        "policy term", "premium paying term", "premium due date",
        "grace period", "lapse", "revival", "surrender value",
        "paid up value", "death benefit", "critical illness",
        "cashless", "reimbursement", "network hospital",
        "irda", "irdai", "agent", "broker", "advisor",
        "proposal form", "medical report", "underwriting",
        "exclusion", "waiting period", "co-payment", "deductible",
    },
    "Vehicle Document": {
        "registration certificate", "rc book", "rc", "vehicle registration",
        "chassis number", "engine number", "vehicle number",
        "number plate", "registration number", "registration date",
        "make", "model", "manufacturer", "year of manufacture",
        "fuel type", "petrol", "diesel", "cng", "electric", "hybrid",
        "color", "colour", "seating capacity", "gross weight",
        "fitness certificate", "pollution certificate", "puc",
        "insurance validity", "road tax", "rto", "transport office",
        "hypothecation", "noc", "transfer of ownership",
        "driving licence", "dl", "licence class", "endorsement",
    },
    "Medical Document": {
        "prescription", "medical certificate", "diagnosis", "patient",
        "doctor", "physician", "hospital", "clinic", "medical centre",
        "patient name", "patient id", "opd", "ipd", "ward",
        "medicine", "drug", "tablet", "capsule", "syrup", "injection",
        "dosage", "dose", "frequency", "duration", "refill",
        "blood test", "urine test", "x-ray", "mri", "ct scan",
        "ultrasound", "ecg", "echo", "biopsy", "pathology",
        "lab report", "test report", "hemoglobin", "blood sugar",
        "blood pressure", "pulse", "temperature", "weight", "height",
        "discharge summary", "admission", "discharge", "treatment",
        "surgery", "operation", "procedure", "anaesthesia",
        "icd", "diagnosis code", "registration number",
    },
    "Presentation/Other": {
        "presentation", "slide", "agenda", "objective",
        "conclusion", "thank you", "name",
        "introduction", "overview", "summary", "contents",
        "table of contents", "chapter", "section",
    },
}


# ─────────────────────────────────────────────
#  DOCUMENT CLASSIFICATION
# ─────────────────────────────────────────────

def classify_document_type(text):
    text_lower = text.lower()
    scores = {}
    for cat, keywords in DOCUMENT_CATEGORIES.items():
        total = sum(text_lower.count(kw) for kw in keywords)
        scores[cat] = total
    best_cat = max(scores, key=scores.get)
    return "Unknown Document" if scores[best_cat] == 0 else best_cat


# ─────────────────────────────────────────────
#  LOW-LEVEL EXTRACTION HELPERS
# ─────────────────────────────────────────────

def _find_label_value(text, label_variants):
    """
    Search every line for 'label: value' pattern.
    label_variants is a list of strings to match (case-insensitive, partial).
    Returns the first non-empty value found.
    """
    for line in text.split('\n'):
        if ':' not in line:
            continue
        label, _, rest = line.partition(':')
        label_clean = label.strip().lower()
        for variant in label_variants:
            if variant in label_clean:
                value = rest.strip()
                if value:
                    return value
    return None


def _find_amount(text, keyword_hints=None):
    """
    Extract a monetary amount.
    If keyword_hints provided, search those lines first.
    Falls back to first ₹/Rs. amount in full text.
    """
    lines = text.split('\n')
    if keyword_hints:
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keyword_hints):
                nums = re.findall(r'[₹\s]*([\d,]+\.?\d*)', line)
                if nums:
                    cleaned = [n.replace(',', '') for n in nums if len(n.replace(',', '')) >= 2]
                    if cleaned:
                        return cleaned[0]
    # fallback
    nums = re.findall(r'(?:₹|Rs\.?)\s*([\d,]+\.?\d*)', text)
    if nums:
        return nums[0].replace(',', '')
    return None


def _find_date(text, label_variants=None):
    """Find a date, optionally near a label."""
    date_pattern = r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})\b'
    if label_variants:
        for line in text.split('\n'):
            if any(v in line.lower() for v in label_variants):
                m = re.search(date_pattern, line)
                if m:
                    return m.group(1)
    m = re.search(date_pattern, text)
    return m.group(1) if m else None


def _find_number(text, label_variants, pattern=r'[\dXx]{6,20}'):
    """Find a number (account, ID, etc.) near a label."""
    for line in text.split('\n'):
        line_lower = line.lower()
        if any(v in line_lower for v in label_variants):
            m = re.search(pattern, line)
            if m:
                return m.group(0)
    return None


# ─────────────────────────────────────────────
#  LEGACY SINGLE-FIELD EXTRACTORS  (kept for backward compat)
# ─────────────────────────────────────────────

def extract_pan(text):
    m = re.search(r'[A-Z]{5}\d{4}[A-Z]', text)
    return m.group(0) if m else None


def extract_name(text):
    label_variants = [
        "account holder name", "account holder",
        "applicant name", "full name", "customer name",
        "holder name", "pan name", "employee name",
        "student name", "candidate name", "child name",
        "insured name", "policy holder", "card holder",
        "cardholder", "name of applicant", "name of employee",
        "name", "applicant",
    ]
    return _find_label_value(text, label_variants)


def extract_date(text):
    return _find_date(text)


def extract_loan_amount(text):
    return _find_amount(text, ["loan amount", "sanctioned amount", "approved amount"])


def extract_account_number(text):
    result = _find_number(text, ["account number", "account no", "acc no", "a/c no"])
    if result:
        return result
    # numeric fallback
    m = re.search(r'\b(\d{9,18})\b', text)
    return m.group(1) if m else None


def extract_income(text):
    return _find_amount(text, [
        "gross salary", "net salary", "monthly salary",
        "net monthly salary", "take home", "in hand",
        "income", "salary", "annual ctc", "ctc",
    ])


def extract_address(text):
    return _find_label_value(text, ["address", "residential address", "permanent address", "premises"])


# ─────────────────────────────────────────────
#  SMART DYNAMIC FIELD EXTRACTOR  (by document type)
# ─────────────────────────────────────────────

def extract_fields_by_type(doc_type, text):
    """
    Returns a dict of {field_name: value} relevant to the document type.
    Only non-None values are included.
    """
    fields = {}

    def fv(variants):
        return _find_label_value(text, variants)

    def fa(hints):
        return _find_amount(text, hints)

    def fd(variants):
        return _find_date(text, variants)

    def fn(variants, pattern=r'[\dXx]{6,20}'):
        return _find_number(text, variants, pattern)

    if doc_type == "Bank Statement":
        fields["Account Holder"]   = fv(["account holder name", "account holder", "name"])
        fields["Account Number"]   = fn(["account number", "account no", "a/c no"])
        fields["IFSC Code"]        = fv(["ifsc code", "ifsc"])
        fields["Branch"]           = fv(["branch"])
        fields["Account Type"]     = fv(["account type"])
        fields["Statement Period"] = fv(["period", "statement period", "from", "date"])
        fields["Opening Balance"]  = fa(["opening balance"])
        fields["Closing Balance"]  = fa(["closing balance"])
        fields["Total Credits"]    = fa(["total credit", "total credits"])
        fields["Total Debits"]     = fa(["total debit", "total debits"])
        fields["Net Change"]       = fa(["net change"])
        fields["MICR Code"]        = fn(["micr"], r'\d{9}')
        fields["SWIFT / BIC"]      = fv(["swift", "bic"])

    elif doc_type == "Loan Application":
        fields["Applicant Name"]     = fv(["full name", "applicant name", "name"])
        fields["PAN"]                = extract_pan(text)
        fields["Aadhaar"]            = fv(["aadhaar", "aadhar", "uid"])
        fields["Mobile"]             = fn(["mobile", "phone", "contact"], r'\+?[\d\s\-]{10,13}')
        fields["Email"]              = fv(["email"])
        fields["Date of Birth"]      = fd(["date of birth", "dob"])
        fields["Loan Type"]          = fv(["loan type"])
        fields["Loan Amount"]        = fa(["loan amount"])
        fields["Loan Purpose"]       = fv(["loan purpose", "purpose"])
        fields["Tenure"]             = fv(["tenure", "repayment period"])
        fields["Rate of Interest"]   = fv(["rate of interest", "interest rate", "roi"])
        fields["EMI"]                = fa(["emi preferred", "emi", "monthly instalment"])
        fields["Application No"]     = fv(["application number", "application no", "ref"])
        fields["Employer"]           = fv(["employer", "company", "organisation", "organization"])
        fields["Designation"]        = fv(["designation", "position"])
        fields["Monthly Salary"]     = fa(["gross salary", "net salary", "monthly salary"])
        fields["Annual CTC"]         = fa(["annual ctc", "ctc", "annual income"])
        fields["Account Number"]     = fn(["account number", "account no"])
        fields["IFSC Code"]          = fv(["ifsc"])
        fields["Co-Applicant Name"]  = fv(["co-applicant", "co applicant"])
        fields["Guarantor Name"]     = fv(["guarantor"])
        fields["Property Value"]     = fa(["property value"])
        fields["Down Payment"]       = fa(["down payment", "margin"])

    elif doc_type == "KYC Document":
        fields["Name"]          = fv(["name", "full name", "applicant name"])
        fields["PAN"]           = extract_pan(text)
        fields["Aadhaar / UID"] = fv(["aadhaar", "aadhar", "uid", "enrolment"])
        fields["Date of Birth"] = fd(["date of birth", "dob"])
        fields["Gender"]        = fv(["gender", "sex"])
        fields["Father Name"]   = fv(["father", "father name", "father's name"])
        fields["Mother Name"]   = fv(["mother", "mother name", "mother's name"])
        fields["Address"]       = fv(["address", "permanent address"])
        fields["Nationality"]   = fv(["nationality"])
        fields["Mobile"]        = fn(["mobile", "phone", "contact"], r'\+?[\d\s\-]{10,13}')

    elif doc_type == "Income Certificate":
        fields["Employee Name"]   = fv(["employee name", "name", "applicant"])
        fields["PAN"]             = extract_pan(text)
        fields["Employer"]        = fv(["employer", "company", "organisation", "organization"])
        fields["Designation"]     = fv(["designation", "position"])
        fields["Department"]      = fv(["department", "division"])
        fields["Date of Joining"] = fd(["date of joining", "joining date"])
        fields["Basic Salary"]    = fa(["basic salary", "basic"])
        fields["HRA"]             = fa(["hra", "house rent allowance"])
        fields["DA"]              = fa(["dearness allowance", " da "])
        fields["Gross Salary"]    = fa(["gross salary", "gross"])
        fields["Deductions"]      = fa(["total deduction", "deductions"])
        fields["Net Salary"]      = fa(["net salary", "net pay", "take home", "in hand"])
        fields["Annual CTC"]      = fa(["annual ctc", "ctc"])
        fields["TDS"]             = fa(["tds", "tax deducted"])
        fields["PF"]              = fa(["provident fund", " pf "])
        fields["Assessment Year"] = fv(["assessment year", "ay"])
        fields["Financial Year"]  = fv(["financial year", "fy"])

    elif doc_type == "Tax Document":
        fields["Name"]              = fv(["name", "assessee"])
        fields["PAN"]               = extract_pan(text)
        fields["Assessment Year"]   = fv(["assessment year", "ay"])
        fields["Financial Year"]    = fv(["financial year", "fy"])
        fields["ITR Type"]          = fv(["itr", "return type", "form"])
        fields["Gross Total Income"]= fa(["gross total income"])
        fields["Total Deductions"]  = fa(["total deductions", "deductions under chapter"])
        fields["Total Income"]      = fa(["total income", "net income"])
        fields["Tax Payable"]       = fa(["tax payable", "total tax"])
        fields["TDS"]               = fa(["tds", "tax deducted at source"])
        fields["Advance Tax"]       = fa(["advance tax"])
        fields["Refund"]            = fa(["refund"])
        fields["Acknowledgement No"]= fv(["acknowledgement", "ack no"])
        fields["E-Filing Date"]     = fd(["date of filing", "filed on", "filing date"])

    elif doc_type == "Credit Card Details":
        fields["Card Holder Name"] = fv(["card holder", "cardholder", "name"])
        fields["Card Number"]      = fn(["card number"], r'[\dX*]{12,19}')
        fields["Credit Score"]     = fv(["credit score", "cibil score", "civil score", "score"])
        fields["Credit Limit"]     = fa(["credit limit", "total limit"])
        fields["Available Credit"] = fa(["available credit", "available limit"])
        fields["Outstanding"]      = fa(["outstanding", "amount due", "total outstanding"])
        fields["Minimum Due"]      = fa(["minimum due", "min due", "minimum amount due"])
        fields["Payment Due Date"] = fd(["payment due", "due date"])
        fields["Statement Date"]   = fd(["statement date", "billing date"])
        fields["SWIFT Code"]       = fv(["swift code", "swift", "bic"])
        fields["Bank Name"]        = fv(["bank name", "issuer", "issued by"])

    elif doc_type == "Address Proof":
        fields["Name"]             = fv(["name", "consumer name", "customer name", "account holder"])
        fields["Address"]          = fv(["address", "service address", "premises", "installation address"])
        fields["Consumer Number"]  = fv(["consumer number", "consumer no", "connection number", "customer id"])
        fields["Bill Number"]      = fv(["bill number", "bill no", "invoice number"])
        fields["Bill Date"]        = fd(["bill date", "invoice date", "date of bill"])
        fields["Due Date"]         = fd(["due date", "last date of payment"])
        fields["Units Consumed"]   = fv(["units", "units consumed", "reading"])
        fields["Amount Due"]       = fa(["amount due", "amount payable", "total amount", "net payable"])
        fields["Pin Code"]         = fn(["pin", "pincode", "postal code", "zip"], r'\d{6}')

    elif doc_type == "Birth Certificate":
        fields["Child Name"]       = fv(["child name", "baby name", "name of child", "name"])
        fields["Date of Birth"]    = fd(["date of birth", "born on", "dob"])
        fields["Place of Birth"]   = fv(["place of birth", "born at", "hospital", "birth place"])
        fields["Gender"]           = fv(["gender", "sex"])
        fields["Father Name"]      = fv(["father name", "father", "father's name"])
        fields["Mother Name"]      = fv(["mother name", "mother", "mother's name"])
        fields["Registration No"]  = fv(["registration number", "certificate number", "serial number"])
        fields["Date of Issue"]    = fd(["date of issue", "issued on", "issue date"])
        fields["Issued By"]        = fv(["issued by", "issuing authority", "municipal", "registrar"])

    elif doc_type == "Education Certificate":
        fields["Student Name"]     = fv(["student name", "candidate name", "name"])
        fields["Roll Number"]      = fv(["roll number", "roll no", "registration number", "enrollment"])
        fields["Institution"]      = fv(["university", "institution", "college", "school", "board"])
        fields["Course / Degree"]  = fv(["course", "degree", "diploma", "programme", "stream"])
        fields["Specialization"]   = fv(["specialization", "branch", "subject"])
        fields["Year of Passing"]  = fv(["year of passing", "passing year", "year"])
        fields["Marks Obtained"]   = fv(["marks obtained", "total marks", "marks"])
        fields["Percentage / CGPA"]= fv(["percentage", "cgpa", "gpa", "grade"])
        fields["Result"]           = fv(["result", "division", "class", "grade"])
        fields["Date of Issue"]    = fd(["date of issue", "issued on"])

    elif doc_type == "Property Document":
        fields["Owner / Buyer Name"]   = fv(["buyer", "purchaser", "owner", "transferee", "name"])
        fields["Seller Name"]          = fv(["seller", "vendor", "transferor"])
        fields["Property Address"]     = fv(["property", "premises", "address"])
        fields["Survey / Plot No"]     = fv(["survey number", "plot number", "plot no", "survey no"])
        fields["Area"]                 = fv(["area", "carpet area", "built up area"])
        fields["Property Value"]       = fa(["property value", "consideration", "sale value", "market value"])
        fields["Stamp Duty"]           = fa(["stamp duty"])
        fields["Registration Charges"] = fa(["registration charges", "registration fee"])
        fields["Document Number"]      = fv(["document number", "doc no", "deed number"])
        fields["Registration Date"]    = fd(["registration date", "date of registration", "executed on"])
        fields["Sub Registrar Office"] = fv(["sub registrar", "registrar office", "sro"])

    elif doc_type == "Employment Proof":
        fields["Employee Name"]    = fv(["employee name", "name of employee", "name"])
        fields["Employee ID"]      = fv(["employee id", "emp id", "staff id", "badge"])
        fields["Designation"]      = fv(["designation", "position", "role"])
        fields["Department"]       = fv(["department", "division"])
        fields["Company Name"]     = fv(["company", "organisation", "organization", "employer"])
        fields["Date of Joining"]  = fd(["date of joining", "joining date", "doj"])
        fields["Date of Relieving"]= fd(["date of relieving", "relieving date", "last working day"])
        fields["Employment Type"]  = fv(["employment type", "type of employment", "category"])
        fields["Reporting Manager"]= fv(["reporting manager", "reporting to", "supervisor"])
        fields["HR Name / Sign"]   = fv(["hr", "human resources", "authorized signatory"])

    elif doc_type == "Photo ID":
        fields["Name"]          = fv(["name"])
        fields["ID Number"]     = fv(["licence number", "license number", "id number", "card number", "dl no"])
        fields["Date of Birth"] = fd(["date of birth", "dob"])
        fields["Blood Group"]   = fv(["blood group", "blood"])
        fields["Address"]       = fv(["address"])
        fields["Valid Till"]    = fd(["valid till", "valid upto", "expiry", "expiry date"])
        fields["Issuing RTO"]   = fv(["rto", "issuing authority", "issued by"])
        fields["Vehicle Class"] = fv(["vehicle class", "class of vehicle", "endorsement"])

    elif doc_type == "Insurance Document":
        fields["Policy Holder"]   = fv(["insured", "policy holder", "policyholder", "name"])
        fields["Policy Number"]   = fv(["policy number", "policy no"])
        fields["Plan / Product"]  = fv(["plan name", "product name", "policy name", "plan"])
        fields["Sum Assured"]     = fa(["sum assured", "sum insured", "coverage amount"])
        fields["Premium Amount"]  = fa(["premium", "annual premium", "monthly premium"])
        fields["Policy Term"]     = fv(["policy term", "term"])
        fields["Start Date"]      = fd(["start date", "commencement date", "inception date"])
        fields["Maturity Date"]   = fd(["maturity date", "end date", "expiry date"])
        fields["Premium Due Date"]= fd(["premium due date", "next due date"])
        fields["Nominee"]         = fv(["nominee", "beneficiary"])
        fields["Agent / Advisor"] = fv(["agent", "advisor", "broker"])

    elif doc_type == "Vehicle Document":
        fields["Owner Name"]         = fv(["owner name", "registered owner", "name"])
        fields["Registration Number"]= fv(["registration number", "reg no", "vehicle number"])
        fields["Chassis Number"]     = fv(["chassis number", "chassis no"])
        fields["Engine Number"]      = fv(["engine number", "engine no"])
        fields["Make / Model"]       = fv(["make", "manufacturer"])
        fields["Model"]              = fv(["model"])
        fields["Fuel Type"]          = fv(["fuel type", "fuel"])
        fields["Color"]              = fv(["color", "colour"])
        fields["Year of Manufacture"]= fv(["year of manufacture", "manufacturing year", "year"])
        fields["Registration Date"]  = fd(["registration date", "date of registration"])
        fields["Fitness Valid Till"]  = fd(["fitness", "fitness valid", "fitness upto"])
        fields["Insurance Valid Till"]= fd(["insurance valid", "insurance upto", "insurance expiry"])
        fields["Hypothecation"]       = fv(["hypothecation", "financer", "finance company"])

    elif doc_type == "Medical Document":
        fields["Patient Name"]    = fv(["patient name", "patient", "name"])
        fields["Patient ID"]      = fv(["patient id", "uhid", "mrn", "registration number"])
        fields["Doctor Name"]     = fv(["doctor", "physician", "dr.", "consultant"])
        fields["Hospital"]        = fv(["hospital", "clinic", "centre", "center"])
        fields["Diagnosis"]       = fv(["diagnosis", "impression", "findings"])
        fields["Date"]            = fd(["date", "visit date", "consultation date"])
        fields["Medicines"]       = fv(["medicine", "drug", "rx", "prescription"])
        fields["Blood Group"]     = fv(["blood group"])
        fields["Age"]             = fv(["age"])
        fields["Gender"]          = fv(["gender", "sex"])

    # Remove None values
    return {k: v for k, v in fields.items() if v}


# ─────────────────────────────────────────────
#  CONFIDENCE SCORING
# ─────────────────────────────────────────────

def compute_confidence(fields_dict):
    """
    Confidence = % of non-None fields out of total fields attempted.
    """
    if not fields_dict:
        return 0
    total = len(fields_dict) + fields_dict.get('__total_attempted', 0)
    found = sum(1 for k, v in fields_dict.items() if v and k != '__total_attempted')
    total = max(total, found)
    return round((found / total) * 100) if total > 0 else 0


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────

def process_document_bytes(file_bytes, filename=''):
    start_time = time.time()

    try:
        from pdf2image import convert_from_bytes
        _has_pdf2image = True
    except ImportError:
        _has_pdf2image = False

    # ── OCR ──────────────────────────────────
    if filename.lower().endswith('.pdf'):
        if not _has_pdf2image:
            raise RuntimeError("pdf2image is not installed. Cannot OCR PDF files.")
        images = convert_from_bytes(file_bytes)
        full_text = '\n'.join(
            pytesseract.image_to_string(img, lang='eng') for img in images
        )
    else:
        image = Image.open(io.BytesIO(file_bytes))
        full_text = pytesseract.image_to_string(image, lang='eng')

    # ── Classify ─────────────────────────────
    doc_type = classify_document_type(full_text)

    # ── Legacy 6-field extraction (kept for backward compat) ──
    name           = extract_name(full_text)
    pan            = extract_pan(full_text)
    date           = extract_date(full_text)
    loan_amount    = extract_loan_amount(full_text)
    account_number = extract_account_number(full_text)
    income         = extract_income(full_text)

    # ── Smart dynamic extraction ──────────────
    dynamic_fields = extract_fields_by_type(doc_type, full_text)

    # ── Matched keywords ─────────────────────
    doc_keywords = DOCUMENT_CATEGORIES.get(doc_type, set())
    text_lower   = full_text.lower()
    matched_keywords = [kw for kw in doc_keywords if kw in text_lower]

    # ── Confidence (based on dynamic fields) ─
    if dynamic_fields:
        found  = len(dynamic_fields)
        # use 10 as denominator baseline so partial docs don't score 100%
        total  = max(found + 2, 10)
        confidence = round((found / total) * 100)
    else:
        # legacy fallback
        legacy = [name, pan, date, loan_amount, account_number, income]
        found  = sum(1 for v in legacy if v)
        confidence = round((found / 6) * 100)

    proc_time = round(time.time() - start_time, 3)

    result = {
        'text':             full_text,
        'doc_type':         doc_type,
        'matched_keywords': matched_keywords,
        'dynamic_fields':   dynamic_fields,
        # legacy fields
        'name':             name,
        'pan':              pan,
        'date':             date,
        'loan_amount':      loan_amount,
        'account_number':   account_number,
        'income':           income,
        'address':          extract_address(full_text),
        'confidence':       confidence,
        'proc_time':        proc_time,
    }
    return result