from .text import clean_ocr_text, normalize_loose

SULFITE_WORDS = [
    "SULFITES", "SULPHITES", "SULFATES", "SULFITE",
    "SULFITTE", "SULFITTER", "SOLFITI", "SOLFITE", "SULFIT"
]

ORGANIC_KEYWORDS = [
    "ORGANIC", "CERTIFIED ORGANIC", "MADE WITH ORGANIC",
    "USDA ORGANIC", "CCOF", "CERTIFIED SUSTAINABLE"
]


def sulfites_present(text: str) -> bool:
    cleaned = normalize_loose(clean_ocr_text(text))
    return any(normalize_loose(word) in cleaned for word in SULFITE_WORDS)


def organic_present(text: str) -> bool:
    cleaned = normalize_loose(clean_ocr_text(text))
    return any(normalize_loose(term) in cleaned for term in ORGANIC_KEYWORDS)
