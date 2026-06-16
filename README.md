# Alcohol Label Verification Prototype

A lean proof-of-concept for helping TTB-style compliance agents compare application data against alcohol label artwork.

## What it does

- Accepts application data as JSON.
- Accepts a label image or pasted OCR text.
- Extracts/uses label text.
- Compares important fields with field-specific rules.
- Returns a side-by-side review table.
- Supports a simple batch validation endpoint.

## Why this approach

This prototype favors local OCR plus deterministic validation rules instead of relying entirely on cloud AI APIs. That fits the stakeholder constraints: speed, government network limits, simple UX, and human-in-the-loop review.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

For image OCR, install the Tesseract binary:

- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- Windows: install from the UB Mannheim Tesseract build, then ensure `tesseract.exe` is on PATH.

You can test without OCR by pasting label text into the UI.

## Run

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Test

```bash
pytest
```

## Key assumptions

- This is a standalone prototype, not a COLA integration.
- The tool assists reviewers; it does not approve or reject labels automatically.
- Brand names allow case/punctuation variation.
- Government warning text is strict because stakeholders said wording and capitalization matter.
- ABV is treated as numeric; proof is converted to ABV when present.

## Tradeoffs

- Tesseract is simple and local, but PaddleOCR or EasyOCR may improve accuracy on angled/glare-heavy images.
- The prototype does not store documents or application data.
- Batch mode currently accepts JSON records; a production version should support CSV plus image bundles.
- No authentication is included because the take-home asks for a prototype.

## Example application JSON

```json
{
  "brand_name": "OLD TOM DISTILLERY",
  "class_type": "Kentucky Straight Bourbon Whiskey",
  "alcohol_content": 45,
  "net_contents": "750 mL"
}
```

## Example label text

```text
OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
GOVERNMENT WARNING: (1) ACCORDING TO THE SURGEON GENERAL, WOMEN SHOULD NOT DRINK ALCOHOLIC BEVERAGES DURING PREGNANCY BECAUSE OF THE RISK OF BIRTH DEFECTS. (2) CONSUMPTION OF ALCOHOLIC BEVERAGES IMPAIRS YOUR ABILITY TO DRIVE A CAR OR OPERATE MACHINERY, AND MAY CAUSE HEALTH PROBLEMS.
```
