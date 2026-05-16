import sqlite3
import json
from datetime import datetime

DB_PATH = "fincdocflow.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            doc_type TEXT,
            confidence_score REAL,
            status TEXT,
            extracted_json TEXT,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processing_time_sec REAL
        )
        """
    )
    conn.commit()
    conn.close()

def insert_document(filename, doc_type, confidence, status, extracted, proc_time):
    conn = get_connection()
    c = conn.cursor()
    extracted_str = json.dumps(extracted)
    c.execute(
        """
        INSERT INTO documents
            (filename, doc_type, confidence_score, status, extracted_json, processing_time_sec)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (filename, doc_type, confidence, status, extracted_str, proc_time),
    )
    conn.commit()
    doc_id = c.lastrowid
    conn.close()
    return doc_id

def get_all_documents():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents ORDER BY upload_time DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_document_by_id(doc_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = c.fetchone()
    conn.close()
    return row

def demo_data():
    now = datetime.utcnow().isoformat()

    data = [
        {
            "filename": "loan_form_sample.pdf",
            "doc_type": "loan_form",
            "confidence_score": 96.5,
            "status": "Auto-Approved",
            "extracted": {
                "fields": {
                    "name": "Suresh Kumar",
                    "pan": "ABCDE1234F",
                    "date": "15/08/2024",
                    "loan_amount": "500000",
                    "account_number": "123456789012",
                    "income": "1200000",
                    "address": "Chennai"
                },
                "confidence_per_field": {
                    "name": 0.90,
                    "pan": 0.95,
                    "date": 0.95,
                    "loan_amount": 0.90,
                    "account_number": 0.95,
                    "income": 0.90,
                    "address": 0.80
                }
            },
            "processing_time_sec": 1.8,
        },
        {
            "filename": "kyc_doc.jpg",
            "doc_type": "kyc",
            "confidence_score": 87.2,
            "status": "Review",
            "extracted": {
                "fields": {
                    "name": "Priya Sharma",
                    "pan": "BCDEA2345G",
                    "date": "01/01/2020",
                    "loan_amount": None,
                    "account_number": None,
                    "income": None,
                    "address": "Mumbai"
                },
                "confidence_per_field": {
                    "name": 0.90,
                    "pan": 0.95,
                    "date": 0.95,
                    "loan_amount": 0.0,
                    "account_number": 0.0,
                    "income": 0.0,
                    "address": 0.80
                }
            },
            "processing_time_sec": 2.3,
        },
        {
            "filename": "bank_statement.png",
            "doc_type": "bank_statement",
            "confidence_score": 65.0,
            "status": "Manual",
            "extracted": {
                "fields": {
                    "name": None,
                    "pan": None,
                    "date": "31/03/2024",
                    "loan_amount": None,
                    "account_number": "987654321098",
                    "income": None,
                    "address": None
                },
                "confidence_per_field": {
                    "name": 0.0,
                    "pan": 0.0,
                    "date": 0.95,
                    "loan_amount": 0.0,
                    "account_number": 0.95,
                    "income": 0.0,
                    "address": 0.0
                }
            },
            "processing_time_sec": 3.1,
        },
    ]

    for d in data:
        insert_document(
            filename=d["filename"],
            doc_type=d["doc_type"],
            confidence=d["confidence_score"],
            status=d["status"],
            extracted=d["extracted"],
            proc_time=d["processing_time_sec"],
        )
