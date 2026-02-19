from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import re

# ---------- CONFIG ----------
INPUT_FILE = r"C:\Users\nayakaj\PythonCode\input_url_list.xlsx"
OUTPUT_FILE = r"C:\Users\nayakaj\PythonCode\badge_caps_validation.xlsx"
# ----------------------------

# WHITELIST OF ALLOWED BADGE PATTERNS
BADGE_PATTERNS = [
    {
        "tag": "span",
        "required_classes": {"badge", "badge-light", "w-fit"},
        "required_attrs": {"slot": "title"}
    },
    {
        "tag": "span",
        "required_classes": {"badge", "badge-light"},
        "required_attrs": {}
    },
    {
        "tag": "span",
        "required_classes": {"badge", "badge-dark", "self-baseline"},
        "required_attrs": {"slot": "title"}
    },

    {
    "tag": "span",
    "required_classes": {"badge", "badge-dark"},
    "required_attrs": {"slot": "title"}
    }

]



def is_all_caps(text):
    letters = re.findall(r"[A-Za-z]", text)
    if not letters:
        return False
    return all(ch.isupper() for ch in letters)


def matches_badge_pattern(element):
    """
    Strictly validates element against approved badge patterns
    """
    for pattern in BADGE_PATTERNS:
        if element.name != pattern["tag"]:
            continue

        classes = set(element.get("class", []))
        if not pattern["required_classes"].issubset(classes):
            continue

        attrs_match = True
        for attr, value in pattern["required_attrs"].items():
            if element.get(attr) != value:
                attrs_match = False
                break

        if attrs_match:
            return True

    return False


def check_badge_caps(page, url):
    rows = []
    status = "OK"

    try:
        page.goto(url, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(500)

        soup = BeautifulSoup(page.content(), "html.parser")

        for element in soup.find_all("span"):
            if not matches_badge_pattern(element):
                continue

            text = element.get_text(strip=True)

            is_caps = "Y" if is_all_caps(text) else "N"

            identifier = (
                element.get("id")
                or " ".join(element.get("class", []))
                or "span"
            )

            location = f"<span class='{identifier}'>"

            rows.append({
                "URL": url,
                "Badge Found": "Y",
                "Badge Text ALL CAPS": is_caps,
                "Badge Text": text,
                "Badge Location": location,
                "Status": status
            })

    except Exception as e:
        rows.append({
            "URL": url,
            "Badge Found": "N",
            "Badge Text ALL CAPS": "N",
            "Badge Text": "",
            "Badge Location": "",
            "Status": f"Error: {e}"
        })

    return rows

def run_badge_caps_for_url(url):
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

        badge_rows = check_badge_caps(page, url)
        results.extend(badge_rows)

        browser.close()

    return results


def run_badge_caps_bulk(file):
    df_in = pd.read_excel(file)

    if "URL" not in df_in.columns:
        return None, "Excel must contain a column named 'URL'"

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
            badge_rows = check_badge_caps(page, url)
            results.extend(badge_rows)

        browser.close()

    return pd.DataFrame(results), None
    #pd.DataFrame(results).to_excel(output_file, index=False)

    #return f"✅ Done! Results saved to: {output_file}"
