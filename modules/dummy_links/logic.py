import pandas as pd
import requests
from bs4 import BeautifulSoup



# Texts to ignore on every page (case-insensitive)
IGNORE_TEXTS = {
    "skip to main content",
    "contact us",
    "do not sell my personal information"
}


def is_dummy_link(href):
    if not href:
        return True

    href = href.strip().lower()

    return (
        href == "#"
        or href.startswith("#")
        or href in ("javascript:void(0)", "javascript:void(0);")
    )


def should_ignore_link(text):
    if not text:
        return False
    return text.strip().lower() in IGNORE_TEXTS


def clean_link_text(text):
    if not text:
        return "[NO TEXT]"

    text = text.strip()
    lower_text = text.lower()

    for prefix in ("resource", "article"):
        if lower_text.startswith(prefix):
            return text[len(prefix):].strip()

    return text


def fetch_dummy_links(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        dummy_links = []
        count = 1

        for a in soup.find_all("a"):
            href = a.get("href", "")
            raw_text = a.get_text(strip=True)
            text = clean_link_text(raw_text)

            if should_ignore_link(text):
                continue

            if is_dummy_link(href):
                dummy_links.append(
                    f"[{count}] {text}\n    href={href}"
                )
                count += 1

        if not dummy_links:
            return "No dummy links found"

        return "\n\n".join(dummy_links)

    except requests.RequestException as e:
        return f"ERROR: {e}"

def run_dummy_links_single(url):
    result = fetch_dummy_links(url)
    return result

def run_dummy_links_bulk(file):
    df = pd.read_excel(file)

    if "URL" not in df.columns:
        return None, "Excel must contain a column named 'URL'"

    df["Dummy_Links"] = df["URL"].apply(fetch_dummy_links)
    return df, None