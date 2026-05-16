import streamlit as st
import pandas as pd
import time
import json
import logging
import plotly.express as px
import database
from database import get_all_documents, get_document_by_id
from ocr_engine import process_document_bytes

logger = logging.getLogger(__name__)

# ---------- Page config ----------
st.set_page_config(page_title="FinDocFlow", layout="wide", page_icon="📄")

# ---------- Ensure DB tables exist ----------
database.create_tables()

# ---------- Global CSS ----------
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

* { box-sizing: border-box; }

.gold-divider { height: 2px; background: linear-gradient(90deg, transparent, #f0a500, transparent); margin: 1.5rem auto; width: 60%; }
.section-title { font-family: 'Syne', sans-serif; font-size: 1.5rem; font-weight: 700; color: #ffffff; margin: 2rem 0 1rem; border-left: 4px solid #f0a500; padding-left: 12px; }
.section-sub  { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.9rem; margin-bottom: 1.2rem; }

/* Hero */
.hero { text-align: center; padding: 3rem 1rem 1.5rem; }
.hero h1 { font-family: 'Syne', sans-serif; font-size: 3.2rem; font-weight: 800; color: #f0a500; margin-bottom: 0.3rem; }
.hero p  { font-family: 'DM Sans', sans-serif; font-size: 1.15rem; color: #ffffff; margin-bottom: 0.4rem; }
.hero small { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.95rem; }

/* Step cards */
.steps-row { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
.step-card  { background: #161b27; border: 1px solid #2a2f3e; border-left: 3px solid #f0a500; border-radius: 12px; padding: 20px; flex: 1; min-width: 180px; max-width: 220px; }
.step-icon  { font-size: 2rem; margin-bottom: 8px; }
.step-num   { font-family: 'Syne', sans-serif; color: #f0a500; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
.step-title { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1rem; font-weight: 700; margin: 4px 0; }
.step-desc  { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.85rem; }

/* Stat boxes */
.stats-row { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
.stat-box  { background: #161b27; border: 1px solid #2a2f3e; border-top: 3px solid #f0a500; border-radius: 12px; padding: 18px 24px; text-align: center; flex: 1; min-width: 160px; }
.stat-val  { font-family: 'Syne', sans-serif; color: #f0a500; font-size: 1rem; font-weight: 700; margin: 4px 0; }
.stat-label{ font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.82rem; }

/* Doc type cards */
.doc-row  { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem; }
.doc-card { background: #161b27; border: 1px solid #2a2f3e; border-radius: 12px; padding: 22px; flex: 1; min-width: 180px; max-width: 260px; transition: border-color .3s, transform .3s; }
.doc-card:hover { border-color: #f0a500; transform: translateY(-4px); }
.doc-icon  { font-size: 2rem; margin-bottom: 8px; }
.doc-title { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 6px; }
.doc-desc  { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.85rem; }

/* CTA */
.cta-banner { background: #161b27; border-left: 4px solid #f0a500; border-radius: 12px; padding: 24px 32px; text-align: center; margin: 1rem 0 2rem; }
.cta-banner h3 { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1.4rem; margin-bottom: 6px; }
.cta-banner p  { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.95rem; }

/* Upload page */
.upload-hero    { text-align: center; padding: 2rem 1rem 1rem; }
.upload-hero h2 { font-family: 'Syne', sans-serif; font-size: 2.2rem; font-weight: 800; color: #f0a500; margin-bottom: 0.3rem; }
.upload-hero p  { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 1rem; }

.supported-row { display: flex; gap: 12px; justify-content: center; margin: 1.2rem 0 2rem; flex-wrap: wrap; }
.fmt-badge { background: #161b27; border: 1px solid #2a2f3e; border-radius: 8px; padding: 8px 18px; font-family: 'Syne', sans-serif; color: #f0a500; font-size: 0.85rem; font-weight: 700; letter-spacing: 1px; }

.info-strip { display: flex; gap: 12px; justify-content: center; margin: 1rem 0 1.5rem; flex-wrap: wrap; }
.info-chip  { background: #161b27; border: 1px solid #2a2f3e; border-radius: 20px; padding: 6px 16px; font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.82rem; }
.info-chip span { color: #f0a500; font-weight: 700; }

/* Decision banners */
.decision-approved { background: #0d2b1a; border: 1px solid #1a6b3a; border-radius: 10px; padding: 14px 20px; font-family: 'Syne', sans-serif; color: #2ecc71; font-size: 1.1rem; font-weight: 700; text-align: center; margin: 1rem 0; }
.decision-review   { background: #2b2200; border: 1px solid #6b5000; border-radius: 10px; padding: 14px 20px; font-family: 'Syne', sans-serif; color: #f0a500; font-size: 1.1rem; font-weight: 700; text-align: center; margin: 1rem 0; }
.decision-rejected { background: #2b0d0d; border: 1px solid #6b1a1a; border-radius: 10px; padding: 14px 20px; font-family: 'Syne', sans-serif; color: #e74c3c; font-size: 1.1rem; font-weight: 700; text-align: center; margin: 1rem 0; }

/* Dynamic fields table */
.dynamic-table { width: 100%; border-collapse: collapse; font-family: 'DM Sans', sans-serif; font-size: 0.9rem; margin-bottom: 1.5rem; }
.dynamic-table th { background: #1e2435; color: #f0a500; font-family: 'Syne', sans-serif; font-size: 0.85rem; text-align: left; padding: 10px 14px; border-bottom: 2px solid #f0a500; }
.dynamic-table td { padding: 9px 14px; border-bottom: 1px solid #2a2f3e; color: #ffffff; vertical-align: top; }
.dynamic-table tr:hover td { background: #161b27; }
.dynamic-table td:first-child { color: #8b92a5; width: 40%; }

/* Keyword chips */
.kw-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 0.5rem 0 1.5rem; }
.kw-chip { background: #1e2435; border: 1px solid #f0a500; border-radius: 20px; padding: 4px 12px; font-family: 'DM Sans', sans-serif; color: #f0a500; font-size: 0.78rem; }

/* Doc type badge */
.doc-type-badge { display: inline-block; background: #1e2435; border: 1px solid #f0a500; border-radius: 8px; padding: 6px 18px; font-family: 'Syne', sans-serif; color: #f0a500; font-size: 0.95rem; font-weight: 700; margin-bottom: 1rem; }

/* Dashboard */
.dash-metric { background: #161b27; border: 1px solid #2a2f3e; border-top: 3px solid #f0a500; border-radius: 12px; padding: 18px 24px; text-align: center; }
.dash-metric .val   { font-family: 'Syne', sans-serif; color: #f0a500; font-size: 1.8rem; font-weight: 800; }
.dash-metric .label { font-family: 'DM Sans', sans-serif; color: #8b92a5; font-size: 0.85rem; margin-top: 4px; }
</style>
"""


# ═══════════════════════════════════════════════════════
#  PAGE: HOME
# ═══════════════════════════════════════════════════════
def home_page():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="hero">
        <h1>FinDocFlow</h1>
        <p>AI-Powered Document Intelligence for Indian NBFCs</p>
        <small>From scanned paper to structured data in seconds — no manual entry, no errors.</small>
    </div>
    <div class="gold-divider"></div>

    <div class="section-title">How It Works</div>
    <div class="steps-row">
        <div class="step-card"><div class="step-icon">📤</div><div class="step-num">Step 1</div><div class="step-title">Upload Document</div><div class="step-desc">Submit PDF, JPG or PNG from any device</div></div>
        <div class="step-card"><div class="step-icon">🔍</div><div class="step-num">Step 2</div><div class="step-title">OCR Extraction</div><div class="step-desc">Tesseract reads every field intelligently</div></div>
        <div class="step-card"><div class="step-icon">🎯</div><div class="step-num">Step 3</div><div class="step-title">Smart Classification</div><div class="step-desc">14 document types, 500+ keywords detected</div></div>
        <div class="step-card"><div class="step-icon">📋</div><div class="step-num">Step 4</div><div class="step-title">Audit & Export</div><div class="step-desc">Full audit trail logged, PDF reports generated</div></div>
    </div>

    <div class="section-title">By The Numbers</div>
    <div class="stats-row">
        <div class="stat-box"><div style="font-size:1.5rem">⚡</div><div class="stat-val">Auto-Approved</div><div class="stat-label">&gt;90% Confidence</div></div>
        <div class="stat-box"><div style="font-size:1.5rem">🏦</div><div class="stat-val">14 Doc Types</div><div class="stat-label">KYC · Loan · Bank · Tax · Medical & more</div></div>
        <div class="stat-box"><div style="font-size:1.5rem">🔑</div><div class="stat-val">500+ Keywords</div><div class="stat-label">Deep field recognition</div></div>
        <div class="stat-box"><div style="font-size:1.5rem">🔒</div><div class="stat-val">Audit Trail</div><div class="stat-label">Every action logged</div></div>
    </div>

    <div class="section-title">What FinDocFlow Processes</div>
    <div class="doc-row">
        <div class="doc-card"><div class="doc-icon">🪪</div><div class="doc-title">KYC Documents</div><div class="doc-desc">Aadhaar, PAN, Voter ID — name, DOB, ID numbers</div></div>
        <div class="doc-card"><div class="doc-icon">📝</div><div class="doc-title">Loan Applications</div><div class="doc-desc">Loan amount, EMI, tenure, co-applicant details</div></div>
        <div class="doc-card"><div class="doc-icon">🏦</div><div class="doc-title">Bank Statements</div><div class="doc-desc">Account number, IFSC, balances, transactions</div></div>
        <div class="doc-card"><div class="doc-icon">💰</div><div class="doc-title">Income Certificates</div><div class="doc-desc">Salary, CTC, deductions, employer details</div></div>
        <div class="doc-card"><div class="doc-icon">🏠</div><div class="doc-title">Property Documents</div><div class="doc-desc">Sale deed, stamp duty, registration details</div></div>
        <div class="doc-card"><div class="doc-icon">🚗</div><div class="doc-title">Vehicle Documents</div><div class="doc-desc">RC, chassis, engine number, insurance validity</div></div>
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


# ═══════════════════════════════════════════════════════
#  PAGE: UPLOAD & PROCESS
# ═══════════════════════════════════════════════════════
def upload_page():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-hero">
        <h2>📤 Upload & Process</h2>
        <p>Submit any financial document — FinDocFlow extracts every relevant field automatically</p>
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

    # Tips panel
    st.markdown("""
    <div style="margin-top:1.5rem;">
    <div class="section-title" style="font-size:1rem;">⚙️ What happens after upload?</div>
    <div style="display:flex; gap:14px; flex-wrap:wrap; justify-content:center; margin-bottom:1.5rem;">
        <div style="background:#161b27;border:1px solid #2a2f3e;border-radius:10px;padding:16px 20px;flex:1;min-width:140px;max-width:200px;text-align:center;">
            <div style="font-size:1.8rem;">🔍</div>
            <div style="font-family:'Syne',sans-serif;color:#f0a500;font-size:0.85rem;font-weight:700;margin:6px 0;">OCR Scan</div>
            <div style="font-family:'DM Sans',sans-serif;color:#8b92a5;font-size:0.8rem;">Tesseract reads every field from your document</div>
        </div>
        <div style="background:#161b27;border:1px solid #2a2f3e;border-radius:10px;padding:16px 20px;flex:1;min-width:140px;max-width:200px;text-align:center;">
            <div style="font-size:1.8rem;">🧠</div>
            <div style="font-family:'Syne',sans-serif;color:#f0a500;font-size:0.85rem;font-weight:700;margin:6px 0;">Classification</div>
            <div style="font-family:'DM Sans',sans-serif;color:#8b92a5;font-size:0.8rem;">14 document types, 500+ keywords matched</div>
        </div>
        <div style="background:#161b27;border:1px solid #2a2f3e;border-radius:10px;padding:16px 20px;flex:1;min-width:140px;max-width:200px;text-align:center;">
            <div style="font-size:1.8rem;">📊</div>
            <div style="font-family:'Syne',sans-serif;color:#f0a500;font-size:0.85rem;font-weight:700;margin:6px 0;">Smart Extraction</div>
            <div style="font-family:'DM Sans',sans-serif;color:#8b92a5;font-size:0.8rem;">Fields extracted specific to the document type</div>
        </div>
        <div style="background:#161b27;border:1px solid #2a2f3e;border-radius:10px;padding:16px 20px;flex:1;min-width:140px;max-width:200px;text-align:center;">
            <div style="font-size:1.8rem;">📋</div>
            <div style="font-family:'Syne',sans-serif;color:#f0a500;font-size:0.85rem;font-weight:700;margin:6px 0;">Audit Logged</div>
            <div style="font-family:'DM Sans',sans-serif;color:#8b92a5;font-size:0.8rem;">Every action saved automatically</div>
        </div>
    </div>
    <div class="section-title" style="font-size:1rem;">💡 Tips for best results</div>
    <div style="background:#161b27;border:1px solid #2a2f3e;border-radius:10px;padding:18px 24px;font-family:'DM Sans',sans-serif;color:#8b92a5;font-size:0.88rem;line-height:2.2;">
        ✅ &nbsp;Use clear, high-resolution scans (300 DPI or above)<br>
        ✅ &nbsp;Ensure document is not tilted or cropped<br>
        ✅ &nbsp;PAN number must be visible for KYC documents<br>
        ✅ &nbsp;Loan amount should be clearly printed, not handwritten<br>
        ✅ &nbsp;Bank statements should include account number on every page
    </div>
    </div>
    """, unsafe_allow_html=True)

    if uploaded_file is None:
        return

    bytes_data = uploaded_file.getvalue()

    with st.spinner("🔍 Processing document…"):
        result = process_document_bytes(bytes_data, uploaded_file.name)

    st.success("✅ Processing complete!")

    # ── Document Type Badge ──────────────────────────
    doc_type   = result.get('doc_type', 'Unknown Document')
    confidence = result.get('confidence', 0)

    st.markdown(f'<div class="doc-type-badge">📁 Document Type: {doc_type}</div>', unsafe_allow_html=True)

    # ── Matched Keywords ─────────────────────────────
    matched = result.get('matched_keywords', [])
    if matched:
        st.markdown('<div class="section-title" style="font-size:1rem;">🔑 Matched Keywords</div>', unsafe_allow_html=True)
        chips = ''.join(f'<span class="kw-chip">{kw}</span>' for kw in sorted(matched))
        st.markdown(f'<div class="kw-row">{chips}</div>', unsafe_allow_html=True)

    # ── Document-Specific Fields ─────────────────────
    dynamic = result.get('dynamic_fields', {})
    if dynamic:
        st.markdown('<div class="section-title">📋 Extracted Fields</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Fields extracted based on document type</div>', unsafe_allow_html=True)

        rows_html = ''
        for field, value in dynamic.items():
            rows_html += f'<tr><td>{field}</td><td>{value}</td></tr>'

        st.markdown(f"""
        <table class="dynamic-table">
            <thead><tr><th>Field</th><th>Extracted Value</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)
    else:
        # Fallback to legacy 6 fields
        st.markdown('<div class="section-title">📋 Extracted Fields</div>', unsafe_allow_html=True)
        extracted_items = [
            ("Applicant Name",  result.get("name")),
            ("PAN",             result.get("pan")),
            ("Date (Detected)", result.get("date")),
            ("Loan Amount",     result.get("loan_amount")),
            ("Account Number",  result.get("account_number")),
            ("Income",          result.get("income")),
        ]
        df_ext = pd.DataFrame(extracted_items, columns=["Field", "Value"])
        st.dataframe(df_ext, use_container_width=True)

    # ── Decision & Confidence ────────────────────────
    st.markdown('<div class="section-title">🎯 Decision & Confidence</div>', unsafe_allow_html=True)

    if confidence >= 90:
        decision_label = "AUTO-APPROVED"
        st.markdown(f'<div class="decision-approved">✅ {decision_label} &nbsp;|&nbsp; Confidence: {confidence}%</div>', unsafe_allow_html=True)
    elif confidence >= 70:
        decision_label = "REVIEW REQUIRED"
        st.markdown(f'<div class="decision-review">⚠️ {decision_label} &nbsp;|&nbsp; Confidence: {confidence}%</div>', unsafe_allow_html=True)
    else:
        decision_label = "MANUAL CHECK REQUIRED"
        st.markdown(f'<div class="decision-rejected">❌ {decision_label} &nbsp;|&nbsp; Confidence: {confidence}%</div>', unsafe_allow_html=True)

    # ── Raw OCR Text (collapsible) ───────────────────
    with st.expander("🔤 View Raw OCR Text"):
        st.text(result.get('text', ''))

    # ── Save to DB ───────────────────────────────────
    try:
        extracted_json = json.dumps({
            "dynamic_fields": dynamic,
            "fields": {
                "name":           result.get("name"),
                "pan":            result.get("pan"),
                "date":           result.get("date"),
                "loan_amount":    result.get("loan_amount"),
                "account_number": result.get("account_number"),
                "income":         result.get("income"),
            }
        })
        database.insert_document(
            filename=uploaded_file.name,
            doc_type=doc_type,
            confidence_score=confidence,
            status=decision_label,
            extracted_json=extracted_json,
        )
    except Exception as e:
        logger.warning(f"DB insert skipped: {e}")


# ═══════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════
def dashboard_page():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-hero">
        <h2>📊 Dashboard</h2>
        <p>Real-time overview of all processed documents</p>
    </div>
    <div class="gold-divider"></div>
    """, unsafe_allow_html=True)

    rows = get_all_documents()
    if not rows:
        st.warning("No documents processed yet. Go to **Upload & Process** to add data.")
        return

    df = pd.DataFrame(rows, columns=rows[0].keys())

    total_docs = len(df)
    avg_conf   = df["confidence_score"].mean()
    approved   = int(df["status"].str.contains("APPROVED", case=False).sum())
    review     = int(df["status"].str.contains("REVIEW", case=False).sum())

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="dash-metric"><div class="val">{total_docs}</div><div class="label">Total Documents</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="dash-metric"><div class="val">{avg_conf:.1f}%</div><div class="label">Avg Confidence</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="dash-metric"><div class="val">{approved}</div><div class="label">Auto-Approved</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="dash-metric"><div class="val">{review}</div><div class="label">Pending Review</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-title" style="font-size:1rem;">Documents by Type</div>', unsafe_allow_html=True)
        type_counts = df["doc_type"].value_counts().reset_index()
        type_counts.columns = ["doc_type", "count"]
        fig_bar = px.bar(type_counts, x="doc_type", y="count", color="doc_type",
                         labels={"doc_type": "Type", "count": "Count"},
                         color_discrete_sequence=px.colors.qualitative.Bold,
                         template="plotly_dark")
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with right:
        st.markdown('<div class="section-title" style="font-size:1rem;">Documents by Status</div>', unsafe_allow_html=True)
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig_pie = px.pie(status_counts, names="status", values="count", hole=0.45,
                         color_discrete_sequence=["#2ecc71", "#f0a500", "#e74c3c"],
                         template="plotly_dark")
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown('<div class="section-title" style="font-size:1rem;">Confidence Distribution</div>', unsafe_allow_html=True)
    fig_hist = px.histogram(df, x="confidence_score", nbins=20,
                            labels={"confidence_score": "Confidence %"},
                            color_discrete_sequence=["#f0a500"],
                            template="plotly_dark")
    fig_hist.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown('<div class="section-title" style="font-size:1rem;">Last 10 Documents</div>', unsafe_allow_html=True)
    st.dataframe(df.head(10), use_container_width=True)


# ═══════════════════════════════════════════════════════
#  PAGE: AUDIT LOG
# ═══════════════════════════════════════════════════════
def audit_page():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-hero">
        <h2>📋 Audit Log</h2>
        <p>Complete history of every document processed by FinDocFlow</p>
    </div>
    <div class="gold-divider"></div>
    """, unsafe_allow_html=True)

    rows = get_all_documents()
    if not rows:
        st.info("No audit records yet. Process documents to populate the log.")
        return

    df = pd.DataFrame(rows, columns=rows[0].keys())

    search_term = st.text_input("🔍 Search by filename or document type")
    if search_term:
        mask = (
            df["filename"].str.contains(search_term, case=False, na=False) |
            df["doc_type"].str.contains(search_term, case=False, na=False)
        )
        df = df[mask]

    st.markdown(f"**{len(df)} record(s) found**")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv, file_name="audit_log.csv", mime="text/csv")

    st.markdown('<div class="section-title" style="font-size:1rem;">Compare Two Documents</div>', unsafe_allow_html=True)

    doc_ids    = [r["id"] for r in rows if r["id"]]
    doc_labels = {r["id"]: f"{r['id']} – {r['filename']}" for r in rows if r["id"]}

    if len(doc_ids) < 2:
        st.info("Need at least two documents to compare.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        sel_a = st.selectbox("Document A", doc_ids, format_func=lambda x: doc_labels.get(x, str(x)))
    with col_b:
        sel_b = st.selectbox("Document B", doc_ids, format_func=lambda x: doc_labels.get(x, str(x)))

    if sel_a and sel_b:
        doc_a = get_document_by_id(sel_a)
        doc_b = get_document_by_id(sel_b)
        if doc_a and doc_b:
            a_data = json.loads(doc_a["extracted_json"]) if doc_a["extracted_json"] else {}
            b_data = json.loads(doc_b["extracted_json"]) if doc_b["extracted_json"] else {}

            a_fields = {**a_data.get("dynamic_fields", {}), **a_data.get("fields", {})}
            b_fields = {**b_data.get("dynamic_fields", {}), **b_data.get("fields", {})}

            all_keys = sorted(set(list(a_fields.keys()) + list(b_fields.keys())))
            comp_data = [{"Field": k, f"Doc {sel_a}": a_fields.get(k, "—"), f"Doc {sel_b}": b_fields.get(k, "—")} for k in all_keys]
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True)
        else:
            st.error("Could not load selected documents.")


# ═══════════════════════════════════════════════════════
#  SIDEBAR + ROUTING
# ═══════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state.page = "Home"

with st.sidebar:
    st.markdown("# 📄 FinDocFlow")
    st.markdown("**Sundaram Finance · HAVOC Team**")
    st.divider()
    if st.button("🏠 Home",             use_container_width=True): st.session_state.page = "Home";      st.rerun()
    if st.button("📤 Upload & Process", use_container_width=True): st.session_state.page = "Upload";    st.rerun()
    if st.button("📊 Dashboard",        use_container_width=True): st.session_state.page = "Dashboard"; st.rerun()
    if st.button("📋 Audit Log",        use_container_width=True): st.session_state.page = "Audit";     st.rerun()
    st.divider()
    st.markdown('<div style="font-family:DM Sans,sans-serif;color:#8b92a5;font-size:0.78rem;">C.V. Raman Global University<br>Bhubaneswar · 2026</div>', unsafe_allow_html=True)

page = st.session_state.page
if   page == "Home":      home_page()
elif page == "Upload":    upload_page()
elif page == "Dashboard": dashboard_page()
elif page == "Audit":     audit_page()
else:                     home_page()