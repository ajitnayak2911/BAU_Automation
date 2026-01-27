from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import os

# ---------- CONFIG ----------
INPUT_FILE = r"C:\Users\nayakaj\PythonCode\input_url_list.xlsx"
OUTPUT_FILE = r"C:\Users\nayakaj\PythonCode\seo_meta_results.xlsx"
# ----------------------------


def check_meta_tags(page, url):
    meta_title_present = "N"
    meta_description_present = "N"
    googlebot_index_follow = "N"

    meta_title_text = ""
    meta_description_text = ""
    meta_googlebot_text = ""
    status = "OK"

    try:
        page.goto(url, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(500)

        soup = BeautifulSoup(page.content(), "html.parser")

        meta_title = soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content", "").strip():
            meta_title_present = "Y"
            meta_title_text = meta_title.get("content").strip()

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content", "").strip():
            meta_description_present = "Y"
            meta_description_text = meta_desc.get("content").strip()

        meta_googlebot = soup.find("meta", attrs={"name": "googlebot"})
        if meta_googlebot and meta_googlebot.get("content", "").strip():
            meta_googlebot_text = meta_googlebot.get("content").strip()
            content = meta_googlebot_text.lower().replace(" ", "")
            if "index" in content and "follow" in content:
                googlebot_index_follow = "Y"

    except Exception as e:
        status = f"Error: {e}"

    return (
        meta_title_present,
        meta_title_text,
        meta_description_present,
        meta_description_text,
        googlebot_index_follow,
        meta_googlebot_text,
        status
    )


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    df_in = pd.read_excel(INPUT_FILE)
    if "URL" not in df_in.columns:
        print("ERROR: Input Excel must have a column named 'URL'")
        return

    results = []

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

        for url in df_in["URL"].dropna():
            url = str(url).strip()
            print(f"Processing: {url}")

            result = check_meta_tags(page, url)

            results.append({
                "URL": url,
                "Meta Title Present": result[0],
                "Meta Title Text": result[1],
                "Meta Description Present": result[2],
                "Meta Description Text": result[3],
                "Googlebot Tag index,follow": result[4],
                "Googlebot Tag Content": result[5],
                "Status": result[6]
            })

        browser.close()

    pd.DataFrame(results).to_excel(OUTPUT_FILE, index=False)
    print(f"\n✅ Done! Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()