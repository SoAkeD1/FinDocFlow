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
      'Income Certificate', 'Presentation/Other', 'Unknown Document'
    """
    text_lower = text.lower()

    # Define keywords for each category
    categories = {
        "KYC Document": {
            "kyc", "know your customer", "aadhaar", "aadhar",
            "identity", "voter", "passport"
        },
        "Loan Application": {
            "loan application", "loan amount", "loan purpose",
            "emi", "repayment", "tenure", "disbursement"
        },
        "Bank Statement": {
            "account statement", "transaction", "debit", "credit",
            "balance", "opening balance", "closing balance", "bank statement"
        },
        "Income Certificate": {
            "income", "salary", "form 16", "itr", "tax return", "employer"
        },
        "Presentation/Other": {
            "presentation", "slide", "agenda", "objective",
            "conclusion", "thank you"
        },
    }

    scores = {}
    for cat, keywords in categories.items():
        total = 0
        for kw in keywords:
            total += text_lower.count(kw)
        scores[cat] = total

    # Pick the category with the highest score
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return "Unknown Document"
    return best_cat


def extract_pan(text):
    pattern = r'[A-Z]{5}\d{4}[A-Z]'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_name(text):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'name' in line.lower() and ':' in line:
            parts = line.split(':', 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
    return None


def extract_date(text):
    pattern = r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b'
    match = re.search(pattern, text)
    return match.group(1) if match else None


def extract_loan_amount(text):
    lines = text.split('\n')
    for line in lines:
        if 'loan amount' in line.lower() or 'amount' in line.lower():
            nums = re.findall(r'[\d,]+\.?\d*', line)
            if nums:
                return nums[0].replace(',', '')
    nums = re.findall(r'₹?\s?([\d,]+\.?\d*)', text)
    if nums:
        return nums[0].replace(',', '')
    return None


def extract_account_number(text):
    pattern = r'\b(\d{9,18})\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def extract_income(text):
    lines = text.split('\n')
    for line in lines:
        if 'income' in line.lower() or 'salary' in line.lower():
            nums = re.findall(r'[\d,]+\.?\d*', line)
            if nums:
                return nums[0].replace(',', '')
    return None


def extract_address(text):
    """Simple address extraction by looking for a line containing 'address' and a colon."""
    lines = text.split('\n')
    for line in lines:
        if 'address' in line.lower() and ':' in line:
            parts = line.split(':', 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
    return None


def process_document_bytes(file_bytes, filename=''):
    import time as _time
    import io as _io
    from PIL import Image as _PIL_Image
    import pytesseract as _pytesseract  # already imported, but keep local reference

    start_time = _time.time()

    # Try to import pdf2image (only needed for PDFs)
    try:
        from pdf2image import convert_from_bytes
        _has_pdf2image = True
    except ImportError:
        _has_pdf2image = False

    if filename.lower().endswith('.pdf'):
        if not _has_pdf2image:
            raise RuntimeError(
                "pdf2image is not installed. Cannot perform OCR on PDF files."
            )
        # Convert PDF pages to images and OCR each page
        images = convert_from_bytes(file_bytes)
        full_text = ''
        for img in images:
            full_text += _pytesseract.image_to_string(img, lang='eng') + '\n'
    else:
        # Assume it's an image
        image = _PIL_Image.open(_io.BytesIO(file_bytes))
        full_text = _pytesseract.image_to_string(image, lang='eng')

    # Classify document type
    doc_type = classify_document_type(full_text)

    # Extract fields
    name = extract_name(full_text)
    pan = extract_pan(full_text)
    date = extract_date(full_text)
    loan_amount = extract_loan_amount(full_text)
    account_number = extract_account_number(full_text)
    income