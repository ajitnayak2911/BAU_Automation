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
from . import logic


def run():

    # --- Custom CSS ---
    st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        .stProgress > div > div > div:nth-child(1) {background-color: #4CAF50;}
    </style>
    """, unsafe_allow_html=True)

    st.title("🌐 Automated Tracking link Form Tester")
    st.write("Runs your existing Playwright automation and shows a live per‑URL table.")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Configuration")
        dev_username = st.text_input("DEV Username", value=logic.DEV_USERNAME)
        dev_password = st.text_input("DEV Password", type="password", value=logic.DEV_PASSWORD)
        input_file = st.text_input("Input Excel file path", value=logic.INPUT_FILE)
        output_file = st.text_input("Output Excel file path", value=logic.OUTPUT_FILE)
        headless = st.checkbox("Run headless browser", value=True)
        show_all_logs = st.checkbox("Show full logs", value=True)
        run_btn = st.button("🚀 Run Automation")

    # --- Apply runtime config ---
    logic.DEV_USERNAME = dev_username
    logic.DEV_PASSWORD = dev_password
    logic.INPUT_FILE = input_file
    logic.OUTPUT_FILE = output_file

    # Placeholders
    status_box = st.empty()
    progress_box = st.empty()
    table_box = st.empty()
    log_box = st.empty()

    # Regex patterns
    row_pattern = re.compile(r"Row\s+(\d+)\s*->\s*(\S+)")

    # --- helper to run async main ---
    def run_async_main(log_stream):
        sys.stdout = log_stream
        sys.stderr = log_stream
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(logic.main())
        except Exception:
            traceback.print_exc()
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    # --- Run button pressed ---
    if run_btn:

        if not os.path.exists(input_file):
            st.error(f"❌ Input file not found: {input_file}")
            st.stop()

        start_time = time.time()
        status_box.info("Starting automation... This may take a few minutes.")
        log_stream = StringIO()

        thread = threading.Thread(target=run_async_main, args=(log_stream,), daemon=True)
        thread.start()

        df = pd.DataFrame(columns=["Row", "URL", "Status"])

        while thread.is_alive():
            time.sleep(1)
            logs = log_stream.getvalue()

            if not show_all_logs:
                logs = "\n".join(logs.splitlines()[-100:])

            log_box.markdown(
                f"",
                unsafe_allow_html=True
            )

            for row, url in row_pattern.findall(logs):
                row_i = int(row)
                if row_i not in df["Row"].values:
                    df.loc[len(df)] = [row_i, url, "Running"]

            for i in range(len(df)):
                if f"Row {df.loc[i, 'Row']} ->" in logs and "Captured Response URL" in logs:
                    df.at[i, "Status"] = "Done"

            table_box.dataframe(
                df.sort_values("Row").reset_index(drop=True),
                use_container_width=True,
            )

            processed = len(df)
            if len(df) > 0:
                progress_value = min(processed / max(1, df["Row"].max()), 1.0)
            else:
                progress_value = 0.0

            progress_box.progress(progress_value)
            status_box.info(f"Processing... {processed} URLs so far")

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
