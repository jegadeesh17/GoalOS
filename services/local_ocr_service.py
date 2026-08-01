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
  except Exception:
    return {
      "success": False,
      "text": "",
      "error": (
        "Local Tesseract OCR engine is not installed or found in PATH. "
        "For offline image scanning, install Tesseract OCR locally, or use the recommended CSV Upload option."
      ),
    }


def parse_ocr_text_to_standard_fields(raw_text: str, day_label: str = "") -> dict[str, str]:
  """Parse raw OCR text into standard journal fields: gratitude, tasks, plan, review, takeaway. Returns empty fields if no text."""
  text = raw_text.strip()
  if not text:
    return {
      "gratitude": "",
      "tasks": "",
      "plan": "",
      "review": "",
      "takeaway": "",
    }

  lines = [line.strip() for line in text.splitlines() if line.strip()]
  
  fields = {
    "gratitude": "",
    "tasks": "",
    "plan": "",
    "review": "",
    "takeaway": "",
  }

  current_key = "review"
  bucket_content: dict[str, list[str]] = {k: [] for k in fields}

  for line in lines:
    lower_line = line.lower()
    if "gratitude" in lower_line or "thankful" in lower_line or "grateful" in lower_line:
      current_key = "gratitude"
      content = line.split(":", 1)[-1].strip()
      if content:
        bucket_content[current_key].append(content)
    elif "task" in lower_line or "todo" in lower_line or "to do" in lower_line:
      current_key = "tasks"
      content = line.split(":", 1)[-1].strip()
      if content:
        bucket_content[current_key].append(content)
    elif "plan" in lower_line or "schedule" in lower_line or "timeblock" in lower_line:
      current_key = "plan"
      content = line.split(":", 1)[-1].strip()
      if content:
        bucket_content[current_key].append(content)
    elif "review" in lower_line or "journal" in lower_line or "reflection" in lower_line or "win" in lower_line:
      current_key = "review"
      content = line.split(":", 1)[-1].strip()
      if content:
        bucket_content[current_key].append(content)
    elif "takeaway" in lower_line or "lesson" in lower_line or "action" in lower_line:
      current_key = "takeaway"
      content = line.split(":", 1)[-1].strip()
      if content:
        bucket_content[current_key].append(content)
    else:
      bucket_content[current_key].append(line)

  for k in fields:
    fields[k] = " ".join(bucket_content[k]).strip()

  if not fields["review"] and text:
    fields["review"] = text

  return fields

