import os
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Resolve GOOGLE_APPLICATION_CREDENTIALS to absolute path
_gcp = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
if _gcp and not os.path.isabs(_gcp):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        (Path(__file__).parent.parent / _gcp).resolve()
    )

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware

from db.queries import init_db, save_verification, get_verifications, get_verification
from pipeline.compress import compress
from pipeline.ocr import run_ocr
from pipeline.extract import extract_fields
from pipeline.validate import validate
from pipeline.blockchain import store_verification
from pipeline.storage import upload_compressed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="DocVerify API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "https://doc-verify-core.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OFFICER_API_KEY = os.environ.get("OFFICER_API_KEY", "demo-officer-key-change-in-prod")
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _check_key(key: str):
    if key != OFFICER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid officer key")


def require_officer_key(
    x_officer_key: str | None = Header(None),
    key: str | None = Query(None),
):
    """Accept key via X-Officer-Key header OR ?key= query param."""
    token = x_officer_key or key
    if not token:
        raise HTTPException(status_code=401, detail="Officer key required")
    _check_key(token)


async def _process_file(f: UploadFile, doc_type: str) -> dict:
    raw = await f.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"file_too_large: {f.filename}")
    try:
        comp = compress(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"unsupported_format: {f.filename}")

    ocr_result = run_ocr(comp.compressed_bytes, comp.format)
    extraction = extract_fields(doc_type, ocr_result.full_text, ocr_result.words)

    return {
        "doc_type": doc_type,
        "original_size": comp.original_size,
        "compressed_size": comp.compressed_size,
        "fields": {
            k: {"value": v.value, "confidence": v.confidence}
            for k, v in extraction.fields.items()
        },
        "_compressed_bytes": comp.compressed_bytes,
    }


@app.post("/api/verify")
async def verify(
    applicant_id: str = Form(...),
    doc_type: str = Form(...),
    aadhaar_front: UploadFile | None = File(None),
    aadhaar_back: UploadFile | None = File(None),
    pan: UploadFile | None = File(None),
):
    if doc_type == "aadhaar":
        if not aadhaar_front or not aadhaar_back:
            raise HTTPException(status_code=400, detail="Both aadhaar_front and aadhaar_back are required")
        af = await _process_file(aadhaar_front, "aadhaar_front")
        ab = await _process_file(aadhaar_back, "aadhaar_back")
        if hashlib.sha256(af["_compressed_bytes"]).hexdigest() == hashlib.sha256(ab["_compressed_bytes"]).hexdigest():
            raise HTTPException(status_code=400, detail="Aadhaar front and back appear to be the same image")
        doc_results = [af, ab]

    elif doc_type == "pan":
        if not pan:
            raise HTTPException(status_code=400, detail="pan file is required")
        doc_results = [await _process_file(pan, "pan")]

    else:
        raise HTTPException(status_code=400, detail="doc_type must be 'aadhaar' or 'pan'")

    # Upload compressed images to R2 (best-effort, non-blocking)
    for d in doc_results:
        url = upload_compressed(applicant_id, d["doc_type"], d["_compressed_bytes"])
        if url:
            d["compressed_url"] = url

    # Cross-validate
    validation = validate(doc_results)

    # Blockchain
    doc_hashes = [hashlib.sha256(d["_compressed_bytes"]).digest() for d in doc_results]
    is_verified = validation.overall_confidence >= 75
    chain_result = store_verification(
        applicant_id, doc_hashes, int(validation.overall_confidence), is_verified
    )

    # Strip internal bytes
    for d in doc_results:
        d.pop("_compressed_bytes", None)

    cross_val_dicts = [
        {"field": c.field, "status": c.status, "documents": c.documents, "values": c.values}
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
