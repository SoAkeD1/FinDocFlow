import re
import io
import pytesseract
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def process_document_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Process uploaded document bytes using Tesseract OCR.
    Returns a dict with keys:
        'fields' : dict of extracted field names -> value or None
        'confidence': float between 0 and 100
    """
    results = {
        'name': None,
        'pan': None,
        'date': None,
        'loan_amount': None,
        'account_number': None,
        'income': None,
    }

    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            # use pdf2image to convert each page to PIL Image
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_bytes)
            for img in images:
                # Convert to grayscale for better OCR
                gray = img.convert('L')
                # Optional: apply thresholding? Not needed.
                # Use Tesseract
                page_text = pytesseract.image_to_string(gray, lang='eng')
                text += page_text + "\n"
        else:
            # Assume image
            img = Image.open(io.BytesIO(file_bytes))
            gray = img.convert('L')
            text = pytesseract.image_to_string(gray, lang='eng')
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        # Continue with empty text
        pass

    # --- Name extraction ---
    # Look for name: label patterns
    name_pattern = r'(?:name|applicant|customer)\s*[:=]\s*(.+)'
    match = re.search(name_pattern, text, re.IGNORECASE)
    if match:
        name_candidate = match.group(1).strip()
        # Clean up possible extra characters
        # Take until newline or following keyword
        name_candidate = name_candidate.split('\n')[0].strip()
        # remove punctuation at end
        name_candidate = re.sub(r'[^\w\s]', '', name_candidate).strip()
        if name_candidate:
            results['name'] = name_candidate

    # --- PAN ---
    pan_pattern = r'\b[A-Za-z]{5}\d{4}[A-Za-z]\b'
    match = re.search(pan_pattern, text)
    if match:
        results['pan'] = match.group(0).upper()

    # --- Date ---
    date_pattern = r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'
    match = re.search(date_pattern, text)
    if match:
        results['date'] = match.group(1)

    # --- Loan Amount ---
    amount_pattern = r'(?:Rs