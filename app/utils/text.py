import re
from difflib import SequenceMatcher


OCR_FIXES = {
    # Alcohol / ABV cleanup
    "ALC./VOL.": "ALC VOL",
    "ALC/VOL": "ALC VOL",
    "ALC.VOL": "ALC VOL",
    "ALC VOL.": "ALC VOL",
    "ALC. VOL.": "ALC VOL",
    "ALCOHOL/VOLUME": "ALCOHOL VOLUME",
    "ALCOHOL/VOL": "ALCOHOL VOL",
    "ALOOHOL": "ALCOHOL",
    "ALOOHOV": "ALCOHOL",
    "ALOOHOVVOU": "ALCOHOL VOLUME",
    "ALOOHOVVOL": "ALCOHOL VOLUME",
    "ALOHOL": "ALCOHOL",
    "ALAN": "ALC",
    "ALL": "ALC",
    "ALI": "ALC",
    "VOLUT": "VOL",

    # Net contents cleanup
    "TLITER": "1 LITER",
    "T LITER": "1 LITER",
    "1LITER": "1 LITER",
    "ILITER": "1 LITER",
    "I LITER": "1 LITER",
    "1 LT": "1 L",
    "750M": "750ML",
    "75OML": "750ML",
    "730M": "750ML",
    "7S0ML": "750ML",
    "150WL": "750ML",
    "150ML": "750ML",
    "150 ML": "750 ML",
    "1SO ML": "750 ML",
    "1S0 ML": "750 ML",
    "1750 ML": "750 ML",
    "175 CL": "75 CL",
    "70a": "750ML",
    "70A": "750ML",

    # Sulfites cleanup
    "SULPHITES": "SULFITES",
    "SULFATES": "SULFITES",
    "SULFITTER": "SULFITES",
    "SULETES": "SULFITES",
    "SULPHT": "SULFITES",
    "SOLFITI": "SULFITES",
    "SOLFITE": "SULFITES",
    "CONTAINS QT": "CONTAINS SULFITES",

    # Warning cleanup
    "GOVERNMENT WARMING": "GOVERNMENT WARNING",
    "NMENT WARNING": "GOVERNMENT WARNING",
    "OOT MENT WARNING": "GOVERNMENT WARNING",
    "GOVERNME T WARNING": "GOVERNMENT WARNING",
    "ACCORDNG": "ACCORDING",
    "BIRTHD": "BIRTH",
    "DEFECIS": "DEFECTS",
    "BEERS": "BEVERAGES",
    "A.COHOUC": "ALCOHOLIC",
    "DRIVEACAR": "DRIVE A CAR",

    # Common OCR producer mistakes
    "INE.": "INC.",
    " INE ": " INC ",
    "DISTILLERY INE": "DISTILLERY INC",
    "MAKER’S": "MAKER'S",
    "MAKERS": "MAKER'S",
}


def clean_ocr_text(text: str) -> str:
    text = text or ""
    text = text.upper()

    for bad, good in OCR_FIXES.items():
        text = text.replace(bad, good)

    text = re.sub(r"\b(12[0-9])\s*%\s*ALC\b", lambda m: f"12.{m.group(1)[2]}% ALC", text)
    text = re.sub(r"\b(13[0-9])\s*%\s*ALC\b", lambda m: f"13.{m.group(1)[2]}% ALC", text)

    return text


def normalize_loose(value: str) -> str:
    value = value or ""
    value = value.upper()
    value = re.sub(r"[^A-Z0-9.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fuzzy_score(a: str, b: str) -> float:
    left = normalize_loose(a)
    right = normalize_loose(b)

    if not left or not right:
        return 0.0

    if left in right:
        return 100.0

    return round(SequenceMatcher(None, left, right).ratio() * 100, 2)
