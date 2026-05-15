import streamlit as st
import pandas as pd
import time
import random
import re
import io
import json
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
        df_ext = pd.DataFrame(extracted_items, columns=["Field", "Value"])
        st.dataframe(df_ext, use_container_width=True)

        st.info(f"**Decision:** {decision}   |   **Confidence:** {confidence}%")


# ---------- Page: Dashboard ----------
def dashboard_page():
    st.subheader("📊 Dashboard")

    rows = get_all_documents()  # list of sqlite3.Row

    if not rows:
        st.warning("No documents have been processed yet. Go to **Upload & Process** to add data.")
        return

    df = pd.DataFrame(rows, columns=rows[0].keys())

    # --- Metric cards ---
    total_docs = len(df)
    avg_conf = df["confidence_score"].mean()
    approved = int(df["status"].str.contains("Approved", case=False).sum())
    latest_name = df.iloc[0]["filename"] if total_docs > 0 else "N/A"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Documents", total_docs)
    col2.metric("Avg Confidence", f"{avg_conf:.1f}%")
    col3.metric("Auto‑Approved", approved)
    col4.metric("Latest Upload", latest_name)

    st.markdown("---")

    # --- Charts ---
    left, right = st.columns(2)

    with left:
        st.markdown("#### Documents by Type")
        type_counts = df["doc_type"].value_counts().reset_index()
        type_counts.columns = ["doc_type", "count"]
        fig_bar = px.bar(
            type_counts,
            x="doc_type",
            y="count",
            color="doc_type",
            labels={"doc_type": "Document Type", "count": "Count"},
            template="plotly_white",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with right:
        st.markdown("#### Documents by Status")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig_pie = px.pie(
            status_counts,
            names="status",
            values="count",
            color="status",
            hole=0.4,
            template="plotly_white",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # --- Recent documents table ---
    st.markdown("#### Last 10 Documents")
    last10 = df.head(10)
    st.dataframe(last10, use_container_width=True)


# ---------- Page: Audit Log ----------
def audit_page():
    st.subheader("📋 Audit Log")

    rows = get_all_documents()

    if not rows:
        st.info("No audit records yet. Process documents to populate the log.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=rows[0].keys())

    # --- Search bar ---
    search_term = st.text_input("🔍 Search by filename or document type")
    if search_term:
        mask = (
            df["filename"].str.contains(search_term, case=False, na=False)
            | df["doc_type"].str.contains(search_term, case=False, na=False)
        )
        df = df[mask]

    st.markdown(f"**{len(df)} record(s) found**")

    # --- Full history table ---
    st.dataframe(df, use_container_width=True)

    # --- CSV download ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download CSV",
        data=csv,
        file_name="audit_log.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # --- Compare two documents side by side ---
    st.markdown("#### Compare Two Documents")

    doc_ids = [r["id"] for r in rows if r["id"]]
    doc_labels = {r["id"]: f"{r['id']} – {r['filename']}" for r in rows if r["id"]}

    if len(doc_ids) < 2:
        st.info("Need at least two documents to compare.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        sel_a = st.selectbox("Select Document A", doc_ids, format_func=lambda x: doc_labels.get(x, str(x)))
    with col_b:
        sel_b = st.selectbox("Select Document B", doc_ids, format_func=lambda x: doc_labels.get(x, str(x)))

    if sel_a and sel_b:
        doc_a = get_document_by_id(sel_a)
        doc_b = get_document_by_id(sel_b)

        if doc_a and doc_b:
            a_extracted = json.loads(doc_a["extracted_json"]) if doc_a["extracted_json"] else {}
            b_extracted = json.loads(doc_b["extracted_json"]) if doc_b["extracted_json"] else {}

            # Compare fields
            field_keys = sorted(set(list(a_extracted.get("fields", {}).keys()) + list(b_extracted.get("fields", {}).keys())))

            comp_data = []
            for key in field_keys:
                a_val = a_extracted.get("fields", {}).get(key, "")
                b_val = b_extracted.get("fields", {}).get(key, "")
                comp_data.append({"Field": key, f"Doc {sel_a}": a_val, f"Doc {sel_b}": b_val})

            comp_df = pd.DataFrame(comp_data)
            st.dataframe(comp_df, use_container_width=True)
        else:
            st.error("Could not load the selected documents.")
    else:
        st.info("Select both documents to compare.")


# ---------- Sidebar Navigation ----------
if "page" not in st.session_state:
    st.session_state.page = "Home"

with st.sidebar:
    st.markdown("# 📄 FinDocFlow")
    st.markdown("**Sundaram Finance**")
    st.divider()
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "Home"
    if st.button("📤 Upload & Process", use_container_width=True):
        st.session_state.page = "Upload"
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"
    if st.button("📋 Audit Log", use_container_width=True):
        st.session_state.page = "Audit"

# ---------- Page Routing ----------
if st.session_state.page == "Home":
    home_page()
elif st.session_state.page == "Upload":
    upload_page()
elif st.session_state.page == "Dashboard":
    dashboard_page()
elif st.session_state.page == "Audit":
    audit_page()
else:
    home_page()
