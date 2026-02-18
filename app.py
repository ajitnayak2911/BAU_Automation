import streamlit as st
import asyncio
import threading
import time
import sys
from io import StringIO
import os
import re
import pandas as pd
import traceback

# --- Windows asyncio fix ---
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# === import your existing working script ===
import form_automation

# --- Page setup ---
st.set_page_config(page_title="Automated Form Tester", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .block-container {padding-top: 1rem;}
    .stProgress > div > div > div:nth-child(1) {background-color: #4CAF50;}
</style>
""", unsafe_allow_html=True)

st.title("🌐 Automated Tracking link Form Tester")

# ✅ Regex patterns (REQUIRED)
row_pattern = re.compile(r"Row\s+(\d+)\s*->\s*(\S+)")
finish_pattern = re.compile(r"✅ Results saved", re.IGNORECASE)

# ✅ Thread helper (REQUIRED)
def run_async_main(log_stream):
    sys.stdout = log_stream
    sys.stderr = log_stream
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(form_automation.main())
    except Exception:
        traceback.print_exc()
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


tab1, tab2 = st.tabs(["🔁 Manual File Path Mode", "📂 Bulk Upload Mode"])

# =====================================================
# ✅ TAB 1 – MANUAL MODE (ORIGINAL LOGIC PRESERVED)
# =====================================================
with tab1:

    st.write("Runs your existing Playwright automation and shows a live per‑URL table.")

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        dev_username = st.text_input("DEV Username", value=form_automation.DEV_USERNAME)
        dev_password = st.text_input("DEV Password", type="password", value=form_automation.DEV_PASSWORD)
        input_file = st.text_input("Input Excel file path", value=form_automation.INPUT_FILE)
        output_file = st.text_input("Output Excel file path", value=form_automation.OUTPUT_FILE)
        headless = st.checkbox("Run headless browser", value=True)
        show_all_logs = st.checkbox("Show full logs", value=True)
        run_btn = st.button("🚀 Run Automation")

    # Apply runtime config
    form_automation.DEV_USERNAME = dev_username
    form_automation.DEV_PASSWORD = dev_password
    form_automation.INPUT_FILE = input_file
    form_automation.OUTPUT_FILE = output_file

    status_box = st.empty()
    progress_box = st.empty()
    table_box = st.empty()
    log_box = st.empty()

    if run_btn:

        if not os.path.exists(input_file):
            st.error(f"❌ Input file not found: {input_file}")
            st.stop()

        start_time = time.time()
        status_box.info("Starting automation...")
        log_stream = StringIO()

        thread = threading.Thread(target=run_async_main, args=(log_stream,), daemon=True)
        thread.start()

        df = pd.DataFrame(columns=["Row", "URL", "Status"])

        while thread.is_alive():
            time.sleep(1)
            logs = log_stream.getvalue()

            if not show_all_logs:
                logs = "\n".join(logs.splitlines()[-100:])

            log_box.markdown(f"")

            for row, url in row_pattern.findall(logs):
                row_i = int(row)
                if row_i not in df["Row"].values:
                    df.loc[len(df)] = [row_i, url, "Running"]

            for i in range(len(df)):
                if f"Row {df.loc[i, 'Row']} ->" in logs and "Captured Response URL" in logs:
                    df.at[i, "Status"] = "Done"

            table_box.dataframe(df, use_container_width=True)

            if len(df) > 0:
                progress_box.progress(min(len(df)/max(1, df["Row"].max()), 1.0))

            status_box.info(f"Processing... {len(df)} URLs so far")

        thread.join(timeout=2)

        elapsed = round(time.time() - start_time, 1)
        final_logs = log_stream.getvalue()

        st.text_area("📝 Final Logs", final_logs, height=400)
        status_box.success(f"✅ Completed in {elapsed}s! Results saved at: {output_file}")

        if os.path.exists(output_file):
            with open(output_file, "rb") as f:
                st.download_button(
                    "⬇️ Download Results (Excel)",
                    f,
                    file_name=os.path.basename(output_file),
                )


# =====================================================
# ✅ TAB 2 – BULK UPLOAD MODE (SAFE & SEPARATE)
# =====================================================
with tab2:

    st.header("📂 Bulk Upload – Tracking Link Automation")
    st.write("Upload an Excel file instead of entering file path manually.")

    uploaded_file = st.file_uploader(
        "Upload Input Excel File",
        type=["xlsx"],
        key="bulk_upload_mode"
    )

    bulk_run_btn = st.button("🚀 Run Bulk Automation")

    if bulk_run_btn:

        if not uploaded_file:
            st.error("❌ Please upload an Excel file first.")
            st.stop()

        temp_input_path = os.path.join(os.getcwd(), "temp_uploaded_input.xlsx")
        with open(temp_input_path, "wb") as f:
            f.write(uploaded_file.read())

        temp_output_path = os.path.join(os.getcwd(), "temp_bulk_output.xlsx")

        # ✅ FIXED TYPO HERE
        form_automation.INPUT_FILE = temp_input_path
        form_automation.OUTPUT_FILE = temp_output_path

        status_box2 = st.empty()
        log_box2 = st.empty()

        status_box2.info("Starting bulk automation...")

        log_stream = StringIO()

        thread = threading.Thread(target=run_async_main, args=(log_stream,), daemon=True)
        thread.start()

        while thread.is_alive():
            time.sleep(1)
            logs = log_stream.getvalue()
            log_box2.markdown(f"")

        thread.join(timeout=2)

        status_box2.success("✅ Bulk automation completed!")

        if os.path.exists(temp_output_path):
            with open(temp_output_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Bulk Results",
                    f,
                    file_name="bulk_results.xlsx",
                )
