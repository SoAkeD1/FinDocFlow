import streamlit as st
import pandas as pd
import plotly.express as px
import time
import random
import io

# -------------------------------
# Page configuration (must be first Streamlit command)
# -------------------------------
st.set_page_config(page_title="FinDocFlow", page_icon="📄", layout="wide")

# -------------------------------
# Custom CSS injection
# -------------------------------
st.markdown(
    """
    <style>
    /* Global background */
    .reportview-container, .main, .block-container {
        background-color: #0f172a;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f8fafc;
        font-size: 2rem;
    }
    /* General helper classes */
    .feature-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        color: #f1f5f9;
    }
    .feature-card h3 {
        color: #3b82f6;
    }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# Session state for navigation
# -------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

# -------------------------------
# Sidebar
# -------------------------------
st.sidebar.markdown(
    "<h1 style='color:#3b82f6; text-align:center;'>📄 FinDocFlow</h1>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='color:#94a3b8; text-align:center; font-size:0.9rem;'>Sundaram Finance</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

menu = ["🏠 Home", "📤 Upload & Process", "📊 Dashboard", "📋 Audit Log"]
menu_map = {
    "🏠 Home": "Home",
    "📤 Upload & Process": "Upload",
    "📊 Dashboard": "Dashboard",
    "📋 Audit Log": "Audit",
}
index = menu.index(
    [k for k, v in menu_map.items() if v == st.session_state.page][0]
)  # find current index

selected = st.sidebar.radio("Navigation", menu, index=index)
st.session_state.page = menu_map[selected]

# -------------------------------
# Sample data
# -------------------------------
def generate_sample_data():
    data = pd.DataFrame(
        {
            "Reference ID": [f"FD-{i:04d}" for i in range(1, 21)],
            "Document Type": [
                "Loan Application",
                "Invoice",
                "KYC",
                "Loan Application",
                "Invoice",
            ]
            * 4,
            "Status": ["Approved", "Review", "Manual", "Approved", "Review"] * 4,
            "Date": pd.date_range("2025-01-01", periods=20, freq="D").strftime(
                "%Y-%m-%d"
            ),
            "Reviewer": ["Alice", "Bob", "Charlie", "Alice", "Bob"] * 4,
        }
    )
    return data


# -------------------------------
# Helper: colored HTML table
# -------------------------------
def colored_table(df):
    color_map_status = {
        "Approved": "#166534",
        "Review": "#854d0e",
        "Manual": "#7f1d1d",
    }
    html = (
        '<table style="width:100%; border-collapse:collapse; color:#f8fafc; font-size:0.9rem;">'
    )
    html += "<thead><tr>"
    for col in df.columns:
        html += f'<th style="background:#1e293b; padding:0.5rem; border:1px solid #334155;">{col}</th>'
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        status = row["Status"]
        row_color = color_map_status.get(status, "#1e293b")
        html += f'<tr style="background:{row_color}; border:1px solid #334155;">'
        for col in df.columns:
            html += f'<td style="padding:0.5rem; border:1px solid #334155;">{row[col]}</td>'
        html += "</tr>"
    html += "</tbody></table>"
    return html


# -------------------------------
# Pages
# -------------------------------
def home_page():
    # Hero section
    st.markdown(
        """
        <div style="text-align:center; padding: 3rem 1rem;">
            <h1 style="color:#f8fafc; font-size:3rem;">Intelligent Document Automation</h1>
            <p style="color:#94a3b8; font-size:1.25rem;">Next‑generation OCR for NBFCs — fast, accurate, on‑premise.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="feature-card"><h3>⚡</h3><h3>80% Faster Processing</h3><p>Cut turnaround time dramatically with AI‑powered extraction.</p></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="feature-card"><h3>🎯</h3><h3>98% Accuracy</h3><p>Industry‑leading OCR accuracy reduces re‑work.</p></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="feature-card"><h3>🔒</h3><h3>100% On‑Premise</h3><p>Your data never leaves your infrastructure.</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='color:#f8fafc; text-align:center;'>How it works</h2>",
        unsafe_allow_html=True,
    )

    steps = [
        ("📤", "Upload", "Upload any document"),
        ("🔍", "OCR", "Extract text & data"),
        ("🧠", "AI Analysis", "Classify & validate"),
        ("✅", "Decision", "Auto‑approve or route"),
        ("📊", "Integration", "Push to core system"),
    ]
    cols = st.columns(5)
    for i, (icon, title, desc) in enumerate(steps):
        with cols[i]:
            st.markdown(
                f"""
                <div style="background:#1e293b; border:1px solid #334155; border-radius:12px; padding:1.2rem; text-align:center;">
                    <div style="font-size:2rem;">{icon}</div>
                    <h4 style="color:#f8fafc; margin:0.5rem 0 0.2rem;">{title}</h4>
                    <p style="color:#94a3b8; font-size:0.85rem;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def upload_page():
    st.markdown(
        "<h2 style='color:#f8fafc;'>📤 Upload & Process</h2>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Choose a document (PDF, JPG, PNG)", type=["pdf", "jpg", "png"]
    )

    if uploaded_file is not None:
        with st.spinner("Processing document…"):
            time.sleep(0.8)
            st.info("Step 1/4: OCR Extraction completed ✅")
            time.sleep(0.6)
            st.info("Step 2/4: Data Parsing completed ✅")
            time.sleep(0.6)
            st.info("Step 3/4: Classification completed ✅")
            time.sleep(0.6)
            st.info("Step 4/4: Verification completed ✅")
            st.success("Processing complete!")

        # Random decision
        decision = random.choices(
            ["Auto-Approved", "Review", "Manual"], weights=[70, 20, 10]
        )[0]
        color_map = {
            "Auto-Approved": "#22c55e",
            "Review": "#eab308",
            "Manual": "#ef4444",
        }
        st.markdown(
            f"""
            <div style="background:{color_map[decision]}; color:white; padding:1rem; border-radius:8px; font-size:1.5rem; text-align:center; margin:1rem 0;">
                ✅ Decision: {decision}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Extracted fields
        st.markdown("<h4 style='color:#f8fafc;'>Extracted Fields</h4>", unsafe_allow_html=True)
        extracted = {
            "Applicant Name": "John Doe",
            "Loan Amount": "₹25,00,000",
            "PAN": "ABCDE1234F",
            "Date of Birth": "01/01/1990",
            "Status": "Active",
            "Document Date": "2025-01-15",
        }
        df_extracted = pd.DataFrame(extracted.items(), columns=["Field", "Value"])
        col_a, col_b = st.columns(2)
        with col_a:
            st.dataframe(df_extracted, use_container_width=True, hide_index=True)
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)  # spacing
            st.markdown(
                "<p style='color:#94a3b8;'>Confidence Score</p>",
                unsafe_allow_html=True,
            )
            st.progress(89, "89%")
            st.caption("High confidence extraction")

        st.markdown("<hr>", unsafe_allow_html=True)


def dashboard_page():
    st.markdown(
        "<h2 style='color:#f8fafc;'>📊 Dashboard</h2>", unsafe_allow_html=True
    )

    # ---------------------------
    # Row 1: Metric cards
    # ---------------------------
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Documents", "12,847", "+234")
    with m2:
        st.metric("STP Rate", "78.5%", "+2.1%")
    with m3:
        st.metric("Avg. Processing Time", "2.3s", "-0.4s")
    with m4:
        st.metric("Error Rate", "0.12%", "-0.03%")

    # ---------------------------
    # Row 2: Charts
    # ---------------------------
    data = generate_sample_data()

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(
            "<h4 style='color:#f8fafc;'>Documents by Status</h4>",
            unsafe_allow_html=True,
        )
        status_counts = data["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_bar = px.bar(
            status_counts,
            x="Status",
            y="Count",
            color="Status",
            color_discrete_map={
                "Approved": "#22c55e",
                "Review": "#eab308",
                "Manual": "#ef4444",
            },
            template="plotly_dark",
        )
        fig_bar.update_layout(showlegend=False, margin=dict(t=0, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.markdown(
            "<h4 style='color:#f8fafc;'>Documents by Type</h4>",
            unsafe_allow_html=True,
        )
        type_counts = data["Document Type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        fig_pie = px.pie(
            type_counts,
            names="Type",
            values="Count",
            color_discrete_sequence=["#3b82f6", "#22c55e", "#eab308"],
            template="plotly_dark",
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(margin=dict(t=0, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    # ---------------------------
    # Row 3: Recent documents table
    # ---------------------------
    st.markdown(
        "<h4 style='color:#f8fafc;'>Recent Documents</h4>",
        unsafe_allow_html=True,
    )
    recent = data.head(10)[["Reference ID", "Document Type", "Status", "Date"]]
    st.markdown(colored_table(recent), unsafe_allow_html=True)


def audit_page():
    st.markdown(
        "<h2 style='color:#f8fafc;'>📋 Audit Log</h2>", unsafe_allow_html=True
    )

    data = generate_sample_data()

    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("🔍 Search by Reference ID or Reviewer", "")
    with col_filter:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Approved", "Review", "Manual"],
            index=0,
        )

    filtered = data.copy()
    if search_term:
        filtered = filtered[
            filtered.apply(
                lambda row: row.astype(str)
                .str.contains(search_term, case=False)
                .any(),
                axis=1,
            )
        ]
    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]

    st.markdown(
        f"<p style='color:#94a3b8;'>Showing {len(filtered)} records</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        colored_table(filtered[["Reference ID", "Document Type", "Status", "Date", "Reviewer"]]),
        unsafe_allow_html=True,
    )

    # Download CSV
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="audit_log.csv",
        mime="text/csv",
    )


# -------------------------------
# Route to active page
# -------------------------------
if st.session_state.page == "Home":
    home_page()
elif st.session_state.page == "Upload":
    upload_page()
elif st.session_state.page == "Dashboard":
    dashboard_page()
elif st.session_state.page == "Audit":
    audit_page()
