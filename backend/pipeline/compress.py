import io
from dataclasses import dataclass

from PIL import Image
import fitz  # PyMuPDF

MAX_DIMENSION = 1200
JPEG_QUALITY = 70
TARGET_SIZE = 300 * 1024  # 300 KB


@dataclass
class CompressionResult:
    compressed_bytes: bytes
    original_size: int
    compressed_size: int
    format: str  # "jpeg", "pdf"


def _detect_format(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"%PDF":
        return "pdf"
    raise ValueError(f"Unsupported format: unrecognised file header")


def _compress_image(data: bytes) -> bytes:
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out.getvalue()


def _compress_pdf(data: bytes) -> bytes:
    doc = fitz.open(stream=data, filetype="pdf")
    out_doc = fitz.open()
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("jpeg")
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img_out = io.BytesIO()
        img.save(img_out, format="JPEG", quality=JPEG_QUALITY)
        img_pdf_bytes = img_out.getvalue()
        img_pdf = fitz.open(stream=img_pdf_bytes, filetype="jpeg")
        rect = img_pdf[0].rect
        page_doc = fitz.open()
        page_doc.new_page(width=rect.width, height=rect.height)
        page_doc[0].insert_image(rect, stream=img_pdf_bytes)
        out_doc.insert_pdf(page_doc)
    out = io.BytesIO()
    out_doc.save(out)
    return out.getvalue()


def compress(data: bytes) -> CompressionResult:
    original_size = len(data)
    fmt = _detect_format(data)

    if fmt in ("jpeg", "png"):
        compressed = _compress_image(data)
        output_fmt = "jpeg"  # _compress_image always outputs JPEG
    else:  # pdf
        compressed = _compress_pdf(data)
        output_fmt = "pdf"

    # Never return a file larger than the original
    if len(compressed) >= original_size:
        compressed = data

    return CompressionResult(
        compressed_bytes=compressed,
        original_size=original_size,
        compressed_size=len(compressed),
        format=output_fmt,
    )
