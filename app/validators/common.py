from typing import Dict, Any
from app.utils.text import clean_ocr_text, normalize_loose, fuzzy_score


def result(field, application, label, status, confidence, rule) -> Dict[str, Any]:
    return {
        "field": field,
        "application": application,
        "label": label,
        "status": status,
        "confidence": confidence,
        "rule": rule,
    }


def check_required_term(field: str, expected: str, label_text: str, rule: str):
    expected = expected or ""
    clean_text = clean_ocr_text(label_text)

    if not expected:
        return result(
            field,
            "",
            "not provided",
            "review",
            0,
            "Application field was not provided, so this item could not be checked.",
        )

    if normalize_loose(expected) in normalize_loose(clean_text):
        score = 100.0
        status = "match"
    else:
        score = fuzzy_score(expected, clean_text)
        status = "review" if score >= 50 else "mismatch"

    return result(
        field,
        expected,
        "found in label text" if score >= 80 else "not confidently found",
        status,
        score,
        rule,
    )


def summarize(results):
    return {
        "matches": sum(r["status"] == "match" for r in results),
        "mismatches": sum(r["status"] == "mismatch" for r in results),
        "reviews": sum(r["status"] == "review" for r in results),
    }
