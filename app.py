import streamlit as st
import pandas as pd
import time
import random
import re
import io
import pytesseract
from PIL import Image
import logging
import plotly.express as px
import base64
import database
from database import get_all_documents, get_document_by_id

logger = logging.getLogger(__name__)

# ---------- Page config (must be first Streamlit command) ----------
st.set_page_config(page_title="FinDocFlow", layout="wide", page_icon="📄")

# ---------- Ensure DB tables exist ----------
database.create_tables()


# ---------- OCR extraction function (unchanged from original) ----------
def process_document_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Process uploaded document bytes using Tesseract OCR.
    Returns a dict with keys:
        'fields' : dict of extracted field names -> value or None
        'confidence': float between 0 and 100
    """
    results = {
        "name": None,
        "pan": None,
        "date": None,
        "loan_amount": None,
        "account_number": None,
        "income": None,
    }

    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            # use pdf2image to convert each page to a PIL image
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(file_bytes)
            for img in images:
                gray = img.convert("L")
                page_text = pytesseract.image_to_string(gray, lang="eng")
                text += page_text + "\n"
        else:
            # assume it’s an image file
            img = Image.open(io.BytesIO(file_bytes))
            gray = img.convert("L")
            text = pytesseract.image_to_string(gray, lang="eng")
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        # continue with empty text

    # --- Name extraction ---
    name_pattern = r"(?:name|applicant|customer)\s*[:=]\s*(.+)"
    match = re.search(name_pattern, text, re.IGNORECASE)
    if match:
        name_candidate = match.group(1).strip()
        # Take only the first line and remove punctuation from the end
        name_candidate = name_candidate.split("\n")[0].strip()
        name_candidate = re.sub(r"[^\w\s]", "", name_candidate).strip()
        if name_candidate:
            results["name"] = name_candidate

    # --- PAN ---
    pan_pattern = r"\b[A-Za-z]{5}\d{4}[A-Za-z]\b"
    match = re.search(pan_pattern, text)
    if match:
        results["pan"] = match.group(0).upper()

    # --- Date (DD/MM/YYYY or DD-MM-YYYY) ---
    date_pattern = r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b"
    match = re.search(date_pattern, text)
    if match:
        results["date"] = match.group(1)

    # --- Loan Amount ---
    amount_pattern = r"(?:Rs\.?|INR|amount)\s*[:=]?\s*([\d,]+(?:\.\d+)?)"
    match = re.search(amount_pattern, text, re.IGNORECASE)
    if match:
        raw = match.group(1).replace(",", "")
        results["loan_amount"] = raw

    # --- Account Number (9‑18 digits) ---
    acct_pattern = r"\b\d{9,18}\b"
    matches = re.findall(acct_pattern, text)
    if matches:
        results["account_number"] = matches[0]

    # --- Income ---
    income_pattern = r"(?:income|salary)\s*[:=]?\s*([\d,]+(?:\.\d+)?)"
    match = re.search(income_pattern, text, re.IGNORECASE)
    if match:
        raw = match.group(1).replace(",", "")
        results["income"] = raw

    # --- Confidence ---
    total_fields = len(results)  # 6
    found = sum(1 for value in results.values() if value is not None)
    confidence = round((found / total_fields) * 100) if total_fields else 0

    return {"fields": results, "confidence": confidence}


# ---------- Page: Home ----------
def home_page():
    st.title("🏠 Welcome to FinDocFlow")
    st.markdown(
        """
        **FinDocFlow** – Intelligent Document Processing for Financial Documents.

        Use the sidebar to navigate:
        - **📤 Upload & Process** – Extract key fields from scanned documents using OCR.
        - **📊 Dashboard** – View summary statistics and charts for processed documents.
        - **📋 Audit Log** – Search, review and export document processing history.
        """
    )


# ---------- Page: Upload & Process ----------
def upload_page():
    st.subheader("📤 Upload & Process")
    st.markdown(
        "Upload a financial document and extract key fields using OCR."
    )
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        with st.spinner("Processing document…"):
            extraction = process_document_bytes(bytes_data, uploaded_file.name)

        # Simulate a brief “decision” step (unchanged for illustration)
        time.sleep(0.3)
        st.success("Processing complete!")
        decision = random.choice(["Approved", "Review Required", "Rejected"])

        # Extract fields and confidence
        fields = extraction["fields"]
        confidence = extraction["confidence"]

        # Build a friendly table of extracted fields
        extracted_items = [
            ("Applicant Name", fields.get("name")),
            ("PAN", fields.get("pan")),
            ("Date (Detected)", fields.get("date")),
            ("Loan Amount", fields.get("loan_amount")),
            ("Account Number", fields.get("account_number")),
            ("Income", fields.get("income")),
        ]

        # Convert to DataFrame for display
        df_ext