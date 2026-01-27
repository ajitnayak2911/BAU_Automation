import streamlit as st
import pandas as pd
import subprocess
import tempfile
import os

# --------------------------------------------------
# CONFIG – MUST MATCH YOUR STANDALONE SCRIPT
# --------------------------------------------------
SCRIPT_PATH = "Meta_check.py"
INPUT_FILE = r"C:\Users\nayakaj\PythonCode\input_url_list.xlsx"
OUTPUT_FILE = r"C:\Users\nayakaj\PythonCode\seo_meta_results.xlsx"

# --------------------------------------------------
# STREAMLIT UI
# --------------------------------------------------
st.set_page_config("SEO Meta Tag Checker", layout="wide")
st.title("🔍 SEO Meta Tag Checker")

tab1, tab2 = st.tabs(["🔗 Single URL", "📁 Excel Upload"])

# ---------------- TAB 1: SINGLE URL ----------------
with tab1:
    url = st.text_input("Enter URL", placeholder="https://example.com")

    if st.button("Run Check"):
        if not url.strip():
            st.warning("Please enter a URL")
        else:
            # Create temp Excel input
            df_input = pd.DataFrame({"URL": [url.strip()]})
            df_input.to_excel(INPUT_FILE, index=False)

            with st.spinner("Running Playwright (standalone)..."):
                subprocess.run(
                    ["python", SCRIPT_PATH],
                    check=True
                )

            df_out = pd.read_excel(OUTPUT_FILE)
            st.success("✅ Done")
            st.dataframe(df_out, use_container_width=True)

# ---------------- TAB 2: EXCEL UPLOAD ----------------
with tab2:
    uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

    if uploaded_file:
        df_in = pd.read_excel(uploaded_file)

        if "URL" not in df_in.columns:
            st.error("Excel must contain a column named 'URL'")
        else:
            if st.button("Run Bulk Check"):
                df_in.to_excel(INPUT_FILE, index=False)

                with st.spinner("Running Playwright (standalone)..."):
                    subprocess.run(
                        ["python", SCRIPT_PATH],
                        check=True
                    )

                df_out = pd.read_excel(OUTPUT_FILE)
                st.success("✅ Done")
                st.dataframe(df_out, use_container_width=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    df_out.to_excel(tmp.name, index=False)
                    with open(tmp.name, "rb") as f:
                        st.download_button(
                            "⬇ Download Results Excel",
                            f,
                            "seo_meta_results.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
