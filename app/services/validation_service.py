from typing import Dict, Any, List
import re

from app.validators.common import result, check_required_term, summarize
from app.utils.text import clean_ocr_text, fuzzy_score, normalize_loose
from app.utils.alcohol import extract_abv
from app.utils.net_contents import extract_net_contents, normalize_net_contents
from app.utils.warning import warning_score, warning_status
from app.utils.claims import sulfites_present, organic_present


BEER_TYPES = [
    "LAGER BEER", "LIGHT BEER", "BEER", "LAGER", "ALE", "IPA",
    "STOUT", "PORTER", "PILSNER", "MALT BEVERAGE"
]


def bool_setting(application: Dict[str, Any], key: str, default: bool = False) -> bool:
    return bool(application.get(key, default))


def category_defaults(product_category: str) -> Dict[str, bool]:
    product_category = product_category.lower()

    if product_category == "beer":
        return {
            "class_type_required": True,
            "abv_required": False,
            "government_warning_required": True,
            "producer_required": True,
            "origin_required": False,
            "sulfites_required": False,
            "organic_required": False,
        }

    if product_category == "spirits":
        return {
            "class_type_required": True,
            "abv_required": True,
            "government_warning_required": True,
            "producer_required": True,
            "origin_required": False,
            "sulfites_required": False,
            "organic_required": False,
        }

    return {
        "class_type_required": True,
        "abv_required": True,
        "government_warning_required": True,
        "producer_required": True,
        "origin_required": False,
        "sulfites_required": False,
        "organic_required": False,
    }


def has_front_and_back(image_views: List[str]) -> bool:
    views = set(image_views or [])
    return "front" in views and "back" in views


def infer_beer_type(clean_text: str) -> str | None:
    loose = normalize_loose(clean_text)

    for beer_type in BEER_TYPES:
        if normalize_loose(beer_type) in loose:
            return beer_type.title()

    if "BUDWEISER" in loose or "BUD LIGHT" in loose:
        return "Lager Beer"

    return None


def class_type_match(product_category: str, expected: str, clean_text: str):
    expected = (expected or "").strip()
    loose = normalize_loose(clean_text)

    if product_category == "beer":
        inferred = infer_beer_type(clean_text)

        if expected and normalize_loose(expected) in loose:
            return expected, "found in label text", "match", 100

        if expected and inferred:
            expected_tokens = set(normalize_loose(expected).split())
            inferred_tokens = set(normalize_loose(inferred).split())
            if expected_tokens & inferred_tokens:
                return inferred, "beer class/type inferred from label", "match", 85

        if inferred:
            return inferred, "beer class/type inferred from label", "match", 80

        return expected or "Beer / Malt Beverage class/type required", "not confidently found", "review", 0

    if expected:
        score = fuzzy_score(expected, clean_text)
        return expected, "found in label text" if score >= 80 else "not confidently found", "match" if score >= 80 else "review", score

    return "Class/type required", "not provided", "review", 0


def ocr_quality(clean_text: str) -> Dict[str, Any]:
    normalized = normalize_loose(clean_text)
    words = re.findall(r"[A-Z0-9]{2,}", normalized)
    count = len(words)

    score = warning_score(clean_text)
    useful_terms = sum(
        1 for t in ["WARNING", "BEER", "ALC", "VOL", "ML", "OZ", "PROOF", "BREWED", "BOTTLED"]
        if t in normalized
    )

    if count >= 90 or useful_terms >= 5:
        quality = "high"
    elif count >= 30 or useful_terms >= 2:
        quality = "medium"
    else:
        quality = "low"

    return {
        "quality": quality,
        "word_count": count,
        "warning_score": score,
        "useful_label_terms": useful_terms,
    }


def validate_label(
    application: Dict[str, Any],
    label_text: str,
    image_count: int = 1,
    image_views: List[str] | None = None,
) -> Dict[str, Any]:
    results = []
    image_views = image_views or []
    clean_text = clean_ocr_text(label_text)

    product_category = application.get("product_category", "wine").lower()
    defaults = category_defaults(product_category)

    brand_expected = application.get("brand_name", "")
    brand_score = fuzzy_score(brand_expected, clean_text)

    results.append(result(
        "Brand Name",
        brand_expected,
        "found in label text" if brand_score >= 80 else "not confidently found",
        "match" if brand_score >= 80 else "review",
        brand_score,
        "Required baseline label element for beer, wine, and distilled spirits.",
    ))

    class_app, class_label, class_status, class_conf = class_type_match(
        product_category,
        application.get("class_type", ""),
        clean_text,
    )

    if application.get("class_type") or defaults["class_type_required"]:
        results.append(result(
            "Class / Type",
            class_app,
            class_label,
            class_status,
            class_conf,
            "Required class/type designation. Beer examples include beer, ale, lager, stout, porter, pilsner, or malt beverage.",
        ))

    expected_abv = application.get("alcohol_content")
    label_abv = extract_abv(clean_text)

    abv_required = bool_setting(application, "abv_required", defaults["abv_required"])
    abv_declared = label_abv is not None

    if abv_required or abv_declared:
        abv_ok = False

        if expected_abv is not None and label_abv is not None:
            tolerance = 0.10
            if product_category == "wine" and float(expected_abv) < 14:
                tolerance = 0.30
            if product_category == "beer":
                tolerance = 0.30

            abv_ok = abs(float(expected_abv) - float(label_abv)) <= tolerance

        results.append(result(
            "Alcohol Content",
            expected_abv,
            label_abv,
            "match" if abv_ok else "mismatch",
            100 if abv_ok else 0,
            "Wine and distilled spirits require ABV. Beer ABV is optional federally unless declared or otherwise required.",
        ))

    expected_net_raw = application.get("net_contents", "")
    expected_net_ml = normalize_net_contents(expected_net_raw)
    label_net = extract_net_contents(clean_text)
    label_net_ml = normalize_net_contents(label_net)
    net_ok = expected_net_ml is not None and label_net_ml is not None and expected_net_ml == label_net_ml

    results.append(result(
        "Net Contents",
        expected_net_raw,
        label_net,
        "match" if net_ok else "review" if label_net is None else "mismatch",
        100 if net_ok else 0,
        "Required baseline label element. If OCR cannot read the volume, the item is flagged for manual review.",
    ))

    if bool_setting(application, "government_warning_required", defaults["government_warning_required"]):
        score = warning_score(clean_text)
        base_status = warning_status(score)

        if base_status == "match":
            status = "match"
            label = "present"
        elif image_count <= 1 or not has_front_and_back(image_views):
            status = "review"
            label = "not visible on submitted label view"
        else:
            status = "review" if score >= 35 else "mismatch"
            label = "possible/partial" if score >= 35 else "missing or altered"

        results.append(result(
            "Government Warning",
            "Standard warning required",
            label,
            status,
            score,
            "Mandatory health warning. OCR-damaged warnings are scored by required warning concepts and may be routed to manual review.",
        ))

    if product_category == "wine" and bool_setting(application, "sulfites_required", defaults["sulfites_required"]):
        found = sulfites_present(clean_text)
        results.append(result(
            "Sulfites Declaration",
            "Contains sulfites required",
            "present" if found else "missing",
            "match" if found else "mismatch",
            100 if found else 0,
            "Wine containing 10 ppm or more sulfur dioxide requires a sulfites declaration.",
        ))

    if product_category != "wine" and bool_setting(application, "sulfites_required", False):
        results.append(result(
            "Sulfites Declaration",
            "Not normally applicable to this category",
            "skipped",
            "review",
            0,
            "Sulfites review is wine-specific in this prototype.",
        ))

    if bool_setting(application, "producer_required", defaults["producer_required"]):
        results.append(check_required_term(
            "Producer / Bottler",
            application.get("producer_name", ""),
            clean_text,
            "Required baseline label element: name and address of producer, bottler, or importer.",
        ))

    if bool_setting(application, "origin_required", defaults["origin_required"]):
        results.append(check_required_term(
            "Country of Origin",
            application.get("country_of_origin", ""),
            clean_text,
            "Required if imported.",
        ))

    if bool_setting(application, "organic_required", defaults["organic_required"]):
        found = organic_present(clean_text)
        results.append(result(
            "Organic Claims",
            "Organic claim review required",
            "organic claim present" if found else "not found",
            "review" if found else "mismatch",
            100 if found else 0,
            "Organic claims are flagged for manual review rather than auto-approval.",
        ))

    if product_category == "spirits":
        sfov_ok = (
            brand_score >= 80
            and label_abv is not None
            and application.get("class_type", "")
            and normalize_loose(application.get("class_type", "")) in normalize_loose(clean_text)
        )

        results.append(result(
            "Field of Vision",
            "Brand, class/type, and exact ABV in same field of vision",
            "appears present in submitted OCR" if sfov_ok else "manual review required",
            "review",
            50 if sfov_ok else 0,
            "Distilled spirits require brand, class/type, and alcohol content in the same field of vision; final confirmation remains manual.",
        ))

    if bool_setting(application, "formula_review_required", False):
        results.append(result(
            "Formula Approval",
            "Formula review required",
            "manual review required",
            "review",
            0,
            "Flavored products or unusual ingredients may require TTB formula approval before COLA submission.",
        ))

    quality = ocr_quality(clean_text)

    return {
        "summary": summarize(results),
        "results": results,
        "metadata": {
            "product_category": product_category,
            "image_count": image_count,
            "image_views": image_views,
            "front_and_back_supplied": has_front_and_back(image_views),
            "ocr_quality": quality,
        },
    }
