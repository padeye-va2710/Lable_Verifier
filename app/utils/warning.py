from .text import clean_ocr_text, normalize_loose

STANDARD_WARNING = (
    "GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT "
    "DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. "
    "(2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE "
    "MACHINERY, AND MAY CAUSE HEALTH PROBLEMS."
)


def warning_score(text: str) -> float:
    cleaned = normalize_loose(clean_ocr_text(text))

    required_context = [
        "SURGEON GENERAL",
        "PREGNANCY",
        "BIRTH",
        "DEFECT",
        "DRIVE",
        "OPERATE",
        "MACHINERY",
        "HEALTH",
    ]

    hits = sum(1 for keyword in required_context if normalize_loose(keyword) in cleaned)

    if "WARNING" not in cleaned and hits < 3:
        return 0

    return round((hits / len(required_context)) * 100, 2)


def warning_status(score: float) -> str:
    if score >= 50:
        return "match"
    if score >= 30:
        return "review"
    return "mismatch"
