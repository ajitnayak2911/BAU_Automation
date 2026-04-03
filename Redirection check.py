import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#from sqlalchemy import false

# === Configuration ===
file_path = r'C:\Users\nayakaj\PythonCode\301.xlsx'
output_path = r'C:\Users\nayakaj\PythonCode\301_result.xlsx'
username = 'broadridgedigital'
password = 'broadridge1'
max_workers = 10   # adjust between 5–20 for performance vs. server tolerance
timeout = 10       # seconds per request

# === Read Excel ===
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip()
print("Columns found:", df.columns.tolist())

url_col = 'URLs'  # Adjust to match your Excel header


# === Redirect checking function ===
def get_redirect_info(url):
    try:
        print(f"Checking: {url}")

        # Step 1 - Check if redirect is set (without following redirects)
        response = requests.get(url, allow_redirects=False, timeout=timeout, verify=False)
        # Try again with credentials if needed
        if response.status_code in [401, 403]:
            response = requests.get(
                url,
                auth=HTTPBasicAuth(username, password),
                allow_redirects=False,
                timeout=timeout,
                verify=False
            )

        redirect_type = response.status_code
        redirected_url = response.headers.get("Location", None)

        # Step 2 - If redirected, check the final target status
        final_status = None
        if redirected_url:
            try:
                final_response = requests.get(
                    redirected_url, allow_redirects=True, timeout=timeout,verify=False
                )
                final_status = final_response.status_code
            except requests.exceptions.RequestException as e:
                final_status = f"Error: {e}"

        # Return summary
        return {
            "URLs": url,
            "Redirected URL": redirected_url if redirected_url else "No Redirect",
            "Redirect Type": redirect_type,
            "Final Status Code": final_status if final_status else redirect_type,
        }

    except requests.exceptions.RequestException as e:
        return {
            "URLs": url,
            "Redirected URL": f"Error: {e}",
            "Redirect Type": None,
            "Final Status Code": None,
        }


# === Run concurrently with ThreadPoolExecutor ===
results = []
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Start all URL checks
    future_to_url = {executor.submit(get_redirect_info, url): url for url in df[url_col]}

    # Iterate as each completes
    for future in as_completed(future_to_url):
        result = future.result()
        results.append(result)

# === Convert results to DataFrame and save ===
results_df = pd.DataFrame(results)
results_df.to_excel(output_path, index=False, engine="openpyxl")

print(f"\n✅ URL scanning complete. Results saved to: {output_path}")