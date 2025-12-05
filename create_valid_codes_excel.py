"""
create_valid_codes_excel.py

Fetches valid NHTSA codes and saves them to an Excel file
with each field type as a column and its valid codes as dropdown values.
"""

import requests
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook

# ========= CONFIG =========
NHTSA_URL = "https://nrd.api.nhtsa.dot.gov/nhtsa/nhtsadb/api/v1/ncodes"
OUTPUT_PATH = Path(r"C:\\Github\\UVACAB\\DataTapeValidation\\Data\\Processed")


def fetch_valid_codes(url=NHTSA_URL):
    """
    Fetch valid codes from the NHTSA API.
    Returns a dictionary {field_type: set(codes)}.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching API data: {e}")
        return {}

    valid_codes = {}
    for item in data.get("results", []):
        field = item.get("codeName", "").strip().upper()
        code = item.get("code", "").strip().upper()
        if field and code:
            valid_codes.setdefault(field, set()).add(code)

    print(f"Loaded valid codes for {len(valid_codes)} fields from NHTSA API.")
    return valid_codes


def save_valid_codes_excel(valid_codes, output_dir):
    """
    Save valid codes to an Excel file suitable for dropdown lists in Excel.
    Each column = field type, each cell under it = valid codes for that field.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"valid_codes_{timestamp}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "ValidCodes"

    fields = sorted(valid_codes.keys())
    ws.append(fields)

    # Determine max list length to fill rows correctly
    max_len = max(len(codes) for codes in valid_codes.values())

    for i in range(max_len):
        row = []
        for field in fields:
            codes = sorted(valid_codes[field])
            row.append(codes[i] if i < len(codes) else "")
        ws.append(row)

    wb.save(output_file)
    print(f"Saved valid codes Excel file to {output_file}")
    print("Each column represents a field type; use it for dropdowns in Excel.")
    return output_file


def main():
    print("Fetching valid NHTSA codes...")
    valid_codes = fetch_valid_codes()
    if not valid_codes:
        print("No valid codes retrieved. Exiting.")
        return

    save_valid_codes_excel(valid_codes, OUTPUT_PATH)


if __name__ == "__main__":
    main()
