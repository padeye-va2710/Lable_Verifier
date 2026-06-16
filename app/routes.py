import json
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from .services.document_service import process_document, IMAGE_EXTENSIONS, PDF_EXTENSIONS
from .services.validation_service import validate_label
from .web import HTML

router = APIRouter()

SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS


@router.get("/", response_class=HTMLResponse)
def index():
    return HTML


async def upload_to_document(upload: UploadFile | None, view_name: str):
    if upload is None:
        return None

    contents = await upload.read()

    if not contents:
        return {
            "view": view_name,
            "filename": upload.filename,
            "text": "",
            "form_fields": {},
            "error": "File was empty or no file was selected.",
            "kind": "empty",
        }

    suffix = Path(upload.filename or "upload.png").suffix.lower() or ".png"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        processed = process_document(tmp_path)

        return {
            "view": view_name,
            "filename": upload.filename,
            "text": processed.get("text", ""),
            "form_fields": processed.get("form_fields", {}),
            "error": processed.get("error"),
            "kind": processed.get("kind"),
        }

    except Exception as exc:
        return {
            "view": view_name,
            "filename": upload.filename,
            "text": "",
            "form_fields": {},
            "error": str(exc),
            "kind": "error",
        }


def path_to_document(path: Path, view_name: str):
    try:
        processed = process_document(str(path))

        return {
            "view": view_name,
            "filename": path.name,
            "text": processed.get("text", ""),
            "form_fields": processed.get("form_fields", {}),
            "error": processed.get("error"),
            "kind": processed.get("kind"),
        }

    except Exception as exc:
        return {
            "view": view_name,
            "filename": path.name,
            "text": "",
            "form_fields": {},
            "error": str(exc),
            "kind": "error",
        }


@router.post("/validate")
async def validate(
    application_json: str = Form(...),
    label_text: str = Form(""),
    application_form: UploadFile | None = File(None),
    front_image: UploadFile | None = File(None),
    back_image: UploadFile | None = File(None),
    other_images: list[UploadFile] | None = File(None),
):
    application = json.loads(application_json)

    document_items = []
    image_views = []
    texts = []
    form_fields = {}

    pasted = label_text.strip()
    if pasted:
        document_items.append({
            "view": "pasted_text",
            "filename": "pasted_text",
            "text": pasted,
            "form_fields": {},
            "error": None,
            "kind": "text",
        })
        image_views.append("pasted_text")
        texts.append(pasted)

    for upload, view in [
        (application_form, "application_form"),
        (front_image, "front"),
        (back_image, "back"),
    ]:
        item = await upload_to_document(upload, view)

        if item:
            document_items.append(item)

            if item.get("form_fields"):
                form_fields.update(item["form_fields"])

            if item.get("text"):
                texts.append(item["text"])
                image_views.append(view)

    if other_images:
        for upload in other_images:
            item = await upload_to_document(upload, "other")

            if item:
                document_items.append(item)

                if item.get("form_fields"):
                    form_fields.update(item["form_fields"])

                if item.get("text"):
                    texts.append(item["text"])
                    image_views.append("other")

    if not texts:
        return {
            "error": "No readable image, PDF, or pasted label text was provided.",
            "document_items": document_items,
        }

    combined_text = "\n\n".join(texts)

    result = validate_label(
        application=application,
        label_text=combined_text,
        image_count=len(image_views),
        image_views=image_views,
    )

    result["ocr_text"] = combined_text
    result["image_views"] = image_views
    result["document_items"] = document_items
    result["form_fields"] = form_fields

    return result


@router.post("/batch-validate")
async def batch_validate(
    application_json: str = Form(...),
    images: list[UploadFile] | None = File(None),
    forms: list[UploadFile] | None = File(None),
    zip_file: UploadFile | None = File(None),
):
    application = json.loads(application_json)
    batch_results = []

    async def evaluate_upload(upload: UploadFile, view_name: str):
        item = await upload_to_document(upload, view_name)

        if not item or item.get("error") or not item.get("text"):
            return {
                "filename": upload.filename,
                "summary": {"matches": 0, "mismatches": 0, "reviews": 1},
                "results": [{
                    "field": "Document OCR",
                    "application": "Readable image or PDF form",
                    "label": item.get("error") if item else "no file",
                    "status": "review",
                    "confidence": 0,
                    "rule": "Document could not be processed. Try JPG, PNG, or a readable PDF.",
                }],
                "ocr_text": "",
                "document_items": [item] if item else [],
                "form_fields": item.get("form_fields", {}) if item else {},
            }

        result = validate_label(
            application=application,
            label_text=item["text"],
            image_count=1,
            image_views=[view_name],
        )

        result["filename"] = upload.filename
        result["ocr_text"] = item["text"]
        result["document_items"] = [item]
        result["form_fields"] = item.get("form_fields", {})

        return result

    if images:
        for image in images:
            batch_results.append(await evaluate_upload(image, "batch_image"))

    if forms:
        for form in forms:
            batch_results.append(await evaluate_upload(form, "batch_form"))

    if zip_file:
        contents = await zip_file.read()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            zip_path = tmpdir_path / "upload.zip"
            zip_path.write_bytes(contents)

            try:
                with zipfile.ZipFile(zip_path, "r") as z:
                    z.extractall(tmpdir)
            except Exception as exc:
                return {"error": f"Could not read ZIP file: {exc}"}

            files = [
                p for p in tmpdir_path.rglob("*")
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
            ]

            for path in files:
                item = path_to_document(path, "zip_document")

                if item.get("error") or not item.get("text"):
                    batch_results.append({
                        "filename": path.name,
                        "summary": {"matches": 0, "mismatches": 0, "reviews": 1},
                        "results": [{
                            "field": "Document OCR",
                            "application": "Readable image or PDF form",
                            "label": item.get("error"),
                            "status": "review",
                            "confidence": 0,
                            "rule": "Document could not be processed.",
                        }],
                        "ocr_text": "",
                        "document_items": [item],
                        "form_fields": item.get("form_fields", {}),
                    })
                    continue

                result = validate_label(
                    application=application,
                    label_text=item["text"],
                    image_count=1,
                    image_views=["zip_document"],
                )

                result["filename"] = path.name
                result["ocr_text"] = item["text"]
                result["document_items"] = [item]
                result["form_fields"] = item.get("form_fields", {})
                batch_results.append(result)

    if not batch_results:
        return {"error": "No images, PDFs, forms, or ZIP file were provided."}

    return {"batch_results": batch_results}
