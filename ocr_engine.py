import re
import io
import time
import pytesseract
from PIL import Image
import validators


def classify_document_type(text):
    """
    Return the category with the highest keyword‑match score.
    Possible categories:
      'KYC Document', 'Loan Application', 'Bank Statement',
      'Income Certificate', 'Credit Card Details', 'Address Proof',
      'Birth Certificate', 'Education Certificate', 'Property Document',
      'Employment Proof', 'Photo ID', 'Presentation/Other', 'Unknown Document'
    """
    text_lower = text.lower()

    categories = {
        "KYC Document": {
            "pan", "aadhaar", "voter", "passport", "date of birth", "dob",
            "permanent account", "name"
        },
        "Loan Application": {
            "loan application", "loan amount", "loan purpose", "applicant",
            "co-applicant", "emi", "repayment", "name"
        },
        "Bank Statement": {
            "balance", "opening balance", "closing balance", "bank statement",
            "transaction", "debit", "credit", "ifsc", "name"
        },
        "Income Certificate": {
            "income", "salary", "form 16", "itr", "tax return", "employer",
            "name"
        },
        "Credit Card Details": {
            "credit score", "civil score", "swift code", "name"
        },
        "Address Proof": {
            "address", "proof", "electricity", "bill", "name"
        },
        "Birth Certificate": {
            "birth", "born", "father", "mother", "name"
        },
        "Education Certificate": {
            "university", "degree", "diploma", "marks", "name"
        },
        "Property Document": {
            "property", "registration", "stamp", "sale", "name"
        },
        "Employment Proof": {
            "employer", "employee", "designation", "date of joining", "name"
        },
        "Photo ID": {
            "licence", "passport", "photo", "id", "name"
        },
        "Presentation/Other": {
            "presentation", "slide", "chart", "graph"
        },
        "Unknown Document": {
            "unknown", "document"
        },
    }

    scores = {}
    for category, keywords in categories.items():
        count = 0
        for kw in keywords:
            if kw in text_lower:
                count += 1
        scores[category] = count

    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "Unknown Document"
    return best_category


def extract_pan(text):
    pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
    matches = re.findall(pan_pattern, text)
    return matches[0] if matches else None


def process_document_bytes(file_bytes: bytes, filename: str) -> dict:
    image = Image.open(io.BytesIO(file_bytes))
    full_text = pytesseract.image_to_string(image)

    doc_type = classify_document_type(full_text)
    dynamic_fields = extract_fields_by_type(doc_type, full_text)

    # basic confidence estimation (placeholder)
    confidence = 0.99

    result = {
        'filename': filename,
        'full_text': full_text,
        'doc_type': doc_type,
        'confidence': confidence,
        'dynamic_fields': dynamic_fields,
    }
    return result


def extract_fields_by_type(doc_type, text):
    fields = {}
    lines = text.split('\n')

    def find_value(keywords):
        for line in lines:
            if ':' not in line:
                continue
            label, _, rest = line.partition(':')
            label_clean = label.strip().lower()
            for kw in keywords:
                if kw in label_clean:
                    val = rest.strip()
                    if val:
                        return val
        return None

    def find_amount(keywords):
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                nums = re.findall(r'[₹Rs.\s]*([\d,]+\.?\d*)', line)
                if nums:
                    return nums[0].replace(',', '')
        return None

    if doc_type == "Bank Statement":
        fields["Account Holder"] = find_value(["account holder", "account holder name", "name"])
        fields["Account Number"] = find_value(["account number", "account no"])
        fields["IFSC Code"] = find_value(["ifsc", "ifsc code"])
        fields["Opening Balance"] = find_amount(["opening balance"])
        fields["Closing Balance"] = find_amount(["closing balance"])
        fields["Branch"] = find_value(["branch"])

    elif doc_type == "Loan Application":
        fields["Applicant Name"] = find_value(["full name", "applicant name", "name"])
        fields["PAN"] = extract_pan(text)
        fields["Loan Amount"] = find_amount(["loan amount"])
        fields["Loan Type"] = find_value(["loan type"])
        fields["Tenure"] = find_value(["tenure"])
        fields["EM