from pathlib import Path
from shutil import copy2
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.services.excel_writer import append_to_workbook
from app.services.pdf_extractor import extract_document
from app.services.storage import cleanup_expired, get_workbook, init_storage, upsert_workbook


app = FastAPI(title="Finance OCR Extractor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
def startup() -> None:
    init_storage()
    cleanup_expired()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "retention_days": settings.retention_days}


@app.post("/api/upload")
async def upload_pdf(
    pdf: UploadFile = File(...),
    workbook_id: str | None = Form(default=None),
) -> dict:
    cleanup_expired()

    if not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    upload_id = str(uuid4())
    pdf_path = settings.uploads_dir / f"{upload_id}.pdf"
    with pdf_path.open("wb") as fh:
        fh.write(await pdf.read())

    try:
        extracted = extract_document(pdf_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Extraction failed: {exc}") from exc

    if workbook_id:
        existing = get_workbook(workbook_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Workbook ID not found or expired.")
        source_path = Path(existing["output_path"])
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Existing workbook file is missing.")
        output_id = workbook_id
    else:
        source_path = settings.template_path
        output_id = str(uuid4())

    if not source_path.exists():
        raise HTTPException(status_code=500, detail="Template workbook not found.")

    output_path = settings.outputs_dir / f"{output_id}.xlsx"
    if source_path != output_path:
        copy2(source_path, output_path)

    rows_added = append_to_workbook(output_path, output_path, extracted)
    upsert_workbook(output_id, output_path)

    return {
        "workbook_id": output_id,
        "rows_added": rows_added,
        "download_url": f"/api/workbooks/{output_id}/download",
        "message": "Extraction completed and workbook updated.",
    }


@app.get("/api/workbooks/{workbook_id}/download")
def download_workbook(workbook_id: str):
    cleanup_expired()
    row = get_workbook(workbook_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workbook ID not found or expired.")

    file_path = Path(row["output_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Workbook file is missing.")

    return FileResponse(
        path=file_path,
        filename=f"quote_export_{workbook_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# Mount static files at the end to avoid intercepting API routes
frontend_dir = settings.base_dir / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
