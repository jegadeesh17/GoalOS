"""Local OCR Service: Zero-API offline text extraction from images using pytesseract."""

from typing import Any


def extract_text_from_image(image_bytes: bytes) -> dict[str, Any]:
  """Attempts local offline OCR using pytesseract without any external API calls."""
  try:
    import io

    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes))
  except Exception as exc:
    return {
      "success": False,
      "text": "",
      "error": f"Failed to open image file: {str(exc)}",
    }

  try:
    import pytesseract

    extracted_text = pytesseract.image_to_string(image)
    if extracted_text.strip():
      return {
        "success": True,
        "text": extracted_text.strip(),
        "error": None,
      }
    else:
      return {
        "success": False,
        "text": "",
        "error": "No clear text recognized from image. Please ensure good lighting and contrast or use CSV upload.",
      }
  except Exception as exc:
    return {
      "success": False,
      "text": "",
      "error": (
        "Local Tesseract OCR engine is not installed or found in PATH. "
        "For offline image scanning, install Tesseract OCR locally, or use the recommended CSV Upload option."
      ),
    }
