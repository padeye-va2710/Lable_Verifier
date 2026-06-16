import re
from typing import Optional
from .text import clean_ocr_text


def extract_abv(text: str) -> Optional[float]:
    text = clean_ocr_text(text)
    candidates = []

    percent_patterns = [
        r"(\d+(?:\.\d+)?)\s*%\s*ALC\s*/?\s*VOL",
        r"(\d+(?:\.\d+)?)\s*%\s*ALC\.?\s*VOL\.?",
        r"(\d+(?:\.\d+)?)\s*%\s*ALCOHOL\s*/?\s*VOLUME",
        r"(\d+(?:\.\d+)?)\s*%\s*ALCOHOL\s*VOL",
        r"(\d+(?:\.\d+)?)\s*%\s*BY\s*VOL\.?",
        r"ALC\.?\s*(\d+(?:\.\d+)?)\s*%\s*(?:BY\s*)?VOL\.?",
        r"(\d+(?:\.\d+)?)\s*%\s*ALC\b",
    ]

    for pattern in percent_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = float(match.group(1))
            if 0 < value <= 80:
                candidates.append(value)

    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*PROOF", text, re.IGNORECASE):
        proof = float(match.group(1))
        if 40 <= proof <= 190:
            candidates.append(proof / 2)

    if not candidates:
        return None

    return candidates[0]
