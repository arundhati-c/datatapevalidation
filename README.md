# DataTape Code Validation Utility

This repository provides a Python script for validating **codes within EV5 DataTape files** against the official **NHTSA (National Highway Traffic Safety Administration)** code registry.

The validation process compares codes extracted from `.ev5` files with the authoritative list of valid codes provided through the NHTSA public API.

- **API documentation:** [NHTSA Swagger UI](https://nrd.api.nhtsa.dot.gov/swagger-ui/index.html#/nhtsa-db-data-controller/listAllCodes)
- **API endpoint:** [https://nrd.api.nhtsa.dot.gov/nhtsa/nhtsadb/api/v1/ncodes](https://nrd.api.nhtsa.dot.gov/nhtsa/nhtsadb/api/v1/ncodes)

## Overview

- validate.py
  - Validates extracted codes against the codes list from the API, outputs CSV reports of invalid codes.
- create_valid_codes_excel.py
  - Generates an Excel file with valid codes for dropdown use.
- requirements.txt
  - Contains all dependencies required to run the above scripts.
- schema.json
  - A data store containing Block to field to column mapping in nested key value pairs format.

## Setup

### Environment

- Download this repository on your machine
- Install Python **3.8+**
- Navigate to the the project directory in a terminal or a command prompt
  ```bash
  cd datatapevalidation
  ```
- Setup a virtual environment named .venv
  ```bash
  python -m venv .venv
  ```
- Activate the virtual environment
  ```bash
  .venv\Scripts\activate
  ```
- Install Required Python libraries
  ```bash
  pip install -r requirements.txt
  ```
- `CONFIG` block in each script allows you to control the behaviour of the script.
    - To change input or output folder paths, change the path variables in `CONFIG` block.
    ```python
    OUTPUT_PATH = Path(r"C:\\Your\\path\\here")
    ```
    - Toggle the type of validation as needed
    ```python
    VALIDATE_FIELD_TYPES = False
    VALIDATE_CODES = True
    ```

### Usage

Before running the scripts, navigate to the directory where the scripts reside, and activate the existing virtual environment.

Navigate to the the project directory in a terminal or a command prompt

```bash
cd datatapevalidation
```

Activate the virtual environment

```bash
.venv\Scripts\activate
```

#### 1. Validate EV5 Files

- Run the main validation script:

  ```bash
  python validate.py
  ```

  What it does:

  - Validates the NHTSA API endpoint
  - Fetches valid codes from the API endpoint into `valid_codes_{timestamp}.csv`
  - Scans all .ev5 files in the folder located in `DATA_PATH`.
  - Validates the codes and generates validation report in `OUTPUT_PATH`.
  - Each line in `valid_codes_{timestamp}.csv` file has 'codeName, code, description', and lists the field, a valid code value and description of the code value.

  Example Output:

  ```bash
  Validating NHTSA API...
  NHTSA API is reachable and valid.
  Loaded 3043 valid codes from NHTSA API.
  Found 2 .ev5 files to validate.

  Processing UVAD1779.ev5...
  Found 128 unique code-like tokens.
  Valid codes: 112
  Invalid codes: 16
  Results written to UVAD1779_validated.csv
  ```

#### 2. Generate Excel File with Valid Codes

   To export all valid codes from the API into an Excel file for dropdown use:

   ```bash
   python create_valid_codes_excel.py
   ```

   - Output:
     Creates `valid_codes_{timestamp}.xlsx` containing only valid codes.
   - Using in Excel:
     - Copy the sheet from `valid_codes_{timestamp}.xlsx` into your excel file.
     - To use the exported valid codes as a dropdown list:
       1. Open your Excel workbook.
       2. Select the cells you want to populate with the dropdown option for a field.
       3. In the ribbon menu at the top, go to Data → Data Validation
       4. Select Allow → list. In the Source field, select cells containing valid codes for that particular field from the generated excel sheet.

### Assumptions

- The NHTSA API endpoint
  https://nrd.api.nhtsa.dot.gov/nhtsa/nhtsadb/api/v1/ncodes
  is assumed to be active, accurate, and current.
- EV5 files are plain-text and use the | delimiter.

### Contributors

- Introduced by: John Paul Donlon
- Authored by: Arundhati Avinash Dange
