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
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800;900&family=DM+Sans:wght@400;500&display=swap');

    .fdf-nav { display: flex; justify-content: space-between; align-items: center; padding: 18px 48px; background: rgba(10,5,30,0.95); border-bottom: 1px solid rgba(255,255,255,0.08); margin: -1rem -1rem 0 -1rem; backdrop-filter: blur(10px); }
    .fdf-logo { font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
    .fdf-logo span { color: #a78bfa; }
    .fdf-nav-links { display: flex; gap: 32px; font-family: 'DM Sans', sans-serif; font-size: 0.95rem; color: rgba(255,255,255,0.7); }

    .fdf-hero {
        background:
            radial-gradient(ellipse at 20% 50%, rgba(109,40,217,0.4) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(139,92,246,0.3) 0%, transparent 50%),
            radial-gradient(ellipse at 60% 80%, rgba(76,29,149,0.35) 0%, transparent 50%),
            linear-gradient(180deg, #0a051e 0%, #150a35 50%, #0d0520 100%);
        min-height: 560px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 80px 48px 60px;
        margin: 0 -1rem;
        position: relative;
        overflow: hidden;
    }
    .fdf-hero::before {
        content: '';
        position: absolute;
        inset: 0;
        background-image:
            radial-gradient(circle at 1px 1px, rgba(167,139,250,0.15) 1px, transparent 0);
        background-size: 40px 40px;
        pointer-events: none;
    }
    .fdf-hero::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        right: 0;
        height: 120px;
        background: linear-gradient(to bottom, transparent, #0a051e);
        pointer-events: none;
    }

    .fdf-floating-docs {
        position: absolute;
        inset: 0;
        pointer-events: none;
        overflow: hidden;
    }
    .fdf-doc-float {
        position: absolute;
        background: rgba(139,92,246,0.08);
        border: 1px solid rgba(167,139,250,0.15);
        border-radius: 8px;
        backdrop-filter: blur(4px);
    }
    .fdf-doc-float:nth-child(1) { width: 80px; height: 100px; top: 15%; left: 8%; transform: rotate(-12deg); animation: floatDoc 6s ease-in-out infinite; }
    .fdf-doc-float:nth-child(2) { width: 60px; height: 80px; top: 25%; right: 10%; transform: rotate(8deg); animation: floatDoc 8s ease-in-out infinite 1s; }
    .fdf-doc-float:nth-child(3) { width: 70px; height: 90px; bottom: 20%; left: 12%; transform: rotate(5deg); animation: floatDoc 7s ease-in-out infinite 2s; }
    .fdf-doc-float:nth-child(4) { width: 50px; height: 65px; bottom: 25%; right: 8%; transform: rotate(-8deg); animation: floatDoc 9s ease-in-out infinite 0.5s; }
    .fdf-doc-float:nth-child(5) { width: 90px; height: 110px; top: 50%; left: 3%; transform: rotate(15deg); animation: floatDoc 7s ease-in-out infinite 3s; }
    .fdf-doc-float:nth-child(6) { width: 65px; height: 85px; top: 10%; right: 22%; transform: rotate(-5deg); animation: floatDoc 10s ease-in-out infinite 1.5s; }

    @keyframes floatDoc {
        0%, 100% { transform: translateY(0px) rotate(var(--r, -12deg)); opacity: 0.6; }
        50% { transform: translateY(-15px) rotate(var(--r, -12deg)); opacity: 1; }
    }

    .fdf-scan-line {
        position: absolute;
        left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(167,139,250,0.6), transparent);
        animation: scanLine 4s linear infinite;
        pointer-events: none;
    }
    @keyframes scanLine {
        0% { top: 10%; opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { top: 90%; opacity: 0; }
    }

    .fdf-badge { display: inline-block; border: 1px solid rgba(167,139,250,0.4); border-radius: 999px; padding: 6px 20px; font-family: 'DM Sans', sans-serif; font-size: 0.85rem; color: #c4b5fd; margin-bottom: 28px; background: rgba(139,92,246,0.12); position: relative; z-index: 2; }

    .fdf-hero h1 { font-family: 'Syne', sans-serif; font-size: 4.2rem; font-weight: 900; color: #ffffff; line-height: 1.05; margin: 0 0 4px; letter-spacing: -2px; position: relative; z-index: 2; }
    .fdf-hero h1 span { background: linear-gradient(135deg, #c4b5fd 0%, #a78bfa 50%, #7c3aed 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; display: block; }
    .fdf-hero p { font-family: 'DM Sans', sans-serif; font-size: 1.05rem; color: rgba(255,255,255,0.6); max-width: 520px; margin: 20px auto 36px; line-height: 1.7; position: relative; z-index: 2; }

    .fdf-trust { background: rgba(10,5,30,0.9); border-top: 1px solid rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.06); padding: 16px 48px; text-align: center; font-family: 'DM Sans', sans-serif; font-size: 0.88rem; color: rgba(255,255,255,0.4); margin: 0 -1rem; letter-spacing: 0.5px; }
    .fdf-trust span { color: #a78bfa; margin: 0 8px; }

    .fdf-section { background: #0a051e; padding: 64px 48px; margin: 0 -1rem; }
    .fdf-section-title { font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800; color: #ffffff; text-align: center; margin-bottom: 40px; }
    .fdf-section-title span { color: #a78bfa; }

    .fdf-steps { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; margin-bottom: 64px; }
    .fdf-step { background: rgba(139,92,246,0.06); border: 1px solid rgba(167,139,250,0.15); border-left: 3px solid #7c3aed; border-radius: 12px; padding: 24px 20px; flex: 1; min-width: 180px; max-width: 230px; transition: border-color 0.3s, transform 0.3s; }
    .fdf-step:hover { border-color: rgba(167,139,250,0.5); transform: translateY(-4px); }
    .fdf-step-icon { font-size: 2rem; margin-bottom: 10px; }
    .fdf-step-num { font-family: 'Syne', sans-serif; color: #a78bfa; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
    .fdf-step-title { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1rem; font-weight: 700; margin: 6px 0 4px; }
    .fdf-step-desc { font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.5); font-size: 0.82rem; line-height: 1.5; }

    .fdf-stats { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; margin-bottom: 64px; }
    .fdf-stat { background: rgba(139,92,246,0.06); border: 1px solid rgba(167,139,250,0.15); border-top: 3px solid #7c3aed; border-radius: 12px; padding: 24px 28px; flex: 1; min-width: 160px; text-align: center; }
    .fdf-stat-icon { font-size: 1.6rem; margin-bottom: 8px; }
    .fdf-stat-val { font-family: 'Syne', sans-serif; color: #c4b5fd; font-size: 1rem; font-weight: 700; }
    .fdf-stat-label { font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.4); font-size: 0.8rem; margin-top: 4px; }

    .fdf-docs { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; margin-bottom: 64px; }
    .fdf-doc { background: rgba(139,92,246,0.06); border: 1px solid rgba(167,139,250,0.12); border-radius: 12px; padding: 28px 24px; flex: 1; min-width: 200px; max-width: 280px; transition: border-color 0.3s, transform 0.3s; }
    .fdf-doc:hover { border-color: rgba(167,139,250,0.5); transform: translateY(-4px); }
    .fdf-doc-icon { font-size: 2rem; margin-bottom: 10px; }
    .fdf-doc-title { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
    .fdf-doc-desc { font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.45); font-size: 0.83rem; line-height: 1.5; }

    .fdf-cta { background: linear-gradient(135deg, rgba(109,40,217,0.2), rgba(139,92,246,0.1)); border: 1px solid rgba(167,139,250,0.25); border-radius: 16px; padding: 48px; text-align: center; margin: 0 auto; max-width: 700px; }
    .fdf-cta h3 { font-family: 'Syne', sans-serif; color: #ffffff; font-size: 1.6rem; font-weight: 800; margin-bottom: 8px; }
    .fdf-cta p { font-family: 'DM Sans', sans-serif; color: rgba(255,255,255,0.5); font-size: 0.95rem; margin-bottom: 0; }
    </style>

    <div class="fdf-nav"><div class="fdf-logo">Fin<span>Doc</span>Flow</div></div>

    <div class="fdf-hero">
        <div class="fdf-floating-docs">
            <div class="fdf-doc-float"></div>
            <div class="fdf-doc-float"></div>
            <div class="fdf-doc-float"></div>
            <div class="fdf-doc-float"></div>
            <div class="fdf-doc-float"></div>
            <div class="fdf-doc-float"></div>
        </div>
        <div class="fdf-scan-line"></div>
        <div class="fdf-badge">🏆 Sundaram Pitch Fest 2026 — IIT Kharagpur</div>
        <h1>Automate Your<span>Document Back-Office</span></h1>
        <p>AI-powered OCR that reads, classifies and routes financial documents for Indian NBFCs — zero manual entry.</p>
    </div>

    <div class="fdf-trust">Processes: KYC <span>•</span> Loan Applications <span>•</span> Bank Statements <span>•</span> Income Certificates</div>

    <div class="fdf-section">
    <div class="fdf-section-title">How It <span>Works</span></div>
    <div class="fdf-steps">
        <div class="fdf-step"><div class="fdf-step-icon">📤</div><div class="fdf-step-num">Step 01</div><div class="fdf-step-title">Upload</div><div class="fdf-step-desc">PDF, JPG or PNG from any device</div></div>
        <div class="fdf-step"><div class="fdf-step-icon">🔍</div><div class="fdf-step-num">Step 02</div><div class="fdf-step-title">OCR Scan</div><div class="fdf-step-desc">Tesseract extracts name, PAN, date, amounts</div></div>
        <div class="fdf-step"><div class="fdf-step-icon">🎯</div><div class="fdf-step-num">Step 03</div><div class="fdf-step-title">Score and Route</div><div class="fdf-step-desc">Confidence scored 0-100%, auto-routed instantly</div></div>
        <div class="fdf-step"><div class="fdf-step-icon">📋</div><div class="fdf-step-num">Step 04</div><div class="fdf-step-title">Audit and Export</div><div class="fdf-step-desc">Logged, exportable, PDF report ready</div></div>
    </div>
    <div class="fdf-section-title">By The <span>Numbers</span></div>
    <div class="fdf-stats">
        <div class="fdf-stat"><div class="fdf-stat-icon">⚡</div><div class="fdf-stat-val">Auto-Approved</div><div class="fdf-stat-label">&gt;90% Confidence</div></div>
        <div class="fdf-stat"><div class="fdf-stat-icon">🏦</div><div class="fdf-stat-val">4 Doc Types</div><div class="fdf-stat-label">KYC · Loan · Bank · Income</div></div>
        <div class="fdf-stat"><div class="fdf-stat-icon">🔒</div><div class="fdf-stat-val">Audit Trail</div><div class="fdf-stat-label">Every action logged</div></div>
        <div class="fdf-stat"><div class="fdf-stat-icon">📄</div><div class="fdf-stat-val">PDF Export</div><div class="fdf-stat-label">Reports on demand</div></div>
    </div>
    <div class="fdf-section-title">What FinDocFlow <span>Processes</span></div>
    <div class="fdf-docs">
        <div class="fdf-doc"><div class="fdf-doc-icon">🪪</div><div class="fdf-doc-title">KYC Documents</div><div class="fdf-doc-desc">Aadhaar, PAN, Voter ID — extract name, DOB, ID numbers instantly</div></div>
        <div class="fdf-doc"><div class="fdf-doc-icon">📝</div><div class="fdf-doc-title">Loan Applications</div><div class="fdf-doc-desc">Capture applicant name, loan amount, date, co-applicant details</div></div>
        <div class="fdf-doc"><div class="fdf-doc-icon">🏦</div><div class="fdf-doc-title">Bank Statements</div><div class="fdf-doc-desc">Parse account number, transactions, income patterns</div></div>
        <div class="fdf-doc"><div class="fdf-doc-icon">💰</div><div class="fdf-doc-title">Income Certificates</div><div class="fdf-doc-desc">Salary slips, ITR, Form 16 — verify income automatically</div></div>
    </div>
    <div class="fdf-cta"><h3>Ready to digitise your NBFC back-office?</h3><p>Upload your first document and see FinDocFlow extract fields in seconds.</p></div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("📤 Upload a Document", use_container_width=True):
            st.session_state.page = "Upload"
            st.rerun()
    with col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.rerun()
    with col3:
        if st.button("📋 Audit Log", use_container_width=True):
            st.session_state.page = "Audit"
            st.rerun()


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