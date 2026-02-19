import streamlit as st
import pandas as pd
from .logic import run_dummy_links_single, run_dummy_links_bulk
import io

def run():
    st.title("🔗 Dummy Link Checker")

    tab1, tab2 = st.tabs(["🔗 Single URL", "📁 Excel Upload"])

    # ---------------- TAB 1: Single URL ----------------
    with tab1:
        url = st.text_input(
            "Enter URL",
            placeholder="https://www.example.com"
        )

        if st.button("Run Check", key="single_dummy"):
            if not url.strip():
                st.warning("Please enter a URL")
            else:
                with st.spinner("Checking dummy links..."):
                    result = run_dummy_links_single(url.strip())

                st.success("✅ Done")
                st.text(result)

    # ---------------- TAB 2: Excel Upload ----------------
    with tab2:
        uploaded_file = st.file_uploader(
            "Upload Excel (.xlsx)",
            type=["xlsx"]
        )

        if uploaded_file:
            if st.button("Run Bulk Check", key="bulk_dummy"):
                with st.spinner("Checking dummy links..."):
                    df_out, error = run_dummy_links_bulk(uploaded_file)

                if error:
                    st.error(error)
                else:
                    st.success("✅ Done")
                    st.dataframe(df_out, use_container_width=True)

                    output = io.BytesIO()
                    df_out.to_excel(output, index=False, engine="openpyxl")
                    output.seek(0)

                    st.download_button(
                        "⬇ Download Results",
                        output,
                        "dummy_link_results.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )