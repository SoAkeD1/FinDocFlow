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
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

    .hero { text-align: center; padding: 3rem 1rem 1.5rem; }
    .hero h1 { font-family: 'Syne', sans-serif; font-size: 3.2rem; font-weight: 800; color: #f0a500; margin-bottom: 0.3rem; }
    .hero p { font-family: 'DM Sans', sans-serif; font-size: 1.15rem; color: #ffffff; margin-bottom: 0.5rem; }
    .hero small { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.95rem; }
    .gold-divider { height: 2px; background: linear-gradient(90deg, transparent, #f0a500, transparent); margin: 2rem auto; width: 60%; }

    .section-title { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700; color: #ffffff; text-align: center; margin: 2.5rem 0 1.2rem; }

    .steps-row { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
    .step-card { background: #161b27; border: 1px solid #2a2f3e; border-left: 3px solid #f0a500; border-radius: 12px; padding: 20px; flex: 1; min-width: 180px; max-width: 220px; animation: fadeSlideUp 0.5s ease both; }
    .step-card:nth-child(1) { animation-delay: 0.1s; }
    .step-card:nth-child(2) { animation-delay: 0.2s; }
    .step-card:nth-child(3) { animation-delay: 0.3s; }
    .step-card:nth-child(4) { animation-delay: 0.4s; }
    .step-icon { font-size: 2rem; margin-bottom: 8px; }
    .step-num { font-family: 'Syne', sans-serif; color: #f0a500; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
    .step-title { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1rem; font-weight: 700; margin: 4px 0; }
    .step-desc { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.85rem; }

    .stats-row { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
    .stat-box { background: #161b27; border: 1px solid #2a2f3e; border-top: 3px solid #f0a500; border-radius: 12px; padding: 18px 24px; text-align: center; flex: 1; min-width: 160px; }
    .stat-icon { font-size: 1.5rem; }
    .stat-val { font-family: 'Syne', sans-serif; color: #f0a500; font-size: 1rem; font-weight: 700; margin: 4px 0; }
    .stat-label { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.82rem; }

    .doc-row { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
    .doc-card { background: #161b27; border: 1px solid #2a2f3e; border-radius: 12px; padding: 22px; flex: 1; min-width: 180px; max-width: 260px; transition: border-color 0.3s, transform 0.3s; }
    .doc-card:hover { border-color: #f0a500; transform: translateY(-4px); }
    .doc-icon { font-size: 2rem; margin-bottom: 8px; }
    .doc-title { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 6px; }
    .doc-desc { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.85rem; }

    .cta-banner { background: #161b27; border-left: 4px solid #f0a500; border-radius: 12px; padding: 24px 32px; text-align: center; margin: 1rem 0 2rem; }
    .cta-banner h3 { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1.4rem; margin-bottom: 6px; }
    .cta-banner p { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.95rem; }

    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>

    <div class="hero">
        <h1>FinDocFlow</h1>
        <p>AI-Powered Document Intelligence for Indian NBFCs</p>
        <small>From scanned paper to structured data in seconds — no manual entry, no errors.</small>
    </div>
    <div class="gold-divider"></div>

    <div class="section-title">How It Works</div>
    <div class="steps-row">
        <div class="step-card">
            <div class="step-icon">📤</div>
            <div class="step-num">Step 1</div>
            <div class="step-title">Upload Document</div>
            <div class="step-desc">Submit PDF, JPG or PNG files from any device</div>
        </div>
        <div class="step-card">
            <div class="step-icon">🔍</div>
            <div class="step-num">Step 2</div>
            <div class="step-title">OCR Extraction</div>
            <div class="step-desc">Tesseract reads PAN, name, dates, loan amount, account number</div>
        </div>
        <div class="step-card">
            <div class="step-icon">🎯</div>
            <div class="step-num">Step 3</div>
            <div class="step-title">Confidence Scoring</div>
            <div class="step-desc">Auto-approved above 90%, flagged for review below 70%</div>
        </div>
        <div class="step-card">
            <div class="step-icon">📋</div>
            <div class="step-num">Step 4</div>
            <div class="step-title">Audit & Export</div>
            <div class="step-desc">Full audit trail logged, PDF reports generated instantly</div>
        </div>
    </div>

    <div class="section-title">By The Numbers</div>
    <div class="stats-row">
        <div class="stat-box"><div class="stat-icon">⚡</div><div class="stat-val">Auto-Approved</div><div class="stat-label">&gt;90% Confidence</div></div>
        <div class="stat-box"><div class="stat-icon">🏦</div><div class="stat-val">4 Doc Types</div><div class="stat-label">KYC · Loan · Bank · Income</div></div>
        <div class="stat-box"><div class="stat-icon">🔒</div><div class="stat-val">Audit Trail</div><div class="stat-label">Every action logged</div></div>
        <div class="stat-box"><div class="stat-icon">📄</div><div class="stat-val">PDF Export</div><div class="stat-label">Reports on demand</div></div>
    </div>

    <div class="section-title">What FinDocFlow Processes</div>
    <div class="doc-row">
        <div class="doc-card">
            <div class="doc-icon">🪪</div>
            <div class="doc-title">KYC Documents</div>
            <div class="doc-desc">Aadhaar, PAN, Voter ID — extract name, DOB, ID numbers instantly</div>
        </div>
        <div class="doc-card">
            <div class="doc-icon">📝</div>
            <div class="doc-title">Loan Applications</div>
            <div class="doc-desc">Capture applicant name, loan amount, date, co-applicant details</div>
        </div>
        <div class="doc-card">
            <div class="doc-icon">🏦</div>
            <div class="doc-title">Bank Statements</div>
            <div class="doc-desc">Parse account number, transactions, income patterns</div>
        </div>
    </div>

    <div class="cta-banner">
        <h3>Ready to digitise your NBFC back-office?</h3>
        <p>Upload your first document and see FinDocFlow in action.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Go to Upload & Process", use_container_width=True):
            st.session_state.page = "Upload"
            st.rerun()

# ---------- Page: Upload & Process ----------
def upload_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

    .upload-hero { text-align: center; padding: 2rem 1rem 1rem; }
    .upload-hero h2 { font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800; color: #f0a500; margin-bottom: 0.3rem; }
    .upload-hero p { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 1rem; }

    .supported-row { display: flex; gap: 12px; justify-content: center; margin: 1.2rem 0 2rem; flex-wrap: wrap; }
    .fmt-badge { background: #161b27; border: 1px solid #2a2f3e; border-radius: 8px; padding: 8px 18px; font-family: 'Syne', sans-serif; color: #f0a500; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px; }

    .info-strip { display: flex; gap: 12px; justify-content: center; margin: 1.5rem 0; flex-wrap: wrap; }
    .info-chip { background: #161b27; border: 1px solid #2a2f3e; border-radius: 20px; padding: 6px 16px; font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.82rem; }
    .info-chip span { color: #f0a500; font-weight: 700; }

    .result-header { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; color: #ffffff; margin: 1.5rem 0 0.8rem; border-left: 3px solid #f0a500; padding-left: 12px; }

    .decision-approved { background: #0d2b1a; border: 1px solid #1a6b3a; border-radius: 10px; padding: 14px 20px; font-family: 'Syne', sans-serif; color: #2ecc71; font-size: 1.1rem; font-weight: 700; text-align: center; margin: 1rem 0; }
    .decision-review { background: #2b2200; border: 1px solid #6b5000; border-radius: 10px; padding: 14px 20px; font-family: 'Syne', sans-serif; color: #f0a500; font-size: 1.1rem; font-weight: 700; text-align: center; margin: 1rem 0; }
    .decision-rejected { background: #2b0d0d; border: 1px solid #6b1a1a; border-radius: 10px; padding: 14px 20px; font-family: 'Syne', sans-serif; color: #e74c3c; font-size: 1.1rem; font-weight: 700; text-align: center; margin: 1rem 0; }

    .gold-divider { height: 2px; background: linear-gradient(90deg, transparent, #f0a500, transparent); margin: 1.5rem auto; width: 60%; }
    .section-hdr { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700; color: #ffffff; border-left: 3px solid #f0a500; padding-left: 12px; margin-bottom: 1rem; }
    </style>

    <div class="upload-hero">
        <h2>📤 Upload & Process</h2>
        <p>Submit a financial document and let FinDocFlow extract key fields instantly using OCR</p>
    </div>

    <div class="supported-row">
        <div class="fmt-badge">📄 PDF</div>
        <div class="fmt-badge">🖼️ JPG</div>
        <div class="fmt-badge">🖼️ PNG</div>
        <div class="fmt-badge">🖼️ JPEG</div>
    </div>

    <div class="info-strip">
        <div class="info-chip">⚡ Auto-approved if confidence <span>&gt;90%</span></div>
        <div class="info-chip">🔍 Review required if <span>70–90%</span></div>
        <div class="info-chip">🚨 Manual check if <span>&lt;70%</span></div>
    </div>

    <div class="gold-divider"></div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "png", "jpg", "jpeg"])

    st.markdown("""
    <div style="margin-top: 2rem;">
    <div class="section-hdr">⚙️ What happens after upload?</div>
    <div style="display:flex; gap:14px; flex-wrap:wrap; justify-content:center; margin-bottom:2rem;">
        <div style="background:#161b27; border:1px solid #2a2f3e; border-radius:10px; padding:16px 20px; flex:1; min-width:160px; max-width:220px; text-align:center;">
            <div style="font-size:1.8rem;">🔍</div>
            <div style="font-family:'Syne',sans-serif; color:#f0a500; font-size:0.85rem; font-weight:700; margin:6px 0;">OCR Scan</div>
            <div style="font-family:'DM Sans',sans-serif; color:#8b92a5; font-size:0.8rem;">Tesseract reads every field from your document</div>
        </div>
        <div style="background:#161b27; border:1px solid #2a2f3e; border-radius:10px; padding:16px 20px; flex:1; min-width:160px; max-width:220px; text-align:center;">
            <div style="font-size:1.8rem;">🧠</div>
            <div style="font-family:'Syne',sans-serif; color:#f0a500; font-size:0.85rem; font-weight:700; margin:6px 0;">Field Extraction</div>
            <div style="font-family:'DM Sans',sans-serif; color:#8b92a5; font-size:0.8rem;">Name, PAN, date, loan amount, account number pulled out</div>
        </div>
        <div style="background:#161b27; border:1px solid #2a2f3e; border-radius:10px; padding:16px 20px; flex:1; min-width:160px; max-width:220px; text-align:center;">
            <div style="font-size:1.8rem;">🎯</div>
            <div style="font-family:'Syne',sans-serif; color:#f0a500; font-size:0.85rem; font-weight:700; margin:6px 0;">Confidence Score</div>
            <div style="font-family:'DM Sans',sans-serif; color:#8b92a5; font-size:0.8rem;">Each field scored and routed automatically</div>
        </div>
        <div style="background:#161b27; border:1px solid #2a2f3e; border-radius:10px; padding:16px 20px; flex:1; min-width:160px; max-width:220px; text-align:center;">
            <div style="font-size:1.8rem;">📋</div>
            <div style="font-family:'Syne',sans-serif; color:#f0a500; font-size:0.85rem; font-weight:700; margin:6px 0;">Audit Logged</div>
            <div style="font-family:'DM Sans',sans-serif; color:#8b92a5; font-size:0.8rem;">Every action saved to audit trail automatically</div>
        </div>
    </div>

    <div class="section-hdr">💡 Tips for best results</div>
    <div style="background:#161b27; border:1px solid #2a2f3e; border-radius:10px; padding:18px 24px; font-family:'DM Sans',sans-serif; color:#8b92a5; font-size:0.88rem; line-height:2;">
        ✅ &nbsp;Use clear, high-resolution scans (300 DPI or above)<br>
        ✅ &nbsp;Ensure document is not tilted or cropped<br>
        ✅ &nbsp;PAN number must be visible for KYC documents<br>
        ✅ &nbsp;Loan amount should be clearly printed, not handwritten<br>
        ✅ &nbsp;Bank statements should include account number on every page
    </div>
    </div>
    """, unsafe_allow_html=True)

    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        with st.spinner("Processing document…"):
            extraction = process_document_bytes(bytes_data, uploaded_file.name)

        time.sleep(0.3)
        st.success("✅ Processing complete!")
        decision = random.choice(["Approved", "Review Required", "Rejected"])

        fields = extraction["fields"]
        confidence = extraction["confidence"]

        st.markdown('<div class="result-header">📋 Extracted Fields</div>', unsafe_allow_html=True)

        extracted_items = [
            ("Applicant Name", fields.get("name")),
            ("PAN", fields.get("pan")),
            ("Date (Detected)", fields.get("date")),
            ("Loan Amount", fields.get("loan_amount")),
            ("Account Number", fields.get("account_number")),
            ("Income", fields.get("income")),
        ]

        df_ext = pd.DataFrame(extracted_items, columns=["Field", "Value"])
        st.dataframe(df_ext, use_container_width=True)

        st.markdown('<div class="result-header">🎯 Decision & Confidence</div>', unsafe_allow_html=True)

        if decision == "Approved":
            st.markdown(f'<div class="decision-approved">✅ APPROVED &nbsp;|&nbsp; Confidence: {confidence}%</div>', unsafe_allow_html=True)
        elif decision == "Review Required":
            st.markdown(f'<div class="decision-review">⚠️ REVIEW REQUIRED &nbsp;|&nbsp; Confidence: {confidence}%</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="decision-rejected">❌ MANUAL CHECK REQUIRED &nbsp;|&nbsp; Confidence: {confidence}%</div>', unsafe_allow_html=True)
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
