# 📄 FinDocFlow

> Intelligent Document Automation for Indian NBFCs

Built for **Sundaram Pitch Fest 2026** — E-Cell IIT Kharagpur  
Team **HAVOC** | C.V. Raman Global University

---

## 🚀 What is FinDocFlow?

FinDocFlow is an on-premise OCR and document automation pipeline that extracts, validates, and routes financial documents automatically — reducing manual processing time by 80% while keeping sensitive data fully within company servers.

---

## ✨ Features

- 📤 **Document Upload** — PDF, JPG, PNG support
- 🔍 **OCR Extraction** — Tesseract-powered field extraction
- 🧠 **Auto Classification** — KYC, Loan Application, Bank Statement, Income Certificate
- 📊 **Confidence Scoring** — Auto-Approved / Review / Manual routing
- 📋 **Audit Trail** — Full history with search and CSV export
- 🔄 **Document Compare** — Side-by-side comparison of any 2 documents
- 📈 **Dashboard** — Real-time metrics and charts

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| OCR Engine | Tesseract OCR + pytesseract |
| Backend | Python |
| Dashboard | Streamlit |
| Database | SQLite |
| Charts | Plotly |
| Deployment | On-premise (Docker-ready) |

---

## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
sudo apt install tesseract-ocr -y

# Run the app
streamlit run app.py
```

Open **http://localhost:8501**

---

## 📁 Project Structure
