from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd


def check_meta_tags(page, url):

    meta_title_present = "N"
    meta_description_present = "N"
    googlebot_index_follow = "N"

    meta_title_text = ""
    meta_description_text = ""
    meta_googlebot_text = ""
    status = "OK"

    missing_alt_images = []

    try:
        page.goto(url, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(500)

        soup = BeautifulSoup(page.content(), "html.parser")

        # ✅ Meta Title
        meta_title = soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content", "").strip():
            meta_title_present = "Y"
            meta_title_text = meta_title.get("content").strip()

        # ✅ Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content", "").strip():
            meta_description_present = "Y"
            meta_description_text = meta_desc.get("content").strip()

        # ✅ Googlebot Tag
        meta_googlebot = soup.find("meta", attrs={"name": "googlebot"})
        if meta_googlebot and meta_googlebot.get("content", "").strip():
            meta_googlebot_text = meta_googlebot.get("content").strip()
            content = meta_googlebot_text.lower().replace(" ", "")
            if "index" in content and "follow" in content:
                googlebot_index_follow = "Y"

        # ✅ Image ALT Tag Check (Original Style)
        images = soup.find_all("img")

        for img in images:
            alt = img.get("alt")
            src = img.get("src", "")

            if alt is None or not alt.strip():
                missing_alt_images.append(src)

    except Exception as e:
        status = f"Error: {e}"

    return {
        "URL": url,
        "Meta Title Present": meta_title_present,
        "Meta Title Text": meta_title_text,
        "Meta Description Present": meta_description_present,
        "Meta Description Text": meta_description_text,
        "Googlebot Tag index,follow": googlebot_index_follow,
        "Googlebot Tag Content": meta_googlebot_text,
        "Missing ALT Image Count": len(missing_alt_images),
        "Missing ALT Image Sources": "\n".join(missing_alt_images),
        "Status": status
    }
def run_single_url(url):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        result = check_meta_tags(page, url)

        browser.close()

    return result


def run_bulk(file):

    df_in = pd.read_excel(file)

    if "URL" not in df_in.columns:
        return None, "Excel must contain a column named 'URL'"

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for url in df_in["URL"].dropna():
            url = str(url).strip()
            result = check_meta_tags(page, url)
            results.append(result)

        browser.close()

    return pd.DataFrame(results), None