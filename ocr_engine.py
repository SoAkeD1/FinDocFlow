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

    # Updated keyword sets per specification (including new categories)
    categories = {
        "KYC Document": {
            "pan", "aadhaar", "voter", "passport", "date of birth", "dob", "permanent account", "name"
        },
        "Loan Application": {
            "loan application", "loan amount", "loan purpose", "applicant", "co-applicant", "emi", "repayment", "name"
        },
        "Bank Statement": {
            "balance", "opening balance", "closing balance", "bank statement", "transaction", "debit", "credit", "ifsc", "name"
        },
        "Income Certificate": {
            "income", "salary", "form 16", "itr", "tax return", "employer", "name"
        },
        "Credit Card Details": {
            "credit score", "civil score", "swift code", "name"
        },
        "Address Proof": {
            "residence", "address proof", "electricity bill", "water bill", "gas bill", "rent agreement", "utility", "name"
        },
        "Birth Certificate": {
            "birth certificate", "date of birth", "municipal corporation", "registrar of births", "name"
        },
        "Education Certificate": {
            "marksheet", "degree", "diploma", "university", "board of education", "passing certificate", "name"
        },
        "Property Document": {
            "sale deed", "property", "registration", "stamp duty", "plot number", "survey number", "name"
        },
        "Employment Proof": {
            "offer letter", "appointment letter", "employee id", "designation", "HR", "company letterhead", "name"
        },
        "Photo ID": {
            "photo", "photograph", "photo id", "photo identity", "image", "name"
        },
        "Presentation/Other": {
            "presentation", "slide", "deck", "pdf", "report", "minutes"
        },
        "Unknown Document": {}
    }

    best_category = "Unknown Document"
    best_score = 0

    for category, keywords in categories.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category


def extract_name(text):
    prefixes = [
        "account holder name", "account holder", "applicant name",
        "customer name", "holder name", "pan name", "applicant", "name"
    ]

    for line in text.split('\n'):
        if ':' not in line:
            continue
        label, colon, rest = line.partition(':')
        label_clean = label.strip().lower()
        for prefix in prefixes:
            if prefix in label_clean:
                value = rest.strip()
                if value:
                    return value
    return None
