import re
import io
import time
import pytesseract
from PIL import Image
import validators

def classify_document_type(text):
    text_lower = text.lower()
    if any(kw in text_lower for kw in ['loan application', 'loan form', 'personal loan', 'loan amount', 'loan no', 'loan account', 'loan']):
        return 'loan_form'
    if any(kw in text_lower for kw in ['aadhaar', 'voter id', 'driving licence', 'kyc', 'identity', 'address proof']):
        return 'kyc'
    if any(kw in text_lower for kw in ['bank statement', 'transaction', 'account number', 'statement', 'balance']):
        return 'bank_statement'
    if any(kw in text_lower for kw in ['salary', 'income certificate', 'income', 'pay', 'employer', 'gross salary']):
        return 'income_certificate'
    return 'unknown'

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
    income = extract_income(full_text)
    address = extract_address(full_text)

    # Confidence per field (hard-coded nominal values when a field is extracted)
    def _confidence(val, default=0.90):
        return default if val else 0.0

    confidence_per_field = {
        "name": _confidence(name, 0.90),
        "pan": _confidence(pan, 0.95),
        "date": _confidence(date, 0.95),
        "loan_amount": _confidence(loan_amount, 0.90),
        "account_number": _confidence(account_number, 0.95),
        "income": _confidence(income, 0.90),
        "address": _confidence(address, 0.80),
    }

    # Overall confidence (average of all fields, scaled to percentage)
    values = list(confidence_per_field.values())
    overall_confidence = (sum(values) / len(values)) * 100
    overall_confidence = round(overall_confidence, 1)

    # Determine processing status based on overall confidence
    if overall_confidence >= 90:
        status = "Auto-Approved"
    elif overall_confidence >= 75:
        status = "Review"
    else:
        status = "Manual"

    processing_time = round(_time.time() - start_time, 2)

    extracted_fields = {
        "name": name,
        "pan": pan,
        "date": date,
        "loan_amount": loan_amount,
        "account_number": account_number,
        "income": income,
        "address": address,
    }

    issues = []  # Populate later if any field‑level problems are detected

    result = {
        "filename": filename,
        "doc_type": doc_type,
        "overall_confidence": overall_confidence,
        "processing_time_sec": processing_time,
        "status": status,
        "extracted_fields": extracted_fields,
        "confidence_per_field": confidence_per_field,
        "issues": issues,
    }
    return result
