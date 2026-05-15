import streamlit as st
import pandas as pd
import json
import os
from database import create_tables, insert_document, get_all_documents, demo_data, get_connection, DB_PATH
from ocr_engine import process_document_bytes

st.set_page_config(page_title="FinDocFlow", layout="wide")

# Initialize DB and demo data
create_tables()
conn = get_connection()
count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
conn.close()
if count == 0:
    demo_data()

st.title("FinDocFlow – Document Automation Dashboard")
st.markdown("On-premise OCR & document automation for Indian NBFCs")

menu = st.sidebar.radio("Navigation", ["Upload & Process", "Dashboard", "Audit Log"])

# Show project location in the sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Project root**")
st.sidebar.code(os.getcwd())
st.sidebar.markdown("**Database file**")
st.sidebar.code(DB_PATH)

if menu == "Upload & Process":
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose scanned PDF or image files (JPG, PNG, PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("Process Documents"):
            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        result = process_document_bytes(file_bytes, uploaded_file.name)
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {e}")
                        continue

                insert_document(
                    filename=result["filename"],
                    doc_type=result["doc_type"],
                    confidence=result["overall_confidence"],
                    status=result["status"],
                    extracted={
                        "fields": result["extracted_fields"],
                        "confidence_per_field": result["confidence_per_field"],
                    },
                    proc_time=result["processing_time_sec"],
                )

                st.success(f"Processed {uploaded_file.name} – Status: {result['status']}")
                with st.expander("Show details"):
                    st.json(result["extracted_fields"])
                    st.write("Confidence per field:")
                    st.json(result["confidence_per_field"])
                    st.write(f"Overall confidence: {result['overall_confidence']}%")
                    st.write(f"Document type: {result['doc_type']}")
                    st.write(f"Issues: {result['issues']}")

            st.info("All files processed.")

elif menu == "Dashboard":
    st.header("Dashboard Metrics")
    rows = get_all_documents()
    if not rows:
        st.info("No documents processed yet.")
    else:
        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "filename",
                "doc_type",
                "confidence_score",
                "status",
                "extracted_json",
                "upload_time",
                "processing_time_sec",
            ],
        )
        total = len(df)
        auto_count = len(df[df["status"] == "Auto-Approved"])
        review_count = len(df[df["status"] == "Review"])
        manual_count = len(df[df["status"] == "Manual"])
        stp_rate = (auto_count / total * 100) if total else 0.0
        avg_proc_time = df["processing_time_sec"].mean() if total else 0.0
        error_rate = (manual_count / total * 100) if total else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Processed", total)
        col2.metric("STP Rate", f"{stp_rate:.1f}%")
        col3.metric("Avg Processing Time", f"{avg_proc_time:.2f} s")
        col4.metric("Error / Manual Rate", f"{error_rate:.1f}%")

        st.subheader("Document Status")
        status_df = df["status"].value_counts().reset_index()
        status_df.columns = ["Status", "Count"]
        st.bar_chart(status_df.set_index("Status"))

        st.subheader("Document Types")
        type_df = df["doc_type"].value_counts().reset_index()
        type_df.columns = ["Document Type", "Count"]
        st.bar_chart(type_df.set_index("Document Type"))

elif menu == "Audit Log":
    st.header("Audit Trail")
    rows = get_all_documents()
    if not rows:
        st.info("No records yet.")
    else:
        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "filename",
                "doc_type",
                "confidence_score",
                "status",
                "extracted_json",
                "upload_time",
                "processing_time_sec",
            ],
        )

        def parse_extracted(js):
            try:
                return json.dumps(json.loads(js), indent=2)
            except Exception:
                return js

        df["extracted"] = df["extracted_json"].apply(parse_extracted)

        df_display = df[
            [
                "id",
                "filename",
                "doc_type",
                "confidence_score",
                "status",
                "upload_time",
                "processing_time_sec",
            ]
        ].copy()
        df_display["extracted"] = df["extracted"]
        st.dataframe(df_display)

        st.sidebar.markdown("### Filters")
        status_filter = st.sidebar.multiselect(
            "Status",
            options=["Auto-Approved", "Review", "Manual"],
            default=["Auto-Approved", "Review", "Manual"],
        )
        type_filter = st.sidebar.multiselect(
            "Document Type",
            options=df["doc_type"].unique(),
            default=list(df["doc_type"].unique()),
        )
        filtered = df[
            (df["status"].isin(status_filter)) & (df["doc_type"].isin(type_filter))
        ]
        st.write(f"Showing {len(filtered)} records")
        filtered_display = filtered[["id", "filename", "doc_type", "confidence_score", "status", "upload_time", "processing_time_sec"]].copy()
        filtered_display["extracted"] = filtered["extracted"]
        st.dataframe(filtered_display)
