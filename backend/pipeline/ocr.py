from dataclasses import dataclass, field
from typing import Optional

import os

import fitz
from google.cloud import vision
from google.oauth2 import service_account


@dataclass
class WordAnnotation:
    text: str
    confidence: float


@dataclass
class OCRResult:
    full_text: str
    words: list[WordAnnotation] = field(default_factory=list)


def _get_client() -> vision.ImageAnnotatorClient:
    # Build credentials from individual env vars (Railway-friendly)
    private_key = os.environ.get("GCP_PRIVATE_KEY", "").replace("\\n", "\n")
    client_email = os.environ.get("GCP_CLIENT_EMAIL", "")
    if private_key and client_email:
        info = {
            "type": "service_account",
            "project_id": os.environ.get("GCP_PROJECT_ID", ""),
            "private_key_id": os.environ.get("GCP_PRIVATE_KEY_ID", ""),
            "private_key": private_key,
            "client_email": client_email,
            "client_id": os.environ.get("GCP_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}",
            "universe_domain": "googleapis.com",
        }
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/cloud-vision"]
        )
        return vision.ImageAnnotatorClient(credentials=creds)
    return vision.ImageAnnotatorClient()


def _ocr_bytes(client: vision.ImageAnnotatorClient, img_bytes: bytes) -> OCRResult:
    image = vision.Image(content=img_bytes)
    image_context = vision.ImageContext(language_hints=["hi", "en"])
    response = client.document_text_detection(image=image, image_context=image_context)

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    annotation = response.full_text_annotation
    full_text = annotation.text if annotation else ""
    words = []

    if annotation:
        for page in annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = "".join(s.text for s in word.symbols)
                        words.append(WordAnnotation(text=word_text, confidence=word.confidence))

    return OCRResult(full_text=full_text, words=words)


def run_ocr(
    data: bytes,
    fmt: str,
    client: Optional[vision.ImageAnnotatorClient] = None,
) -> OCRResult:
    if client is None:
        client = _get_client()

    if fmt == "pdf":
        doc = fitz.open(stream=data, filetype="pdf")
        all_text: list[str] = []
        all_words: list[WordAnnotation] = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            result = _ocr_bytes(client, img_bytes)
            all_text.append(result.full_text)
            all_words.extend(result.words)
        return OCRResult(full_text="\n".join(all_text), words=all_words)

    return _ocr_bytes(client, data)
