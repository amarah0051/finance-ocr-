# Optimal Prompt (Part 1)

Build a production-grade system that extracts data from uploaded quote PDFs and writes it into an Excel template with strict schema compliance.

## Business context
- Region/business unit is Spain.
- Input is recurring PDF quotations from the same vendor structure.
- Output must match the provided Excel format exactly.
- European date format is mandatory (`dd/mm/yyyy`).
- Data retention must be 30 days.

## Technical requirements
- Backend in Python using FastAPI.
- PDF extraction stack: `pdfplumber` + anchor-header parsing + `pytesseract` OCR fallback.
- Table extraction should be semantic (not only positional).
- Use strict mapping rules from extracted fields to Excel headers.
- No hardcoded local machine paths; use environment/config paths.
- Must support appending multiple uploaded PDFs into the same Excel workbook.
- Frontend for upload + workbook update flow.

## Input/Output behavior
- Input: user uploads PDF.
- If no `workbook_id`, create output workbook from template and append extracted rows.
- If `workbook_id` is provided, append new extracted rows to the existing workbook.
- Output: downloadable `.xlsx` file with rows mapped to template columns only.

## Excel mapping constraints
- Use the existing worksheet and headers from template.
- Fail fast if required headers are missing (strict mode).
- Populate only fields that exist in the template format.
- Set `BusinessUnit = Spain`.
- Dates must be normalized to `dd/mm/yyyy`.

## Formula logic (backend)
- In `Salesdiscount` column, apply for every appended row:
  `=1-(((O{row}/P1)*(1+P2)/M{row}))`
- Ensure formula is written for all new rows, not only one row.
- Keep P1/P2 constants from template.

## Data governance
- Store metadata in SQLite.
- Generated workbooks and metadata expire after 30 days.
- Implement cleanup for expired records/files.

## Deliverables
1. FastAPI backend (`/api/upload`, `/api/workbooks/{id}/download`, `/api/health`).
2. Frontend upload page with optional workbook ID for update mode.
3. Extraction module with anchor-based semantic parsing and OCR fallback.
4. Excel writer module with strict mapping validation and formula injection.
5. Retention module with 30-day expiry cleanup.
6. Setup/run instructions and clear file structure.

## Quality bar
- Handle large PDFs efficiently.
- Return actionable errors for extraction/mapping failures.
- Keep modules decoupled (extractor, mapper/writer, storage, API).
- Include a sample end-to-end run path with example cURL calls.
