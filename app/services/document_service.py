from pathlib import Path
from typing import Dict, Any
import tempfile

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from .ocr_service import ocr_image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff"}
PDF_EXTENSIONS = {".pdf"}


def extract_pdf_form_fields(path: str) -> Dict[str, Any]:
    if fitz is None:
        return {}

    fields = {}

    try:
        doc = fitz.open(path)
        for page_index, page in enumerate(doc):
            widgets = page.widgets() or []
            for widget in widgets:
                name = widget.field_name or f"page_{page_index + 1}_unnamed"
                value = widget.field_value
                if value not in [None, ""]:
                    fields[name] = value
        doc.close()
    except Exception:
        return {}

    return fields


def extract_pdf_text(path: str) -> str:
    if fitz is None:
        return ""

    parts = []

    try:
        doc = fitz.open(path)
        for i, page in enumerate(doc):
            text = page.get_text("text") or ""
            if text.strip():
                parts.append(f"[PDF_PAGE_TEXT={i + 1}]\n{text.strip()}")
        doc.close()
    except Exception as exc:
        parts.append(f"[PDF_TEXT_ERROR] {exc}")

    return "\n\n".join(parts).strip()


def ocr_pdf_pages(path: str, max_pages: int = 5) -> str:
    if fitz is None:
        return "[PDF_OCR_ERROR] PyMuPDF is not installed."

    parts = []

    try:
        doc = fitz.open(path)

        page_count = min(len(doc), max_pages)

        for i in range(page_count):
            try:
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(pix.tobytes("png"))
                    tmp_path = tmp.name

                text = ocr_image(tmp_path)

                if text.strip():
                    parts.append(f"[PDF_PAGE_OCR={i + 1}]\n{text.strip()}")

            except Exception as page_exc:
                parts.append(f"[PDF_PAGE_OCR_ERROR={i + 1}] {page_exc}")

        doc.close()

    except Exception as exc:
        return f"[PDF_OPEN_ERROR] {exc}"

    return "\n\n".join(parts).strip()


def process_document(path: str) -> Dict[str, Any]:
    p = Path(path)
    ext = p.suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        try:
            text = ocr_image(str(p))
            return {"kind": "image", "text": text, "form_fields": {}, "error": None}
        except Exception as exc:
            return {"kind": "image", "text": "", "form_fields": {}, "error": str(exc)}

    if ext in PDF_EXTENSIONS:
        if fitz is None:
            return {
                "kind": "pdf",
                "text": "",
                "form_fields": {},
                "error": "PyMuPDF is not installed. Run: pip install PyMuPDF",
            }

        try:
            pdf_text = extract_pdf_text(str(p))
            pdf_ocr = ocr_pdf_pages(str(p))
            fields = extract_pdf_form_fields(str(p))

            combined = "\n\n".join(x for x in [pdf_text, pdf_ocr] if x and x.strip())

            if not combined.strip() and not fields:
                return {
                    "kind": "pdf",
                    "text": "",
                    "form_fields": {},
                    "error": "PDF could be opened but no readable text, form fields, or OCR text was extracted.",
                }

            return {
                "kind": "pdf",
                "text": combined,
                "form_fields": fields,
                "error": None,
            }

        except Exception as exc:
            return {
                "kind": "pdf",
                "text": "",
                "form_fields": {},
                "error": f"PDF processing failed: {exc}",
            }

    return {
        "kind": "unsupported",
        "text": "",
        "form_fields": {},
        "error": f"Unsupported file type: {ext}",
    }
