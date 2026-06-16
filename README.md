# AI-Powered Alcohol Label Verification Prototype

## Overview

The Alcohol Label Verification Prototype is a proof-of-concept application designed to assist TTB label compliance agents by automating routine label verification tasks.

The application uses OCR (Optical Character Recognition) and rule-based validation to compare alcohol beverage label information against application data and identify potential mismatches, missing mandatory elements, and items requiring manual review.

This prototype was developed as part of an engineering assessment focused on improving the efficiency of alcohol beverage label reviews while maintaining compliance with TTB labeling requirements.

---

## Key Features

### Application Builder

Create label applications directly within the user interface without manually editing JSON.

Supported product categories:

* Distilled Spirits
* Wine
* Beer / Malt Beverage

Application fields include:

* Brand Name
* Class / Type
* Alcohol Content (ABV)
* Net Contents
* Producer / Bottler
* Country of Origin
* Vintage
* Appellation

---

### Label Image Validation

Supports:

* Front Label Image
* Back Label Image
* Additional Label Images

OCR is performed automatically using Tesseract.

Images are combined into a single review package before validation.

---

### PDF Application Processing

Supports:

* TTB Application Forms
* PDF Label Files
* Fillable PDF Forms

Extracts:

* Form Fields
* Embedded PDF Text
* OCR Text from PDF Pages

Uses:

* PyMuPDF
* Tesseract OCR

---

### Batch Processing

Supports:

* Multiple Label Images
* Multiple PDF Forms
* ZIP File Uploads

Designed to simulate high-volume importer submissions.

---

### TTB Rule Validation

Current validation includes:

#### Common Requirements

* Brand Name
* Class / Type
* Net Contents
* Producer / Bottler
* Country of Origin
* Government Warning

#### Wine Requirements

* ABV Verification
* Sulfites Declaration
* Vintage Review
* Appellation Review

#### Distilled Spirits Requirements

* ABV Verification
* Class / Type Verification
* Same Field of Vision Review
* Government Warning

#### Beer Requirements

* Class / Type Verification
* Net Contents Verification
* Government Warning
* Optional ABV Review

---

### OCR Quality Scoring

The application estimates OCR quality and flags submissions for manual review when OCR confidence is low.

Metrics include:

* Word Count
* Warning Statement Score
* Useful Label Terms Detected
* Overall OCR Quality Rating

---

## Architecture

```text
app/
│
├── main.py
├── routes.py
├── web.py
│
├── services/
│   ├── document_service.py
│   ├── validation_service.py
│   └── ocr_service.py
│
├── validators/
│   ├── common.py
│
├── utils/
│   ├── alcohol.py
│   ├── claims.py
│   ├── net_contents.py
│   ├── text.py
│   └── warning.py
│
└── static/
```

---

## Technology Stack

Backend

* Python 3.14
* FastAPI
* Uvicorn

OCR

* Tesseract OCR
* Pillow

PDF Processing

* PyMuPDF (fitz)

Frontend

* HTML
* CSS
* JavaScript

Deployment

* Ubuntu 24.04+
* Systemd
* EC2

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd label-verifier
```

### Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Requirements

```bash
pip install -r requirements.txt
```

Required packages include:

```text
fastapi
uvicorn
python-multipart
pillow
pytesseract
PyMuPDF
```

---

## Install Tesseract

Ubuntu:

```bash
sudo apt update

sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-eng
```

Verify:

```bash
tesseract --version
```

---

## Running Locally

```bash
source .venv/bin/activate

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000
```

Open:

```text
http://localhost:8000
```

---

## Running as a Service

Create:

```text
/etc/systemd/system/label-verifier.service
```

Contents:

```ini
[Unit]
Description=Alcohol Label Verification App
After=network.target

[Service]
User=root
WorkingDirectory=/opt/label-verifier
Environment=PYTHONPATH=/opt/label-verifier
ExecStart=/opt/label-verifier/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable label-verifier
sudo systemctl start label-verifier
```

Check status:

```bash
sudo systemctl status label-verifier
```

Logs:

```bash
journalctl -u label-verifier -f
```

---

## Running Tests

Compile:

```bash
PYTHONPATH=/opt/label-verifier \
python3 -m py_compile \
app/main.py \
app/routes.py \
app/services/*.py
```

Run Tests:

```bash
source .venv/bin/activate

pytest
```

---

## Example Validation Workflow

1. Select product category.
2. Complete Application Builder.
3. Upload:

   * Application PDF
   * Front Label
   * Back Label
4. Click Validate Label Set.
5. Review:

   * Matches
   * Mismatches
   * Manual Reviews
   * OCR Quality Metrics

---

## Current Limitations

This is a prototype and not an official TTB compliance system.

Items still requiring manual review include:

* Same Field of Vision determination
* Font size requirements
* Label placement requirements
* Organic certification validation
* Complex appellation verification
* Formula approval determination

---

## Future Enhancements

### Phase 1

* Auto-rotate images
* OCR confidence overlays
* Improved producer matching
* Beer-specific validation rules

### Phase 2

* COLA form extraction
* Front/back image pairing
* Label region detection
* Improved warning statement recognition

### Phase 3

* AI-assisted compliance review
* Visual field-of-vision analysis
* Layout validation
* Automated rule recommendations

---

## Disclaimer

This application is intended solely as a prototype and demonstration tool. Final label approval decisions require review by qualified compliance personnel and adherence to all applicable TTB regulations and guidance.

