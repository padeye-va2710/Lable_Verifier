import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import HTMLResponse

from app.ocr import extract_text_from_upload_bytes
from app.validation import validate_label_text


router = APIRouter()
MAX_WORKERS = 2


def _safe(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _build_application_data(
    brand_name: str,
    abv: str,
    product_type: str,
    net_contents: str,
    producer: str,
) -> Dict[str, str]:
    return {
        "brand_name": brand_name.strip(),
        "abv": abv.strip(),
        "product_type": product_type.strip(),
        "net_contents": net_contents.strip(),
        "producer": producer.strip(),
    }


def _process_uploaded_file(payload: Dict[str, Any], application_data: Dict[str, str]) -> Dict[str, Any]:
    filename = payload["filename"]
    file_type = payload["type"]
    file_bytes = payload["bytes"]

    try:
        ocr_result = extract_text_from_upload_bytes(file_bytes, filename)
        extracted_text = ocr_result.get("text", "")
        confidence = ocr_result.get("confidence")

        result = {
            "filename": filename,
            "file_type": file_type,
            "ocr_confidence": confidence,
            "extracted_text": extracted_text,
            "status": "OCR_ONLY",
            "checks": [],
        }

        if file_type == "label":
            validation_result = validate_label_text(
                extracted_text=extracted_text,
                application_data=application_data,
                ocr_confidence=confidence,
            )
            result["status"] = validation_result.get("status", "UNKNOWN")
            result["checks"] = validation_result.get("checks", [])

        return result

    except Exception as exc:
        return {
            "filename": filename,
            "file_type": file_type,
            "status": "ERROR",
            "error": str(exc),
            "ocr_confidence": None,
            "extracted_text": "",
            "checks": [],
        }


@router.get("/bulk", response_class=HTMLResponse)
def bulk_page():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Bulk Upload - Alcohol Label Verification</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 30px;
            background: #f7f7f7;
            color: #222;
        }
        .container {
            max-width: 1000px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,.12);
        }
        h1 {
            margin-top: 0;
        }
        label {
            font-weight: bold;
            display: block;
            margin-top: 14px;
        }
        input, select {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            font-size: 16px;
        }
        .section {
            margin-top: 25px;
            padding: 18px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #fafafa;
        }
        .button {
            background: #1f6feb;
            color: white;
            border: none;
            padding: 14px 24px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 20px;
        }
        .button:hover {
            background: #185abc;
        }
        .back {
            display: inline-block;
            margin-bottom: 20px;
            text-decoration: none;
            font-weight: bold;
        }
        .hint {
            color: #555;
            font-size: 14px;
        }
    </style>
</head>
<body>
<div class="container">
    <a class="back" href="/">← Back to Main Page</a>

    <h1>Bulk Upload & Validation</h1>

    <p>
        Use this page to upload multiple application forms, label images, and label PDFs.
        The application information below will be used to validate each uploaded label.
    </p>

    <form action="/bulk-validate" enctype="multipart/form-data" method="post">

        <div class="section">
            <h2>Application Information</h2>

            <label for="brand_name">Brand Name</label>
            <input id="brand_name" name="brand_name" type="text" placeholder="Example: Stone's Throw">

            <label for="abv">Alcohol By Volume / ABV</label>
            <input id="abv" name="abv" type="text" placeholder="Example: 5.0%">

            <label for="product_type">Product Type</label>
            <select id="product_type" name="product_type">
                <option value="">Select product type</option>
                <option value="beer">Beer</option>
                <option value="wine">Wine</option>
                <option value="distilled spirits">Distilled Spirits</option>
                <option value="malt beverage">Malt Beverage</option>
            </select>

            <label for="net_contents">Net Contents</label>
            <input id="net_contents" name="net_contents" type="text" placeholder="Example: 12 fl oz, 750 mL, 1 L">

            <label for="producer">Producer / Bottler / Importer</label>
            <input id="producer" name="producer" type="text" placeholder="Example: Example Brewing Company">
        </div>

        <div class="section">
            <h2>Application Forms</h2>
            <p class="hint">Upload COLA/application forms here. PDFs are supported.</p>
            <input name="forms" type="file" multiple>
        </div>

        <div class="section">
            <h2>Label Images or PDFs</h2>
            <p class="hint">Upload label artwork, photos, scans, images, or PDFs here.</p>
            <input name="labels" type="file" multiple>
        </div>

        <button class="button" type="submit">Validate Bulk Upload</button>
    </form>
</div>
</body>
</html>
"""


@router.post("/bulk-validate", response_class=HTMLResponse)
async def bulk_validate(
    brand_name: str = Form(""),
    abv: str = Form(""),
    product_type: str = Form(""),
    net_contents: str = Form(""),
    producer: str = Form(""),
    forms: List[UploadFile] = File(default=[]),
    labels: List[UploadFile] = File(default=[]),
):
    application_data = _build_application_data(
        brand_name=brand_name,
        abv=abv,
        product_type=product_type,
        net_contents=net_contents,
        producer=producer,
    )

    file_payloads: List[Dict[str, Any]] = []

    for uploaded_file in forms:
        file_payloads.append({
            "type": "form",
            "filename": uploaded_file.filename,
            "bytes": await uploaded_file.read(),
        })

    for uploaded_file in labels:
        file_payloads.append({
            "type": "label",
            "filename": uploaded_file.filename,
            "bytes": await uploaded_file.read(),
        })

    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(_process_uploaded_file, payload, application_data)
            for payload in file_payloads
        ]

        for future in as_completed(futures):
            results.append(future.result())

    rows = ""

    for result in results:
        status = result.get("status", "UNKNOWN")
        status_class = status.lower()

        checks_html = ""
        for check in result.get("checks", []):
            checks_html += f"""
            <li>
                <strong>{_safe(check.get("name"))}</strong>:
                {_safe(check.get("status"))}
                — {_safe(check.get("message") or check.get("found") or "")}
            </li>
            """

        if not checks_html:
            checks_html = "<li>OCR completed. No label validation checks were run for this file type.</li>"

        extracted_preview = _safe(result.get("extracted_text", ""))[:1000]

        rows += f"""
        <tr>
            <td>{_safe(result.get("filename"))}</td>
            <td>{_safe(result.get("file_type"))}</td>
            <td class="{status_class}">{_safe(status)}</td>
            <td>{_safe(result.get("ocr_confidence"))}</td>
            <td><ul>{checks_html}</ul></td>
            <td><pre>{extracted_preview}</pre></td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Bulk Validation Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 30px;
            background: #f7f7f7;
        }}
        .container {{
            max-width: 1300px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,.12);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            vertical-align: top;
        }}
        th {{
            background: #f0f0f0;
        }}
        .pass {{
            color: green;
            font-weight: bold;
        }}
        .warning {{
            color: #b36b00;
            font-weight: bold;
        }}
        .fail, .error {{
            color: red;
            font-weight: bold;
        }}
        pre {{
            white-space: pre-wrap;
            max-height: 220px;
            overflow: auto;
            background: #fafafa;
            padding: 8px;
        }}
        .button {{
            display: inline-block;
            background: #1f6feb;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            text-decoration: none;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>Bulk Validation Results</h1>

    <p><strong>Total Files Processed:</strong> {len(file_payloads)}</p>
    <p><strong>Parallel Workers:</strong> {MAX_WORKERS}</p>

    <a class="button" href="/bulk">Run Another Bulk Upload</a>
    <a class="button" href="/">Back to Main Page</a>

    <table>
        <thead>
            <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Status</th>
                <th>OCR Confidence</th>
                <th>Checks</th>
                <th>Extracted Text Preview</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</div>
</body>
</html>
"""
