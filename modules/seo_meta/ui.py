import streamlit as st
import pandas as pd
import io
from .logic import run_single_url, run_bulk


def run():

    st.title("🔍 SEO Meta Tag Checker")

    tab1, tab2 = st.tabs(["🔗 Single URL", "📁 Excel Upload"])

    # ---------- SINGLE URL ----------
    with tab1:

        url = st.text_input("Enter URL")

        if st.button("Run Check", key="seo_single"):

            if not url.strip():
                st.warning("Please enter a valid URL")
            else:
                with st.spinner("Checking meta tags..."):
                    result = run_single_url(url.strip())

                df = pd.DataFrame([result])

                st.success("✅ Completed")
                st.dataframe(df, use_container_width=True)

    # ---------- BULK ----------
    with tab2:

        uploaded_file = st.file_uploader(
            "Upload Excel (.xlsx)",
            type=["xlsx"]
        )

        if uploaded_file:

            if st.button("Run Bulk Check", key="seo_bulk"):

                with st.spinner("Running bulk meta check..."):
                    df, error = run_bulk(uploaded_file)

                if error:
                    st.error(error)
                else:
                    st.success("✅ Bulk Completed")
                    st.dataframe(df, use_container_width=True)

                    output = io.BytesIO()
                    df.to_excel(output, index=False)

                    st.download_button(
                        "⬇ Download Results Excel",
                        output.getvalue(),
                        "seo_meta_results.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )