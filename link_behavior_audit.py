import requests
from urllib.parse import urlparse, urljoin
import streamlit as st
import pandas as pd
import io

from bs4 import BeautifulSoup
from openpyxl.styles import PatternFill
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Special paths we classify as "External" even though same domain
SPECIAL_EXTERNAL_PATHS = ["/fr/", "/de/", "/jp/", "/next"]

# Exclude entire sections by CSS selectors (limited to pure nav/footer/cookie banners)
IGNORE_SELECTORS = [
    "footer#footer-section",
    "nav#main-nav",
    "div.promo-bar",
    "div.contact-us__bottom",
    "div.ot-sdk-row",
    "div#onetrust-consent-sdk",
    "div#onetrust-group-container",
    "div.ot-pc-footer-logo",
    "a.ot-cookie-policy-link",
    "div.recaptcha-disclaimer",
    "div.recaptcha-disclaimer.reducefont"
    "a.skip-link[href='#main-content']"
]

# Exclude specific href patterns (known boilerplate)
IGNORE_HREF_PATTERNS = [
    "https://policies.google.com/privacy",
    "https://policies.google.com/terms",
    "javascript:void(0)",         # copy-to-clipboard
    "/contact-us"                 # Skip Contact Us link
]

# Social share domains
SOCIAL_DOMAINS = ["twitter.com", "facebook.com", "linkedin.com"]


def analyze_links(page_url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(page_url)

        # ✅ Explicit wait until at least one <a> appears
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
        )

        # ✅ Get page source for BeautifulSoup cleanup
        html = driver.page_source
        driver.quit()


    except Exception as e:
        return [], f"Error fetching page: {e}"


    # ✅ Parse with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted sections by configured selectors
    for selector in IGNORE_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()

    # --- REMOVE FOOTER ---
    #footer = soup.find("footer", id="footer-section")
    #if footer: footer.decompose()

    # --- REMOVE MAIN NAVIGATION ---
    #nav = soup.find("nav", id="main-nav")
    #if nav: nav.decompose()

    # --- REMOVE PROMO BAR ---
    #promo_bar = soup.find("div", class_="promo-bar")
    #if promo_bar: promo_bar.decompose()

    # --- REMOVE CONTACT US Phone Numbers ---
    #contact_us_numbers = soup.find("div", class_="contact-us__bottom")
    #if contact_us_numbers: contact_us_numbers.decompose()

    # --- REMOVE COOKIE BANNER (OneTrust) ---
    #cookie_banner = soup.find("div", class_="ot-sdk-row")
    #if cookie_banner: cookie_banner.decompose()

    #cookie_logo = soup.find("div", id="onetrust-consent-sdk")
    #if cookie_logo: cookie_logo.decompose()

    #cookie_group = soup.find("div", id="onetrust-group-container")
    #if cookie_group: cookie_group.decompose()

    # --- REMOVE OneTrust Footer Logo ---
    #onetrust_logo = soup.find("div", class_="ot-pc-footer-logo")
    #if onetrust_logo: onetrust_logo.decompose()

    # --- REMOVE BREADCRUMBS ---
    #breadcrumbs = soup.find("nav", class_="breadcrumbs") or soup.find("div", class_="breadcrumbs")
    #if breadcrumbs: breadcrumbs.decompose()

    links = soup.find_all("a", href=True)
    base_domain = urlparse(page_url).netloc

    results = []

    for link in links:
        href = link.get("href")
        if not href:
            continue

        # Skip tel/mailto and skip links
        if (href.startswith("tel:") or
                href.startswith("mailto:")or
                href.startswith("#main-content")
        ):
            continue
        # Skip excluded hrefs
        if any(pattern in href for pattern in IGNORE_HREF_PATTERNS):
            continue

        absolute_url = urljoin(page_url, href)
        parsed_url = urlparse(absolute_url)

        # Link text fallback
        link_text = link.get_text(strip=True) or link.get("aria-label") or link.get("title") or absolute_url

        # Internal vs External
        is_external = parsed_url.netloc and parsed_url.netloc != base_domain
        for sp in SPECIAL_EXTERNAL_PATHS:
            if parsed_url.path.startswith(sp) and parsed_url.netloc == base_domain:
                is_external = True
                break

        # Default behaviour
        opens_in = "New Tab" if link.get("target") == "_blank" else "Same Tab"

        # Social override
        if any(domain in href for domain in SOCIAL_DOMAINS):
            opens_in = "New Tab"

        # Document detection
        doc_extensions = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".ppt", ".pptx")
        is_document = absolute_url.lower().endswith(doc_extensions)

        # Expected rule + reason
        if is_document:
            is_external = True
            expected = "✔" if opens_in == "New Tab" else "✘"
            reason = "Document: must open External in New Tab" if expected == "✔" else "Document opened wrong"
        else:
            expected = "✔" if (
                    (is_external and opens_in == "New Tab")
                    or (not is_external and opens_in == "Same Tab")
            ) else "✘"
            if is_external:
                reason = "External OK" if expected == "✔" else "External should open New Tab"
            else:
                reason = "Internal OK" if expected == "✔" else "Internal should open Same Tab"

        results.append({
            "Link Text": link_text,
            "Opens In": opens_in,
            "Internal/External": "External" if is_external else "Internal",
            "Expected?": expected,
            "Reason": reason
        })

    return results, None


# --- Streamlit UI ---
st.set_page_config(page_title="Link Behavior Audit", layout="wide")

st.title("🔍 Link Behavior Audit Tool")
st.markdown("""
    This app scans a webpage for all **links** and checks:
    - Whether they open in **Same Tab** or **New Tab**
    - Whether they are **Internal** or **External**
    - Whether the behavior matches the **Expected Rule**
       - Internal → Same Tab
       - External → New Tab
       - Documents (PDF/DOC/XLS/PPT) → Always External + New Tab

    👉 Enter any website URL below:
    """)

url = st.text_input("Enter Website URL", "https://www.broadridge.com/")

if st.button("Run Audit"):
    with st.spinner("Analyzing links..."):
        results, error = analyze_links(url)

    if error:
        st.error(error)
    elif results:
        df = pd.DataFrame(results)
        st.success(f"Found {len(df)} links.")

        def highlight_row(row):
            return ['background-color: #f8d7da' if row["Expected?"] == "✘" else
                    'background-color: #d4edda' if row["Expected?"] == "✔" else ''] * len(row)


        # Ensure index is dropped
        df = df.reset_index(drop=True)

        styled_df = df.style.apply(highlight_row, axis=1)

        # 🔸 hide index so it doesn't render Count column
        html_table = styled_df.hide(axis="index").to_html(escape=False)

        # Render in Streamlit
        st.components.v1.html(
            f"""
            <div style="max-height:450px; overflow-y:auto; border:1px solid #ddd;">
                <style>
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    thead th {{
                        position: sticky;
                        top: 0;
                        background: #f1f1f1;
                        z-index: 2;
                    }}
                    th, td {{
                        padding: 6px 12px;
                        border: 1px solid #ccc;
                        text-align: left;
                    }}
                </style>
                {html_table}
            </div>
            """,
            height=500,
            scrolling=False
        )
        # Excel export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="AuditResults")
            ws = writer.sheets["AuditResults"]
            for row in range(2, len(df) + 2):
                expected_value = df.iloc[row - 2]["Expected?"]
                fill = PatternFill(
                    start_color="D4EDDA" if expected_value == "✔" else "F8D7DA",
                    end_color="D4EDDA" if expected_value == "✔" else "F8D7DA",
                    fill_type="solid"
                )
                for col in range(1, len(df.columns) + 1):
                    ws.cell(row=row, column=col).fill = fill

        st.download_button(
            "⬇️ Download results as Excel",
            data=output.getvalue(),
            file_name="link_audit_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No links found on this page.")