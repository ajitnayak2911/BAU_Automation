import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import tempfile

# --------------------------------------------------
# PLAYWRIGHT‑ONLY META CHECK FUNCTION
# --------------------------------------------------
def check_meta_tags(url):
    meta_title_present = "N"
    meta_description_present = "N"
    googlebot_index_follow = "N"

    meta_title_text = ""
    meta_description_text = ""
    meta_googlebot_text = ""
    status = "OK"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            page.goto(url, timeout=60000, wait_until="networkidle")
            page.wait_for_timeout(2000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # --- Meta title ---
        meta_title = soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content", "").strip():
            meta_title_present = "Y"
            meta_title_text = meta_title.get("content").strip()

        # --- Meta description ---
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content", "").strip():
            meta_description_present = "Y"
            meta_description_text = meta_desc.get("content").strip()

        # --- Meta googlebot ---
        meta_googlebot = soup.find("meta", attrs={"name": "googlebot"})
        if meta_googlebot and meta_googlebot.get("content", "").strip():
            meta_googlebot_text = meta_googlebot.get("content").strip()
            content = meta_googlebot_text.lower().replace(" ", "")
            if "index" in content and "follow" in content:
                googlebot_index_follow = "Y"

    except Exception as e:
        status = f"Error: {type(e).__name__}"

    return (
        meta_title_present,
        meta_title_text,
        meta_description_present,
        meta_description_text,
        googlebot_index_follow,
        meta_googlebot_text,
        status
    )

# --------------------------------------------------
# HELPERS (UNCHANGED BEHAVIOR)
# --------------------------------------------------
def title_desc_same(title, desc):
    return "SAME" if title and desc and title.strip().lower() == desc.strip().lower() else "OK"

def seo_warnings(row):
    warnings = []
    if row["Meta Title Present"] == "N":
        warnings.append("Missing Meta Title")
    if row["Meta Description Present"] == "N":
        warnings.append("Missing Meta Description")
    if row["Title & Description Same?"] == "SAME":
        warnings.append("Title & Description Same")
    if row["Googlebot Tag index,follow"] == "N":
        warnings.append("Googlebot not index,follow")
    return "; ".join(warnings) if warnings else "No Issues"

def style_df(df):
    def color(val):
        if val == "Y":
            return "background-color:#c6f6d5"
        if val == "N":
            return "background-color:#feb2b2"
        if val == "SAME":
            return "background-color:#fbd38d"
        return ""
    return df.style.applymap(color)

# --------------------------------------------------
# STREAMLIT UI
# --------------------------------------------------
st.set_page_config("SEO Meta Tag Checker (Playwright)", layout="wide")
st.title("🔍 SEO Meta Tag Checker (Playwright)")

tab1, tab2 = st.tabs(["🔗 URL Input (Auto‑Run)", "📋 Bulk URLs / Excel"])

# ---------- TAB 1 ----------
with tab1:
    url = st.text_input("Enter URL (auto‑runs)", placeholder="https://example.com")

    if url:
        with st.spinner("Checking meta tags..."):
            r = check_meta_tags(url.strip())

        df = pd.DataFrame([{
            "URL": url.strip(),
            "Meta Title Present": r[0],
            "Meta Title Text": r[1],
            "Meta Description Present": r[2],
            "Meta Description Text": r[3],
            "Googlebot Tag index,follow": r[4],
            "Googlebot Tag Content": r[5],
            "Status": r[6],
            "Title & Description Same?": title_desc_same(r[1], r[3])
        }])

        df["SEO Warnings"] = df.apply(seo_warnings, axis=1)
        st.dataframe(style_df(df), use_container_width=True)

# ---------- TAB 2 ----------
with tab2:
    urls_text = st.text_area("Paste URLs (one per line)", height=150)
    uploaded_file = st.file_uploader("Or upload Excel (.xlsx)", type=["xlsx"])

    urls = []

    if urls_text:
        urls.extend([u.strip() for u in urls_text.splitlines() if u.strip()])

    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)
        if "URL" not in df_excel.columns:
            st.error("Excel must contain 'URL' column")
        else:
            urls.extend(df_excel["URL"].dropna().astype(str).tolist())

    if urls and st.button("▶ Run Bulk Check"):
        results = []
        progress = st.progress(0)

        for i, url in enumerate(urls, start=1):
            r = check_meta_tags(url)

            results.append({
                "URL": url,
                "Meta Title Present": r[0],
                "Meta Title Text": r[1],
                "Meta Description Present": r[2],
                "Meta Description Text": r[3],
                "Googlebot Tag index,follow": r[4],
                "Googlebot Tag Content": r[5],
                "Status": r[6],
                "Title & Description Same?": title_desc_same(r[1], r[3])
            })

            progress.progress(i / len(urls))

        df = pd.DataFrame(results)
        df["SEO Warnings"] = df.apply(seo_warnings, axis=1)

        st.dataframe(style_df(df), use_container_width=True)

        st.download_button(
            "⬇ Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            "seo_results.csv",
            "text/csv"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            df.to_excel(tmp.name, index=False)
            with open(tmp.name, "rb") as f:
                st.download_button(
                    "⬇ Download Excel",
                    f,
                    "seo_results.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )