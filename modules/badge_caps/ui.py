import streamlit as st
import pandas as pd
from .logic import run_badge_caps_for_url, run_badge_caps_bulk

def run():
    st.title("Badge Caps Checker")

    tab1, tab2 = st.tabs(["Single URL Check", "Bulk URL Check"])

    # ✅ TAB 1 — SINGLE URL
    with tab1:
        st.subheader("Check Single URL")

        url = st.text_input("Enter URL")

        if st.button("Run Validation", key="single"):
            if not url.strip():
                st.warning("Please enter a valid URL")
            else:
                with st.spinner("Checking badge caps..."):
                    results = run_badge_caps_for_url(url)

                df = pd.DataFrame(results)

                if not df.empty:
                    st.success("Validation Complete ✅")
                    st.dataframe(df)
                else:
                    st.warning("No badges found.")

    # ✅ TAB 2 — BULK CHECK
    with tab2:
        st.subheader("Upload Excel for Bulk Validation")

        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=["xlsx"]
        )

        if uploaded_file is not None:
            if st.button("Run Bulk Validation", key="bulk"):
                with st.spinner("Processing multiple URLs..."):
                    df, error = run_badge_caps_bulk(uploaded_file)

                if error:
                    st.error(error)
                else:
                    st.success("Bulk Validation Complete ✅")
                    st.dataframe(df)

                    # ✅ Download button
                    csv = df.to_csv(index=False).encode("utf-8")

                    st.download_button(
                        label="Download Results as CSV",
                        data=csv,
                        file_name="badge_caps_results.csv",
                        mime="text/csv",
                    )