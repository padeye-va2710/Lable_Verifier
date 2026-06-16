from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from app.validation import validate_label_text
from app.ocr import extract_text_from_upload_bytes


MAX_WORKERS = 2


def validate_single_payload(file_payload: Dict[str, Any], application_data: Dict[str, Any]) -> Dict[str, Any]:
    filename = file_payload.get("filename", "unknown")
    file_bytes = file_payload["bytes"]

    try:
        ocr_result = extract_text_from_upload_bytes(file_bytes, filename)

        validation_result = validate_label_text(
            extracted_text=ocr_result.get("text", ""),
            application_data=application_data,
            ocr_confidence=ocr_result.get("confidence")
        )

        return {
            "filename": filename,
            "status": validation_result.get("status", "UNKNOWN"),
            "ocr_confidence": ocr_result.get("confidence"),
            "extracted_text": ocr_result.get("text", ""),
            "checks": validation_result.get("checks", [])
        }

    except Exception as exc:
        return {
            "filename": filename,
            "status": "ERROR",
            "error": str(exc),
            "checks": []
        }


def process_batch_parallel(file_payloads: List[Dict[str, Any]], application_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(validate_single_payload, payload, application_data): payload
            for payload in file_payloads
        }

        for future in as_completed(future_map):
            results.append(future.result())

    return results
