import io
import pytest
from PIL import Image

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.compress import compress, CompressionResult


def _make_jpeg(width=2000, height=2000) -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _make_png(width=1500, height=1500) -> bytes:
    img = Image.new("RGBA", (width, height), color=(100, 150, 200, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_compress_jpeg_reduces_size():
    data = _make_jpeg()
    result = compress(data)
    assert result.compressed_size < result.original_size


def test_compress_jpeg_under_300kb():
    data = _make_jpeg()
    result = compress(data)
    assert result.compressed_size <= 300 * 1024


def test_compress_jpeg_format():
    data = _make_jpeg()
    result = compress(data)
    assert result.format == "jpeg"


def test_compress_png_works():
    data = _make_png()
    result = compress(data)
    assert result.compressed_size < result.original_size
    assert isinstance(result.compressed_bytes, bytes)
    assert len(result.compressed_bytes) > 0
    assert result.format == "jpeg"  # PNG is re-encoded as JPEG


def test_compress_never_increases_size():
    # Tiny image that's already minimal
    img = Image.new("RGB", (50, 50), color=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    data = buf.getvalue()
    result = compress(data)
    assert result.compressed_size <= result.original_size


def test_compress_returns_dataclass():
    data = _make_jpeg()
    result = compress(data)
    assert isinstance(result, CompressionResult)
    assert result.original_size == len(data)


def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        compress(b"this is not an image file at all")
