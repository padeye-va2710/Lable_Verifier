from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract


def preprocess_image(path: str) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    max_width = 1800
    if image.width > max_width:
        ratio = max_width / image.width
        image = image.resize((max_width, int(image.height * ratio)))

    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)

    return image


def ocr_image(path: str) -> str:
    image = preprocess_image(path)

    text_psm6 = pytesseract.image_to_string(image, config="--oem 3 --psm 6")
    text_psm11 = pytesseract.image_to_string(image, config="--oem 3 --psm 11")

    return f"{text_psm6}\n{text_psm11}".strip()
