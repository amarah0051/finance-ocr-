import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pdfplumber
from PIL import Image

from app.models.schemas import ExtractedDocument, ExtractedLineItem

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None


DATE_MM_DD_YYYY = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
QUOTE_ID_RE = re.compile(r"Quote #:\s*([^\n\r]+)")
EXPIRY_RE = re.compile(r"Expiration Date:\s*([^\n\r]+)")
SKU_RE = re.compile(r"\b(NK-[A-Z0-9-]+)\b")


def _to_eu_date(mmddyyyy: str | None) -> str | None:
    if not mmddyyyy:
        return None
    try:
        return datetime.strptime(mmddyyyy.strip(), "%m/%d/%Y").strftime("%d/%m/%Y")
    except ValueError:
        return mmddyyyy


def _money_to_float(value: str) -> float:
    return float(value.replace(",", ""))


def _safe_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return _money_to_float(value)
    except Exception:
        return default


def _ocr_text(page) -> str:
    if pytesseract is None:
        return ""
    image = page.to_image(resolution=200).original
    if not isinstance(image, Image.Image):
        image = Image.open(BytesIO(image))
    return pytesseract.image_to_string(image)


def _extract_text_by_page(pdf_path: Path) -> list[str]:
    pages: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if len(text.strip()) < 20:
                text = _ocr_text(page)
            pages.append(text)
    return pages


def _extract_parties(text: str) -> tuple[str | None, str | None, str | None]:
    reseller = None
    reseller_contact = None
    end_user = None

    if "Ship To Bill To" in text and "REGIONAL DIRECTOR" in text:
        block = text.split("Ship To Bill To", 1)[1].split("REGIONAL DIRECTOR", 1)[0]
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if lines:
            reseller_contact = lines[0]
        for ln in lines:
            if "exclusive networks" in ln.lower():
                reseller = ln
            if "bbva" in ln.lower():
                end_user = ln

    return reseller, reseller_contact, end_user


def _extract_line_items(pages_text: list[str]) -> list[ExtractedLineItem]:
    items: list[ExtractedLineItem] = []

    for text in pages_text:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for i, ln in enumerate(lines):
            if not SKU_RE.search(ln):
                continue

            sku = SKU_RE.search(ln).group(1)
            name = ln.split(sku, 1)[0].strip()
            tail = ln.split(sku, 1)[1]

            qty_match = re.search(r"\b([0-9][0-9,]*)\b", tail)
            dates = DATE_MM_DD_YYYY.findall(ln)
            if len(dates) < 2 and i + 1 < len(lines):
                dates += DATE_MM_DD_YYYY.findall(lines[i + 1])

            currency_match = re.search(r"\b(USD|EUR|GBP)\b", ln)
            currency = currency_match.group(1) if currency_match else "USD"

            numbers = re.findall(r"\b[0-9][0-9,]*\.[0-9]{2}\b", ln)
            if len(numbers) < 2 and i + 1 < len(lines):
                numbers += re.findall(r"\b[0-9][0-9,]*\.[0-9]{2}\b", lines[i + 1])

            if not qty_match or len(numbers) < 2:
                continue

            list_unit_price = _safe_float(numbers[0])
            discount_percent = _safe_float(numbers[1], default=0.0) if len(numbers) >= 3 else None
            net_unit_price = _safe_float(numbers[2], default=_safe_float(numbers[1])) if len(numbers) >= 3 else _safe_float(numbers[1])

            item = ExtractedLineItem(
                item=name,
                sku=sku,
                quantity=float(qty_match.group(1).replace(",", "")),
                currency=currency,
                list_unit_price=list_unit_price,
                discount_percent=discount_percent,
                net_unit_price=net_unit_price,
                contract_start=_to_eu_date(dates[0]) if len(dates) > 0 else None,
                contract_end=_to_eu_date(dates[1]) if len(dates) > 1 else None,
            )
            items.append(item)

    deduped: dict[tuple[str, float, float], ExtractedLineItem] = {}
    for it in items:
        key = (it.item, it.quantity, it.list_unit_price)
        if key not in deduped:
            deduped[key] = it

    return list(deduped.values())


def extract_document(pdf_path: Path) -> ExtractedDocument:
    pages = _extract_text_by_page(pdf_path)
    full_text = "\n".join(pages)

    quote_match = QUOTE_ID_RE.search(full_text)
    expiry_match = EXPIRY_RE.search(full_text)

    reseller, reseller_contact, end_user = _extract_parties(full_text)
    items = _extract_line_items(pages)

    if not items:
        raise ValueError("No line items detected using semantic extraction rules.")

    return ExtractedDocument(
        internal_id=(quote_match.group(1).strip() if quote_match else pdf_path.stem),
        expires=_to_eu_date(expiry_match.group(1).strip() if expiry_match else None),
        date=_to_eu_date(expiry_match.group(1).strip() if expiry_match else None),
        reseller=reseller,
        reseller_contact=reseller_contact,
        end_user=end_user,
        items=items,
        business_unit="Spain",
        currency=(items[0].currency if items else "USD"),
    )
