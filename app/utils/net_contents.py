import re
from typing import Optional
from .text import clean_ocr_text


def normalize_net_contents(value) -> Optional[int]:
    if value is None:
        return None

    text = clean_ocr_text(str(value))

    if re.search(r"\b1\s*LITER\b", text) or re.search(r"\b1\s*L\b", text):
        return 1000

    if re.search(r"\b75\s*CL\b", text):
        return 750

    match = re.search(r"\b(\d+(?:\.\d+)?)\s*CL\b", text)
    if match:
        return int(round(float(match.group(1)) * 10))

    match = re.search(r"\b(\d+(?:\.\d+)?)\s*M\s*L\b", text)
    if match:
        return int(round(float(match.group(1))))

    match = re.search(r"\b(\d+(?:\.\d+)?)\s*ML\b", text)
    if match:
        return int(round(float(match.group(1))))

    match = re.search(r"\b(\d+(?:\.\d+)?)\s*LITER\b", text)
    if match:
        return int(round(float(match.group(1)) * 1000))

    match = re.search(r"\b(\d+(?:\.\d+)?)\s*L\b", text)
    if match:
        liters = float(match.group(1))
        if liters < 10:
            return int(round(liters * 1000))

    return None


def extract_net_contents(text: str) -> Optional[str]:
    text = clean_ocr_text(text)

    value = normalize_net_contents(text)

    if value is None:
        return None

    if value == 1000:
        return "1 L"

    return f"{value} ML"
