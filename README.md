# Finance OCR (Part 1)

Production-ready starter for extracting quote data from PDF and writing it into the client Excel format.

## What this includes

- FastAPI backend with upload endpoint.
- Semantic PDF extraction using `pdfplumber` + OCR fallback (`pytesseract`).
- Strict mapping to your Excel template headers.
- Appending new uploaded PDF data into the same workbook using `workbook_id`.
- Formula logic in backend for all appended rows in `Salesdiscount` column:
  - `=1-(((O{row}/P1)*(1+P2)/M{row}))`
- European date format (`dd/mm/yyyy`).
- Business unit forced to `Spain`.
- 30-day data retention (workbook records + generated files expire automatically).
- No hardcoded machine paths in runtime flow.

## Project structure

- `/Users/amarahahmed/Desktop/finance ocr/backend/app/main.py` - API
- `/Users/amarahahmed/Desktop/finance ocr/backend/app/services/pdf_extractor.py` - PDF parsing
- `/Users/amarahahmed/Desktop/finance ocr/backend/app/services/excel_writer.py` - Strict Excel mapping + formula
- `/Users/amarahahmed/Desktop/finance ocr/backend/app/services/storage.py` - SQLite retention metadata
- `/Users/amarahahmed/Desktop/finance ocr/backend/app/config/mapping_rules.json` - strict mapping rules
- `/Users/amarahahmed/Desktop/finance ocr/frontend/index.html` - upload UI
- `/Users/amarahahmed/Desktop/finance ocr/templates/template.xlsx` - your provided template copy

## Run locally

```bash
cd "/Users/amarahahmed/Desktop/finance ocr"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

Open: `http://127.0.0.1:8000`

## API usage

### 1) Create new workbook from template

```bash
curl -X POST "http://127.0.0.1:8000/api/upload" \
  -F "pdf=@/absolute/path/input.pdf"
```

### 2) Update same workbook with another PDF

```bash
curl -X POST "http://127.0.0.1:8000/api/upload" \
  -F "pdf=@/absolute/path/input2.pdf" \
  -F "workbook_id=<id_from_previous_response>"
```

### 3) Download workbook

```bash
curl -L "http://127.0.0.1:8000/api/workbooks/<workbook_id>/download" -o output.xlsx
```

## Notes

- OCR requires Tesseract installed on host OS. Without it, text extraction still runs using `pdfplumber` where possible.
- Mapping is strict. If template headers change, update `mapping_rules.json`.
- Expired workbooks are removed after 30 days.
