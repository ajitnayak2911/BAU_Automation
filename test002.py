import os
import time
import asyncio
import sys
import pandas as pd
import streamlit as st
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from io import BytesIO


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# -----------------------------------------------------
# 1️⃣  Load credentials
# -----------------------------------------------------
load_dotenv()
USERNAME = os.getenv("DEV_USERNAME")
PASSWORD = os.getenv("DEV_PASSWORD")

# -----------------------------------------------------
# 2️⃣  Keywords to look for
# -----------------------------------------------------
KEYWORDS = [
    "this site is protected by recaptcha",
    "privacy policy",
    "terms of service",
]

# -----------------------------------------------------
# 3️⃣  Worker function (UNCHANGED LOGIC)
# -----------------------------------------------------
async def validate_single(context, url: str):

    if not url or not isinstance(url, str) or not url.strip():
        return {
            "Validation Result": "Invalid URL",
            "HTTP Status": None,
            "Load Time (s)": None,
            "Disclaimer Text": None,
            "CTA Validation": None,
            "CTA Disclaimer Text": None,
        }

    page = await context.new_page()

    try:
        start_time = time.perf_counter()
        response = await page.goto(url.strip(), timeout=60000)
        await page.wait_for_load_state("load")

        status_code = response.status if response else None
        elapsed = round(time.perf_counter() - start_time, 2)

        # ✅ Close cookie banner
        try:
            await page.wait_for_timeout(2000)

            close_btn = page.locator("button.onetrust-close-btn-handler")
            accept_btn = page.locator("#onetrust-accept-btn-handler")

            if await close_btn.count() > 0:
                await close_btn.first.click(force=True)
                await page.wait_for_timeout(1000)
            elif await accept_btn.count() > 0:
                await accept_btn.first.click(force=True)
                await page.wait_for_timeout(1000)
        except:
            pass

        # ✅ Main disclaimer validation
        disclaimer_locator = page.locator("div.recaptcha-disclaimer")
        disclaimer_text = ""

        if await disclaimer_locator.count() > 0:
            disclaimer_text = (await disclaimer_locator.first.inner_text()).strip()
            html_lower = disclaimer_text.lower()
            result = "Found" if all(k in html_lower for k in KEYWORDS) else "Not Found"
        else:
            result = "Not Found"
            disclaimer_text = None

        # ✅ CTA validation
        cta_result = "CTA Not Present"
        cta_disclaimer_text = None

        cta_locator = page.locator("button.modal-trigger")

        if await cta_locator.count() > 0:
            try:
                await cta_locator.first.click(force=True)
                await page.wait_for_timeout(2000)

                modal_disclaimer = page.locator("div.recaptcha-disclaimer")

                if await modal_disclaimer.count() > 0:
                    cta_disclaimer_text = (
                        await modal_disclaimer.first.inner_text()
                    ).strip()

                    modal_lower = cta_disclaimer_text.lower()
                    cta_result = "Found" if all(k in modal_lower for k in KEYWORDS) else "Not Found"
                else:
                    cta_result = "Disclaimer Not Found in Modal"

            except:
                cta_result = "CTA Click Error"

    except Exception as e:
        return {
            "Validation Result": f"Error: {e}",
            "HTTP Status": None,
            "Load Time (s)": None,
            "Disclaimer Text": None,
            "CTA Validation": None,
            "CTA Disclaimer Text": None,
        }

    finally:
        await page.close()

    return {
        "Validation Result": result,
        "HTTP Status": status_code,
        "Load Time (s)": elapsed,
        "Disclaimer Text": disclaimer_text,
        "CTA Validation": cta_result,
        "CTA Disclaimer Text": cta_disclaimer_text,
    }

# -----------------------------------------------------
# 4️⃣  Bulk Runner
# -----------------------------------------------------
async def run_validation(df):

    urls = df["URLs"].tolist()

    results = []
    statuses = []
    times = []
    disclaimer_texts = []
    cta_results = []
    cta_texts = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        if USERNAME and PASSWORD:
            context = await browser.new_context(
                http_credentials={"username": USERNAME, "password": PASSWORD}
            )
        else:
            context = await browser.new_context()

        SEMAPHORE = asyncio.Semaphore(10)

        async def sem_task(url):
            async with SEMAPHORE:
                return await validate_single(context, url)

        tasks = [asyncio.ensure_future(sem_task(url)) for url in urls]

        progress_bar = st.progress(0)
        total = len(tasks)

        for i, task in enumerate(asyncio.as_completed(tasks), start=1):
            result_dict = await task

            results.append(result_dict["Validation Result"])
            statuses.append(result_dict["HTTP Status"])
            times.append(result_dict["Load Time (s)"])
            disclaimer_texts.append(result_dict["Disclaimer Text"])
            cta_results.append(result_dict["CTA Validation"])
            cta_texts.append(result_dict["CTA Disclaimer Text"])

            progress_bar.progress(i / total)

        await context.close()
        await browser.close()

    df["Validation Result"] = results
    df["HTTP Status"] = statuses
    df["Load Time (s)"] = times
    df["Disclaimer Text"] = disclaimer_texts
    df["CTA Validation"] = cta_results
    df["CTA Disclaimer Text"] = cta_texts

    return df


# -----------------------------------------------------
# 5️⃣  STREAMLIT UI
# -----------------------------------------------------
st.set_page_config(page_title="Bulk Disclaimer Validator", layout="wide")

st.title("🔍 Bulk reCAPTCHA Disclaimer Validator")
st.write("Upload an Excel file containing a column named **URLs**")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    if "URLs" not in df.columns:
        st.error("❌ Column 'URLs' not found in uploaded file.")
    else:
        st.success("✅ File uploaded successfully!")

        if st.button("🚀 Start Validation"):

            with st.spinner("Validating URLs... Please wait..."):
                validated_df = asyncio.run(run_validation(df))

            st.success("✅ Validation Completed!")

            st.dataframe(validated_df)

            # ✅ Download button
            output = BytesIO()
            validated_df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            st.download_button(
                label="📥 Download Validated Excel",
                data=output,
                file_name="validated_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )