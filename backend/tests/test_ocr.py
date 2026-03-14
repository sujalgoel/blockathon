import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from pipeline.ocr import run_ocr, OCRResult, WordAnnotation


def _make_mock_client(full_text: str, words: list[tuple[str, float]]) -> MagicMock:
    """Build a mock Google Vision client returning given text and words."""
    client = MagicMock()

    mock_annotation = MagicMock()
    mock_annotation.text = full_text
    mock_annotation.error.message = ""

    mock_page = MagicMock()
    mock_block = MagicMock()
    mock_para = MagicMock()

    mock_words = []
    for word_text, conf in words:
        w = MagicMock()
        w.confidence = conf
        w.symbols = [MagicMock(text=ch) for ch in word_text]
        mock_words.append(w)

    mock_para.words = mock_words
    mock_block.paragraphs = [mock_para]
    mock_page.blocks = [mock_block]
    mock_annotation.pages = [mock_page]

    response = MagicMock()
    response.full_text_annotation = mock_annotation
    response.error.message = ""
    client.document_text_detection.return_value = response

    return client


def test_run_ocr_returns_ocr_result():
    import io
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    mock_client = _make_mock_client(
        "Ramesh Kumar Negi\nDOB: 14/03/1988",
        [("Ramesh", 0.98), ("Kumar", 0.97), ("Negi", 0.99)]
    )

    result = run_ocr(img_bytes, "jpeg", client=mock_client)
    assert isinstance(result, OCRResult)
    assert "Ramesh Kumar Negi" in result.full_text
    assert len(result.words) == 3
    assert result.words[0].text == "Ramesh"
    assert result.words[0].confidence == 0.98


def test_run_ocr_empty_response():
    import io
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    client = MagicMock()
    response = MagicMock()
    response.full_text_annotation.text = ""
    response.full_text_annotation.pages = []
    response.error.message = ""
    client.document_text_detection.return_value = response

    result = run_ocr(buf.getvalue(), "jpeg", client=client)
    assert result.full_text == ""
    assert result.words == []


def test_run_ocr_passes_language_hints():
    import io
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    mock_client = _make_mock_client("text", [])
    run_ocr(buf.getvalue(), "jpeg", client=mock_client)

    image_context = mock_client.document_text_detection.call_args.kwargs["image_context"]
    assert "hi" in image_context.language_hints
    assert "en" in image_context.language_hints
