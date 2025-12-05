import requests
import csv
import json
import re
from pathlib import Path
from datetime import datetime

# ========= CONFIG =========
BASE_PATH = Path(__file__).resolve().parent         # Resolve the parent directory of the scripts
DATA_PATH = BASE_PATH / "Data"                      # Input folder path
OUTPUT_PATH = DATA_PATH / "ProcessedFiles"          # Output path
SCHEMA_PATH = BASE_PATH / "schema.json"             # Schema file path
NHTSA_URL = "https://nrd.api.nhtsa.dot.gov/nhtsa/nhtsadb/api/v1/ncodes"
VALIDATE_FIELD_TYPES = False    # validate that field_type exists in valid_codes
VALIDATE_CODES = True           # validate that value is an allowed code


# ========= FUNCTIONS =========

def fetch_valid_codes(url=NHTSA_URL):
    """Fetch valid codes from the NHTSA API and return a list of dicts."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching API data: {e}")
        return []

    results = data.get("results", [])
    if not results:
        print("No results returned from API.")
        return []

    # Save valid codes to a timestamped CSV
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    output_file = OUTPUT_PATH / f"valid_codes_{timestamp}.csv"

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["CodeName", "Code", "Description"])
        for item in sorted(results, key=lambda x: (x.get("codeName", ""), x.get("code", ""))):
            writer.writerow([
                item.get("codeName", "").strip(),
                item.get("code", "").strip().upper(),
                item.get("description", "").strip()
            ])

    print(f"Loaded {len(results)} valid codes from NHTSA API.")
    print(f"Saved valid codes to {output_file.name}")
    return results


def validate_nhtsa_api(url):
    """Validate the NHTSA API endpoint before using it."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return False, f"API request failed: {e}"

    try:
        data = response.json()
    except ValueError:
        return False, "Response is not valid JSON."

    if "results" not in data or not isinstance(data["results"], list):
        return False, "Unexpected JSON structure (missing 'results')."

    sample = data["results"][0] if data["results"] else None
    if not sample or "code" not in sample:
        return False, "No 'code' field found in API response."

    return True, data


def load_schema(schema_path):
    """Load EV5 JSON schema."""
    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        return {}
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_ev5_blocks(ev5_path):
    """Return {block_name: [lines]} from an EV5 file."""
    blocks = {}
    current_block = None
    with ev5_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            header_match = re.match(r"^-{2,}\s*([A-Z ]+)\s*-{2,}$", line)
            if header_match:
                current_block = header_match.group(1).strip().upper()
                blocks[current_block] = []
                continue

            if current_block:
                blocks[current_block].append(line)
    return blocks


def validate_ev5_blocks(ev5_path, schema, valid_codes,
                        validate_field_types=VALIDATE_FIELD_TYPES,
                        validate_codes=VALIDATE_CODES):

    blocks = parse_ev5_blocks(ev5_path)
    invalid_entries = []
    checked_count = 0

    # Build lookups
    valid_lookup = {}
    for v in valid_codes:
        name = v.get("codeName", "").strip().upper()
        code = v.get("code", "").strip().upper()
        if name and code:
            valid_lookup.setdefault(name, set()).add(code)

    for block, rows in blocks.items():
        if block.upper() not in schema:
            continue

        for line_num, row in enumerate(rows, start=1):
            parts = row.split("|")

            for field_type, col in schema[block].items():
                idx = int(col) - 1
                if idx >= len(parts):
                    continue

                value = parts[idx].strip().upper()
                if not value:
                    continue

                checked_count += 1
                field_type_upper = field_type.strip().upper()

                # FIELD validation
                if validate_field_types:
                    if field_type_upper not in valid_lookup:
                        invalid_entries.append({
                            "Block": block,
                            "Field": field_type,
                            "Value": value,
                            "Line": line_num,
                            "Column": col,
                            "ExpectedCodes": "Field type not recognized",
                            "InvalidType": "FIELD",
                            "Status": "INVALID"
                        })
                        # Skip code validation if field invalid
                        continue

                # CODE validation
                if validate_codes:
                    if field_type_upper in valid_lookup:
                        if value not in valid_lookup[field_type_upper]:
                            expected = ", ".join(sorted(valid_lookup[field_type_upper]))
                            invalid_entries.append({
                                "Block": block,
                                "Field": field_type,
                                "Value": value,
                                "Line": line_num,
                                "Column": col,
                                "ExpectedCodes": expected,
                                "InvalidType": "CODE",
                                "Status": "INVALID"
                            })

    return checked_count, invalid_entries


def write_combined_report(ev5_path, invalid_entries):
    """Write invalid field report to CSV with line, column, and invalid type."""
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    output_csv = OUTPUT_PATH / f"{ev5_path.stem}_schema_validated.csv"

    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Block", "Line", "Column", "Field", "Value", 
            "InvalidType", "ExpectedCodes", "Status"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for e in invalid_entries:
            writer.writerow(e)

    print(f"  Schema validation results written to {output_csv.name}")



def main():
    """Main workflow: validate the API, then process EV5 files."""
    print("Validating NHTSA API...")

    ok, result = validate_nhtsa_api(NHTSA_URL)
    if not ok:
        print(f"API validation failed: {result}")
        return
    else:
        print("NHTSA API is reachable and valid.")

    valid_codes = fetch_valid_codes()
    if not valid_codes:
        return

    schema = load_schema(SCHEMA_PATH)
    if not schema:
        print("Schema not loaded, exiting.")
        return

    ev5_files = list(DATA_PATH.rglob("*.ev5"))
    if not ev5_files:
        print(f"No .ev5 files found in {DATA_PATH}")
        return

    print(f"Found {len(ev5_files)} .ev5 files to validate.")

    for ev5_path in ev5_files:
        print(f"\nProcessing {ev5_path.name}...")
        checked, invalid = validate_ev5_blocks(ev5_path, schema, valid_codes)
        print(f"  Checked {checked} coded fields.")
        print(f"  Invalid entries: {len(invalid)}")
        if invalid:
            for e in invalid[:10]:
                print(f"    {e['Block']}.{e['Field']} = {e['Value']}")
            if len(invalid) > 10:
                print(f"    ...and {len(invalid)-10} more.")
            write_combined_report(ev5_path, invalid)
        else:
            print("  All coded fields valid.")


if __name__ == "__main__":
    main()
