import re
from rapidfuzz import fuzz


REQUIRED_GOV_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, "
    "WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY "
    "BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF "
    "ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR "
    "OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)


def normalize_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def loose_normalize(value):
    value = normalize_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def contains_fuzzy(extracted_text, expected_value, threshold=85):
    extracted = normalize_text(extracted_text)
    expected = normalize_text(expected_value)

    if not expected:
        return True, 100

    if loose_normalize(expected) in loose_normalize(extracted):
        return True, 100

    score = fuzz.partial_ratio(expected.lower(), extracted.lower())
    return score >= threshold, round(score, 2)


def add_check(checks, name, status, expected=None, found=None, message=None, confidence=None):
    checks.append({
        "name": name,
        "status": status,
        "expected": expected,
        "found": found,
        "message": message,
        "confidence": confidence
    })


def validate_label_text(extracted_text, application_data, ocr_confidence=None):
    checks = []
    text = normalize_text(extracted_text)

    brand = application_data.get("brand_name")
    passed, score = contains_fuzzy(text, brand, threshold=85)
    add_check(
        checks,
        "Brand Name",
        "PASS" if passed else "FAIL",
        expected=brand,
        found="Detected in OCR text" if passed else "Not clearly detected",
        confidence=score
    )

    abv = application_data.get("abv")
    passed, score = contains_fuzzy(text, abv, threshold=90)
    add_check(
        checks,
        "ABV",
        "PASS" if passed else "FAIL",
        expected=abv,
        found="Detected in OCR text" if passed else "Not clearly detected",
        confidence=score
    )

    product_type = application_data.get("product_type")
    passed, score = contains_fuzzy(text, product_type, threshold=80)
    add_check(
        checks,
        "Product Type",
        "PASS" if passed else "WARNING",
        expected=product_type,
        found="Detected in OCR text" if passed else "Not clearly detected",
        confidence=score
    )

    net_contents = application_data.get("net_contents")
    passed, score = contains_fuzzy(text, net_contents, threshold=85)
    add_check(
        checks,
        "Net Contents",
        "PASS" if passed else "WARNING",
        expected=net_contents,
        found="Detected in OCR text" if passed else "Not clearly detected",
        confidence=score
    )

    producer = application_data.get("producer")
    passed, score = contains_fuzzy(text, producer, threshold=80)
    add_check(
        checks,
        "Producer",
        "PASS" if passed else "WARNING",
        expected=producer,
        found="Detected in OCR text" if passed else "Not clearly detected",
        confidence=score
    )

    warning_present, warning_score = contains_fuzzy(text, "GOVERNMENT WARNING:", threshold=90)
    add_check(
        checks,
        "Government Warning Prefix",
        "PASS" if warning_present else "FAIL",
        expected="GOVERNMENT WARNING:",
        found="Detected in OCR text" if warning_present else "Not clearly detected",
        confidence=warning_score
    )

    full_warning_present, full_warning_score = contains_fuzzy(text, REQUIRED_GOV_WARNING, threshold=70)
    add_check(
        checks,
        "Government Warning Statement",
        "PASS" if full_warning_present else "WARNING",
        expected=REQUIRED_GOV_WARNING,
        found="Detected or partially detected" if full_warning_present else "Not fully detected",
        confidence=full_warning_score
    )

    if ocr_confidence is not None:
        add_check(
            checks,
            "OCR Confidence",
            "PASS" if ocr_confidence >= 70 else "WARNING",
            expected="70 or higher",
            found=ocr_confidence,
            message="OCR confidence is acceptable." if ocr_confidence >= 70 else "OCR confidence is low. Manual review recommended.",
            confidence=ocr_confidence
        )

    statuses = [check["status"] for check in checks]

    if "FAIL" in statuses:
        overall_status = "FAIL"
    elif "WARNING" in statuses:
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    return {
        "status": overall_status,
        "checks": checks
    }
