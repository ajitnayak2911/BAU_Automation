import pandas as pd
import json
import re

# Path to your Excel file
file_path = r"C:\Users\nayakaj\Payload.xlsx"

# Load Excel file (Sheet1 has the payload_v2 column)
df = pd.read_excel(file_path, sheet_name="Sheet1")

# Function to extract only the first valid JSON object
def extract_json(payload):
    try:
        if isinstance(payload, str) and "{" in payload:
            # Use regex to capture the first {...} block
            match = re.search(r"\{.*\}", payload)
            if match:
                return json.loads(match.group(0))
    except Exception as e:
        print(f"Error parsing JSON: {e}")
    return None

# Apply extraction
df["parsed_payload"] = df["payload_v2"].apply(extract_json)

# Flatten JSON objects into columns
json_df = pd.json_normalize(df["parsed_payload"].dropna()).reset_index(drop=True)

# Reset SubmissionDate index too
submission_dates = df["SubmissionDate UTC"].reset_index(drop=True)

# Merge safely
final_df = pd.concat([submission_dates, json_df], axis=1)

# Save result to CSV
output_file = r"C:\Users\nayakaj\Extracted_Payload.csv"
final_df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"✅ Extraction complete. File saved as {output_file}")
