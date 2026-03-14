import os
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from db.queries import init_db, save_verification, get_verifications, get_verification
from pipeline.compress import compress
from pipeline.ocr import run_ocr
from pipeline.extract import classify_doc_type, extract_fields
from pipeline.validate import validate
from pipeline.blockchain import store_verification


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="DocVerify API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OFFICER_API_KEY = os.environ.get("OFFICER_API_KEY", "demo-officer-key-change-in-prod")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def require_officer_key(x_officer_key: str = Header(...)):
    if x_officer_key != OFFICER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid officer key")


@app.post("/api/verify")
async def verify(
    applicant_id: str = Form(...),
    files: list[UploadFile] = File(...),
):
    if not files or len(files) > 5:
        raise HTTPException(status_code=400, detail="Upload 1–5 files")

    doc_results = []
    all_compressed_bytes = []

    for f in files:
        raw = await f.read()

        if len(raw) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"file_too_large: {f.filename}")

        # Stage 1: Compress
        try:
            comp = compress(raw)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"unsupported_format: {f.filename}")

        all_compressed_bytes.append(comp.compressed_bytes)

        # Stage 2: OCR
        ocr_result = run_ocr(comp.compressed_bytes, comp.format)

        # Stage 3: Extract
        doc_type = classify_doc_type(ocr_result.full_text)
        extraction = extract_fields(doc_type, ocr_result.full_text, ocr_result.words)

        doc_results.append({
            "doc_type": doc_type,
            "original_size": comp.original_size,
            "compressed_size": comp.compressed_size,
            "fields": {
                k: {"value": v.value, "confidence": v.confidence}
                for k, v in extraction.fields.items()
            },
            "_compressed_bytes": comp.compressed_bytes,
        })

    # Stage 4: Cross-validate
    validation = validate(doc_results)

    # Stage 5: Blockchain
    doc_hashes = [
        hashlib.sha256(d["_compressed_bytes"]).digest()
        for d in doc_results
    ]
    is_verified = validation.overall_confidence >= 75
    chain_result = store_verification(
        applicant_id, doc_hashes, int(validation.overall_confidence), is_verified
    )

    # Strip internal fields before storing/returning
    for d in doc_results:
        d.pop("_compressed_bytes", None)

    cross_val_dicts = [
        {
            "field": c.field,
            "status": c.status,
            "documents": c.documents,
            "values": c.values,
        }
        for c in validation.checks
    ]

    save_verification(
        applicant_id=applicant_id,
        overall_confidence=int(validation.overall_confidence),
        is_verified=is_verified,
        tx_hash=chain_result.tx_hash if chain_result else None,
        documents=doc_results,
        cross_validation=cross_val_dicts,
    )

    response = {
        "applicant_id": applicant_id,
        "documents": doc_results,
        "cross_validation": cross_val_dicts,
        "overall_confidence": int(validation.overall_confidence),
        "is_verified": is_verified,
    }

    if chain_result:
        response["blockchain"] = {
            "tx_hash": chain_result.tx_hash,
            "block_number": chain_result.block_number,
            "contract_address": chain_result.contract_address,
            "polygonscan_url": f"https://amoy.polygonscan.com/tx/{chain_result.tx_hash}",
        }

    return response


@app.get("/api/verifications")
def list_verifications(_=Depends(require_officer_key)):
    return {"verifications": get_verifications()}


@app.get("/api/verifications/{applicant_id}")
def get_verification_detail(applicant_id: str, _=Depends(require_officer_key)):
    result = get_verification(applicant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result
