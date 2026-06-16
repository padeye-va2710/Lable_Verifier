import io
from typing import Any, Dict, List

import fitz
import pytesseract
from PIL import Image, ImageOps


def _resize_image(image: Image.Image, max_width: int = 1800) -> Image.Image:
    width, height = image.size
    if width <= max_width:
        return image

    ratio = max_width / float(width)
    new_height = int(height * ratio)
    return image.resize((max_width, new_height))


def _ocr_image(image: Image.Image) -> Dict[str, Any]:
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    image = _resize_image(image)

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--oem 1 --psm 6"
    )

    words: List[str] = []
    confidences: List[float] = []

    for text, conf in zip(data.get("text", []), data.get("conf", [])):
        clean_text = text.strip()
        if clean_text:
            words.append(clean_text)

        try:
            conf_value = float(conf)
            if conf_value >= 0:
                confidences.append(conf_value)
        except ValueError:
            pass

    return {
        "text": " ".join(words),
        "confidence": round(sum(confidences) / len(confidences), 2) if confidences else None
    }


def _ocr_pdf(file_bytes: bytes) -> Dict[str, Any]:
    pdf = fitz.open(stream=file_bytes, filetype="pdf")

    all_text: List[str] = []
    all_confidences: List[float] = []

    for page in pdf:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.open(io.BytesIO(pix.tobytes("png")))

        result = _ocr_image(image)
        if result.get("text"):
            all_text.append(result["text"])

        if result.get("confidence") is not None:
            all_confidences.append(result["confidence"])

    pdf.close()

    return {
        "text": "\n".join(all_text),
        "confidence": round(sum(all_confidences) / len(all_confidences), 2) if all_confidences else None
    }


def extract_text_from_upload_bytes(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        return _ocr_pdf(file_bytes)

    image = Image.open(io.BytesIO(file_bytes))
    return _ocr_image(image)
