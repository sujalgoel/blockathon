# DocVerify PS01 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an end-to-end document verification pipeline — compression → OCR → field extraction → cross-validation → Polygon blockchain anchoring — with a React frontend for citizens (upload) and officers (dashboard).

**Architecture:** Single FastAPI monolith handling all pipeline stages synchronously per request. React frontend proxies `/api` to backend. Smart contract on Polygon Amoy testnet stores tamper-proof verification records keyed by applicant ID.

**Tech Stack:** Python 3.11 + FastAPI + Pillow + PyMuPDF + Google Vision API + web3.py + SQLite | React 18 + Vite + TailwindCSS + Axios | Solidity 0.8.24 + Hardhat on Polygon Amoy

---

## File Map

```
BLOCKATHON/
├── .env                               # secrets (gitignored)
├── .env.example                       # template committed to git
├── .gitignore
│
├── contracts/
│   ├── package.json
│   ├── hardhat.config.js
│   ├── contracts/
│   │   └── DocumentVerification.sol   # Solidity smart contract
│   ├── scripts/
│   │   └── deploy.js                  # Hardhat deploy script
│   └── test/
│       └── DocumentVerification.test.js
│
├── backend/
│   ├── requirements.txt
│   ├── main.py                        # FastAPI app, routes, pipeline orchestration
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── compress.py                # Stage 1: image/PDF compression
│   │   ├── ocr.py                     # Stage 2: Google Vision OCR
│   │   ├── extract.py                 # Stage 3: doc classification + field extraction
│   │   ├── validate.py                # Stage 4: cross-field validation + confidence
│   │   └── blockchain.py              # Stage 5: Polygon Amoy write
│   ├── db/
│   │   ├── schema.sql                 # CREATE TABLE statements
│   │   └── queries.py                 # init_db, save_verification, get_verifications, get_verification
│   └── tests/
│       ├── test_compress.py
│       ├── test_extract.py
│       ├── test_validate.py
│       ├── test_ocr.py
│       └── test_blockchain.py
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx                   # React root, router
        ├── App.jsx                    # Route definitions
        ├── index.css                  # CSS variables, animations, global reset
        ├── api.js                     # Axios wrapper (all API calls)
        ├── pages/
        │   ├── UploadPage.jsx         # Citizen upload screen
        │   └── DashboardPage.jsx      # Officer dashboard
        └── components/
            ├── DocChip.jsx            # Upload status chip per document type
            ├── VerificationCard.jsx   # Application row + expandable detail panel
            └── BlockchainReceipt.jsx  # Blockchain tx hash display
```

---

## Chunk 1: Project Scaffolding & Smart Contract

### Task 1: Project scaffolding

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/requirements.txt`
- Create: `contracts/package.json`

- [ ] **Step 1: Create .gitignore**

```
.env
__pycache__/
*.pyc
*.pyo
.venv/
node_modules/
artifacts/
cache/
db/verifications.db
*.egg-info/
.DS_Store
```

Save to `BLOCKATHON/.gitignore`.

- [ ] **Step 2: Create .env.example**

```
GOOGLE_APPLICATION_CREDENTIALS=./gcp-credentials.json
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology/
DEPLOYER_PRIVATE_KEY=your_testnet_private_key_here
CONTRACT_ADDRESS=set_after_deploy
OFFICER_API_KEY=demo-officer-key-change-in-prod
```

Save to `BLOCKATHON/.env.example`.

- [ ] **Step 3a: Copy .env.example to .env**

```bash
cp BLOCKATHON/.env.example BLOCKATHON/.env
```

- [ ] **Step 3b: Fill in real credentials in .env**

Open `BLOCKATHON/.env` and set:
- `GOOGLE_APPLICATION_CREDENTIALS` — path to your GCP service account JSON (download from GCP Console → IAM → Service Accounts → Keys)
- `POLYGON_RPC_URL` — use `https://rpc-amoy.polygon.technology/` or your Alchemy/Infura Amoy endpoint
- `DEPLOYER_PRIVATE_KEY` — export from MetaMask → Account Details → Export Private Key
- Leave `CONTRACT_ADDRESS` as `set_after_deploy` for now

Verify at least 3 variables are populated:
```bash
grep -v "your_testnet\|set_after_deploy\|demo-officer" BLOCKATHON/.env | grep -c "="
```
Expected output: `3` or more.

- [ ] **Step 4: Create backend/requirements.txt**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
Pillow==10.3.0
PyMuPDF==1.24.3
google-cloud-vision==3.7.2
web3==6.18.0
aiosqlite==0.20.0
python-Levenshtein==0.25.1
python-dotenv==1.0.1
filetype==1.2.0
pytest==8.2.0
pytest-mock==3.14.0
httpx==0.27.0
```

- [ ] **Step 5: Create Python virtualenv and install**

```bash
cd BLOCKATHON/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: no errors, packages installed.

- [ ] **Step 6: Create contracts/package.json**

```json
{
  "name": "docverify-contracts",
  "version": "1.0.0",
  "devDependencies": {
    "@nomicfoundation/hardhat-toolbox": "^5.0.0",
    "hardhat": "^2.22.0",
    "dotenv": "^16.4.0"
  }
}
```

- [ ] **Step 7: Install Hardhat**

```bash
cd BLOCKATHON/contracts
npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 8: Create __init__.py files and pytest config**

```bash
touch BLOCKATHON/backend/pipeline/__init__.py
touch BLOCKATHON/backend/tests/__init__.py
touch BLOCKATHON/backend/db/__init__.py
```

Create `BLOCKATHON/backend/pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 9: Commit**

```bash
cd BLOCKATHON
git init
git add .gitignore .env.example backend/requirements.txt contracts/package.json backend/pipeline/__init__.py backend/tests/__init__.py backend/db/__init__.py backend/pytest.ini
git commit -m "chore: project scaffolding, deps, gitignore, pytest config"
```

---

### Task 2: Smart contract

**Files:**
- Create: `contracts/contracts/DocumentVerification.sol`
- Create: `contracts/hardhat.config.js`
- Create: `contracts/test/DocumentVerification.test.js`
- Create: `contracts/scripts/deploy.js`

- [ ] **Step 1: Write the failing contract test**

Create `contracts/test/DocumentVerification.test.js`:

```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DocumentVerification", function () {
  let contract;

  beforeEach(async () => {
    const DocVerify = await ethers.getContractFactory("DocumentVerification");
    contract = await DocVerify.deploy();
  });

  it("stores and retrieves a verification record", async () => {
    const applicantId = "UK-2024-00183";
    const docHash = ethers.keccak256(ethers.toUtf8Bytes("test-doc"));

    await contract.storeVerification(applicantId, [docHash], 91, true);

    const records = await contract.getRecords(applicantId);
    expect(records.length).to.equal(1);
    expect(records[0].applicantId).to.equal(applicantId);
    expect(records[0].confidence).to.equal(91);
    expect(records[0].isVerified).to.equal(true);
  });

  it("returns empty array for unknown applicant", async () => {
    const records = await contract.getRecords("UNKNOWN-ID");
    expect(records.length).to.equal(0);
  });

  it("stores multiple records for the same applicant", async () => {
    const id = "UK-2024-00183";
    const h1 = ethers.keccak256(ethers.toUtf8Bytes("doc1"));
    const h2 = ethers.keccak256(ethers.toUtf8Bytes("doc2"));

    await contract.storeVerification(id, [h1], 80, true);
    await contract.storeVerification(id, [h2], 60, false);

    const records = await contract.getRecords(id);
    expect(records.length).to.equal(2);
    expect(records[0].isVerified).to.equal(true);
    expect(records[1].isVerified).to.equal(false);
  });

  it("emits VerificationStored event", async () => {
    const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");
    const id = "UK-2024-00183";
    const hash = ethers.keccak256(ethers.toUtf8Bytes("doc"));

    await expect(contract.storeVerification(id, [hash], 75, true))
      .to.emit(contract, "VerificationStored")
      .withArgs(id, 75, true, anyValue);
  });
});
```

- [ ] **Step 2: Run test — expect FAIL (contract not yet written)**

```bash
cd BLOCKATHON/contracts
npx hardhat test
```

Expected: `Error: No contract factory found for name "DocumentVerification"`

- [ ] **Step 3: Write the Solidity contract**

Create `contracts/contracts/DocumentVerification.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract DocumentVerification {
    struct VerificationRecord {
        string applicantId;
        bytes32[] docHashes;
        uint8 confidence;
        bool isVerified;
        uint256 timestamp;
    }

    mapping(string => VerificationRecord[]) private records;

    event VerificationStored(
        string applicantId,
        uint8 confidence,
        bool isVerified,
        uint256 timestamp
    );

    function storeVerification(
        string memory applicantId,
        bytes32[] memory docHashes,
        uint8 confidence,
        bool isVerified
    ) external {
        records[applicantId].push(VerificationRecord({
            applicantId: applicantId,
            docHashes: docHashes,
            confidence: confidence,
            isVerified: isVerified,
            timestamp: block.timestamp
        }));
        emit VerificationStored(applicantId, confidence, isVerified, block.timestamp);
    }

    function getRecords(string memory applicantId)
        external
        view
        returns (VerificationRecord[] memory)
    {
        return records[applicantId];
    }
}
```

- [ ] **Step 4: Write hardhat.config.js**

```javascript
const path = require("path");
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: path.join(__dirname, "../.env") });

module.exports = {
  solidity: "0.8.24",
  networks: {
    amoy: {
      url: process.env.POLYGON_RPC_URL || "",
      accounts: process.env.DEPLOYER_PRIVATE_KEY
        ? [process.env.DEPLOYER_PRIVATE_KEY]
        : [],
      chainId: 80002,
    },
  },
};
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd BLOCKATHON/contracts
npx hardhat test
```

Expected:
```
DocumentVerification
  ✔ stores and retrieves a verification record
  ✔ returns empty array for unknown applicant
  ✔ stores multiple records for the same applicant
  ✔ emits VerificationStored event

4 passing
```

- [ ] **Step 6: Write deploy script**

Create `contracts/scripts/deploy.js`:

```javascript
const hre = require("hardhat");

async function main() {
  const DocVerify = await hre.ethers.getContractFactory("DocumentVerification");
  const contract = await DocVerify.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log(`DocumentVerification deployed to: ${address}`);
  console.log(`\nAdd to .env:\nCONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```

- [ ] **Step 7: Commit**

```bash
cd BLOCKATHON
git add contracts/
git commit -m "feat: DocumentVerification smart contract with Hardhat tests"
```

---

### Task 3: Deploy contract to Polygon Amoy

**Prerequisites:** `.env` must have `POLYGON_RPC_URL` and `DEPLOYER_PRIVATE_KEY`. Wallet must have Amoy MATIC from https://faucet.polygon.technology/

- [ ] **Step 1: Get testnet MATIC**

Visit https://faucet.polygon.technology/, select Amoy, enter your wallet address. Wait for 0.5 MATIC to arrive (takes ~30 seconds).

If the primary faucet is rate-limiting, fallback options:
- https://www.alchemy.com/faucets/polygon-amoy
- https://faucet.quicknode.com/polygon/amoy

- [ ] **Step 2: Deploy**

```bash
cd BLOCKATHON/contracts
npx hardhat run scripts/deploy.js --network amoy
```

Expected output:
```
DocumentVerification deployed to: 0xABCD...1234

Add to .env:
CONTRACT_ADDRESS=0xABCD...1234
```

- [ ] **Step 3: Save CONTRACT_ADDRESS to .env**

Edit `BLOCKATHON/.env` — set `CONTRACT_ADDRESS=<address from deploy output>`.

- [ ] **Step 4: Verify contract on Polygonscan Amoy (optional but impressive for judges)**

```bash
cd BLOCKATHON/contracts
npx hardhat verify --network amoy <CONTRACT_ADDRESS> --contract contracts/contracts/DocumentVerification.sol:DocumentVerification
```

- [ ] **Step 5: Commit**

```bash
cd BLOCKATHON
git add .env.example
git commit -m "feat: deploy DocumentVerification to Polygon Amoy"
```

---

## Chunk 2: Backend Pipeline

### Task 4: FastAPI skeleton + SQLite

**Files:**
- Create: `backend/db/schema.sql`
- Create: `backend/db/__init__.py`
- Create: `backend/db/queries.py`
- Create: `backend/main.py`

- [ ] **Step 1: Create db/schema.sql**

```sql
CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id TEXT NOT NULL,
    overall_confidence INTEGER NOT NULL,
    is_verified INTEGER NOT NULL,
    tx_hash TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id INTEGER NOT NULL REFERENCES verifications(id),
    doc_type TEXT NOT NULL,
    original_size INTEGER NOT NULL,
    compressed_size INTEGER NOT NULL,
    fields_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cross_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id INTEGER NOT NULL REFERENCES verifications(id),
    field TEXT NOT NULL,
    status TEXT NOT NULL,
    documents_json TEXT NOT NULL,
    values_json TEXT NOT NULL
);
```

- [ ] **Step 2: Create db/__init__.py**

```bash
touch BLOCKATHON/backend/db/__init__.py
```

- [ ] **Step 3: Create db/queries.py**

```python
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "verifications.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    with get_conn() as conn:
        conn.executescript(schema)


def save_verification(
    applicant_id: str,
    overall_confidence: int,
    is_verified: bool,
    tx_hash: str | None,
    documents: list[dict],
    cross_validation: list[dict],
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO verifications (applicant_id, overall_confidence, is_verified, tx_hash)
               VALUES (?, ?, ?, ?)""",
            (applicant_id, overall_confidence, int(is_verified), tx_hash),
        )
        verification_id = cur.lastrowid

        for doc in documents:
            conn.execute(
                """INSERT INTO documents (verification_id, doc_type, original_size, compressed_size, fields_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    verification_id,
                    doc["doc_type"],
                    doc["original_size"],
                    doc["compressed_size"],
                    json.dumps(doc["fields"]),
                ),
            )

        for check in cross_validation:
            conn.execute(
                """INSERT INTO cross_validation (verification_id, field, status, documents_json, values_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    verification_id,
                    check["field"],
                    check["status"],
                    json.dumps(check["documents"]),
                    json.dumps(check["values"]),
                ),
            )
        conn.commit()
    return verification_id


def get_verifications() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT applicant_id, overall_confidence, is_verified, tx_hash, created_at FROM verifications ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_verification(applicant_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM verifications WHERE applicant_id = ? ORDER BY id DESC LIMIT 1",
            (applicant_id,),
        ).fetchone()
        if not row:
            return None
        verification_id = row["id"]

        doc_rows = conn.execute(
            "SELECT doc_type, original_size, compressed_size, fields_json FROM documents WHERE verification_id = ?",
            (verification_id,),
        ).fetchall()

        cv_rows = conn.execute(
            "SELECT field, status, documents_json, values_json FROM cross_validation WHERE verification_id = ?",
            (verification_id,),
        ).fetchall()

    documents = [
        {
            "doc_type": r["doc_type"],
            "original_size": r["original_size"],
            "compressed_size": r["compressed_size"],
            "fields": json.loads(r["fields_json"]),
        }
        for r in doc_rows
    ]
    cross_val = [
        {
            "field": r["field"],
            "status": r["status"],
            "documents": json.loads(r["documents_json"]),
            "values": json.loads(r["values_json"]),
        }
        for r in cv_rows
    ]
    return {
        "applicant_id": row["applicant_id"],
        "overall_confidence": row["overall_confidence"],
        "is_verified": bool(row["is_verified"]),
        "tx_hash": row["tx_hash"],
        "created_at": row["created_at"],
        "documents": documents,
        "cross_validation": cross_val,
    }
```

- [ ] **Step 4: Create main.py skeleton**

```python
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
ALLOWED_MIME_PREFIXES = ("image/jpeg", "image/png", "application/pdf")


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
        except ValueError as e:
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
            "_words": ocr_result.words,
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
        d.pop("_words", None)

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
```

- [ ] **Step 5: Verify backend starts**

```bash
cd BLOCKATHON/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Expected: `Uvicorn running on http://127.0.0.1:8000`. Ctrl+C to stop.

- [ ] **Step 6: Commit**

```bash
cd BLOCKATHON
git add backend/
git commit -m "feat: FastAPI skeleton, SQLite schema and queries, pipeline wiring"
```

---

### Task 5: Compression stage

**Files:**
- Create: `backend/pipeline/compress.py`
- Create: `backend/tests/test_compress.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_compress.py`:

```python
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd BLOCKATHON/backend
source .venv/bin/activate
python -m pytest tests/test_compress.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — compress.py doesn't exist yet.

- [ ] **Step 3: Implement compress.py**

```python
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
    format: str  # "jpeg", "png", "pdf"


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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_compress.py -v
```

Expected:
```
test_compress.py::test_compress_jpeg_reduces_size PASSED
test_compress.py::test_compress_jpeg_under_300kb PASSED
test_compress.py::test_compress_jpeg_format PASSED
test_compress.py::test_compress_png_works PASSED
test_compress.py::test_compress_never_increases_size PASSED
test_compress.py::test_compress_returns_dataclass PASSED
test_compress.py::test_unsupported_format_raises PASSED
7 passed
```

- [ ] **Step 5: Commit**

```bash
cd BLOCKATHON
git add backend/pipeline/compress.py backend/tests/test_compress.py
git commit -m "feat: compression stage — Pillow image + PyMuPDF PDF compression"
```

---

### Task 6: OCR stage

**Files:**
- Create: `backend/pipeline/ocr.py`
- Create: `backend/tests/test_ocr.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_ocr.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from pipeline.ocr import run_ocr, OCRResult, WordAnnotation


def _make_mock_client(full_text: str, words: list[tuple[str, float]]) -> MagicMock:
    """Build a mock Google Vision client returning given text and words."""
    client = MagicMock()

    # Build fake annotation structure
    mock_annotation = MagicMock()
    mock_annotation.text = full_text
    mock_annotation.error.message = ""

    mock_pages = []
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_ocr.py -v
```

Expected: `ImportError` — ocr.py doesn't exist yet.

- [ ] **Step 3: Implement ocr.py**

```python
from dataclasses import dataclass, field
from typing import Optional

import fitz
from google.cloud import vision


@dataclass
class WordAnnotation:
    text: str
    confidence: float


@dataclass
class OCRResult:
    full_text: str
    words: list[WordAnnotation] = field(default_factory=list)


def _get_client() -> vision.ImageAnnotatorClient:
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_ocr.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
cd BLOCKATHON
git add backend/pipeline/ocr.py backend/tests/test_ocr.py
git commit -m "feat: OCR stage — Google Vision API with Hindi+English language hints"
```

---

### Task 7: Field extraction stage

**Files:**
- Create: `backend/pipeline/extract.py`
- Create: `backend/tests/test_extract.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_extract.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.extract import classify_doc_type, extract_fields, ExtractionResult

AADHAAR_TEXT = """Government of India
Ramesh Kumar Negi
DOB: 14/03/1988
MALE
S/O Mohan Negi
123 Village Road, Chamoli, Uttarakhand - 246401
4821 5678 1234
UIDAI"""

PAN_TEXT = """INCOME TAX DEPARTMENT
GOVT. OF INDIA
Permanent Account Number Card
ABCDE1234F
RAMESH KUMAR NEGI
Father's Name: MOHAN NEGI
Date of Birth: 14/03/1988"""

INCOME_CERT_TEXT = """Income Certificate
This is to certify that Ramesh Kumar Negi
resident of Chamoli, Uttarakhand
Annual Income: Rs. 85,000/-
Issuing Authority: Tehsildar Chamoli"""

DOMICILE_TEXT = """Domicile Certificate
Name: Ramesh Kumar Negi
Address: Village Pokhari, Chamoli, Uttarakhand
Issuing Authority: SDM Chamoli"""

CASTE_TEXT = """जाति प्रमाण पत्र
Name: Ramesh Kumar Negi
Caste: Scheduled Caste
Sub-Caste: Harijan
District: Chamoli"""


class TestClassification:
    def test_aadhaar(self):
        assert classify_doc_type(AADHAAR_TEXT) == "aadhaar"

    def test_pan(self):
        assert classify_doc_type(PAN_TEXT) == "pan"

    def test_income_cert(self):
        assert classify_doc_type(INCOME_CERT_TEXT) == "income_cert"

    def test_domicile_cert(self):
        assert classify_doc_type(DOMICILE_TEXT) == "domicile_cert"

    def test_caste_cert(self):
        assert classify_doc_type(CASTE_TEXT) == "caste_cert"

    def test_unknown(self):
        assert classify_doc_type("random unrelated text here") == "unknown"


class TestAadhaarExtraction:
    def test_uid_extracted_and_masked(self):
        result = extract_fields("aadhaar", AADHAAR_TEXT, [])
        assert "uid" in result.fields
        uid_val = result.fields["uid"].value
        # Last 4 digits visible, first 8 masked
        assert "1234" in uid_val
        assert "4821" not in uid_val  # masked

    def test_dob_extracted(self):
        result = extract_fields("aadhaar", AADHAAR_TEXT, [])
        assert "dob" in result.fields
        assert "1988" in result.fields["dob"].value

    def test_gender_extracted(self):
        result = extract_fields("aadhaar", AADHAAR_TEXT, [])
        assert "gender" in result.fields
        assert result.fields["gender"].value in ("Male", "Female")

    def test_name_extracted(self):
        result = extract_fields("aadhaar", AADHAAR_TEXT, [])
        assert "name" in result.fields
        assert "Ramesh" in result.fields["name"].value


class TestPANExtraction:
    def test_pan_number_extracted(self):
        result = extract_fields("pan", PAN_TEXT, [])
        assert "pan_number" in result.fields
        assert result.fields["pan_number"].value == "ABCDE1234F"

    def test_dob_extracted(self):
        result = extract_fields("pan", PAN_TEXT, [])
        assert "dob" in result.fields
        assert "1988" in result.fields["dob"].value


class TestUnknownExtraction:
    def test_unknown_returns_empty_fields(self):
        result = extract_fields("unknown", "some text", [])
        assert isinstance(result, ExtractionResult)
        assert result.fields == {}
        assert result.doc_type == "unknown"
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_extract.py -v
```

Expected: `ImportError` — extract.py doesn't exist yet.

- [ ] **Step 3: Implement extract.py**

```python
import re
from dataclasses import dataclass, field


@dataclass
class FieldResult:
    value: str
    confidence: float


@dataclass
class ExtractionResult:
    doc_type: str
    fields: dict[str, FieldResult] = field(default_factory=dict)


# --- Regexes ---
_UID_RE = re.compile(r"\b(\d{4})\s(\d{4})\s(\d{4})\b")
_DOB_RE = re.compile(r"\b(\d{2}[/\-]\d{2}[/\-]\d{4}|\d{4}[/\-]\d{2}[/\-]\d{2})\b")
_PAN_RE = re.compile(r"\b([A-Z]{5}\d{4}[A-Z])\b")
_INCOME_RE = re.compile(r"(?:Rs\.?\s*|INR\s*)([\d,]+)", re.IGNORECASE)
_NAME_LINE_RE = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+)+$")
_DISTRICT_RE = re.compile(
    r"\b(Chamoli|Dehradun|Haridwar|Nainital|Almora|Pithoragarh|Pauri|Tehri|Rudraprayag|Uttarkashi|Bageshwar|Champawat|Udham Singh Nagar)\b",
    re.IGNORECASE,
)


def classify_doc_type(text: str) -> str:
    if any(k in text for k in ("आधार", "UIDAI", "Unique Identification")):
        return "aadhaar"
    if any(k in text for k in ("Income Tax", "Permanent Account", "PAN")):
        return "pan"
    if any(k in text for k in ("Income Certificate", "आय प्रमाण")):
        return "income_cert"
    if any(k in text for k in ("Domicile", "मूल निवास")):
        return "domicile_cert"
    if any(k in text for k in ("Caste", "जाति प्रमाण")):
        return "caste_cert"
    return "unknown"


def _extract_name(text: str) -> str | None:
    skip_lines = {"Government of India", "INCOME TAX DEPARTMENT", "GOVT. OF INDIA"}
    for line in text.splitlines():
        line = line.strip()
        if line in skip_lines:
            continue
        if _NAME_LINE_RE.match(line):
            return line
    return None


def _extract_district(text: str) -> str | None:
    m = _DISTRICT_RE.search(text)
    return m.group(0).title() if m else None


def _extract_aadhaar(text: str) -> dict[str, FieldResult]:
    fields: dict[str, FieldResult] = {}

    uid_m = _UID_RE.search(text)
    if uid_m:
        masked = f"XXXX XXXX {uid_m.group(3)}"
        fields["uid"] = FieldResult(value=masked, confidence=0.99)

    dob_m = _DOB_RE.search(text)
    if dob_m:
        fields["dob"] = FieldResult(value=dob_m.group(0), confidence=0.97)

    if "FEMALE" in text.upper():
        fields["gender"] = FieldResult(value="Female", confidence=0.95)
    elif "MALE" in text.upper():
        fields["gender"] = FieldResult(value="Male", confidence=0.95)

    name = _extract_name(text)
    if name:
        fields["name"] = FieldResult(value=name, confidence=0.90)

    district = _extract_district(text)
    if district:
        fields["district"] = FieldResult(value=district, confidence=0.88)

    return fields


def _extract_pan(text: str) -> dict[str, FieldResult]:
    fields: dict[str, FieldResult] = {}

    pan_m = _PAN_RE.search(text)
    if pan_m:
        fields["pan_number"] = FieldResult(value=pan_m.group(1), confidence=0.99)

    dob_m = _DOB_RE.search(text)
    if dob_m:
        fields["dob"] = FieldResult(value=dob_m.group(0), confidence=0.97)

    name = _extract_name(text)
    if name:
        fields["name"] = FieldResult(value=name, confidence=0.90)

    # Father's name: line after "Father" keyword
    for line in text.splitlines():
        if "Father" in line and ":" in line:
            fname = line.split(":", 1)[1].strip().title()
            if fname:
                fields["father_name"] = FieldResult(value=fname, confidence=0.88)
            break

    return fields


def _extract_income_cert(text: str) -> dict[str, FieldResult]:
    fields: dict[str, FieldResult] = {}

    name = _extract_name(text)
    if name:
        fields["name"] = FieldResult(value=name, confidence=0.88)

    income_m = _INCOME_RE.search(text)
    if income_m:
        fields["annual_income"] = FieldResult(value=income_m.group(1).replace(",", ""), confidence=0.90)

    district = _extract_district(text)
    if district:
        fields["district"] = FieldResult(value=district, confidence=0.88)

    for line in text.splitlines():
        if "Issuing Authority" in line and ":" in line:
            auth = line.split(":", 1)[1].strip()
            if auth:
                fields["issuing_authority"] = FieldResult(value=auth, confidence=0.85)
            break

    return fields


def _extract_domicile(text: str) -> dict[str, FieldResult]:
    fields: dict[str, FieldResult] = {}

    for line in text.splitlines():
        if line.strip().startswith("Name:"):
            name = line.split(":", 1)[1].strip()
            if name:
                fields["name"] = FieldResult(value=name, confidence=0.88)
            break

    district = _extract_district(text)
    if district:
        fields["district"] = FieldResult(value=district, confidence=0.88)

    for line in text.splitlines():
        if "Address" in line and ":" in line:
            addr = line.split(":", 1)[1].strip()
            if addr:
                fields["address"] = FieldResult(value=addr, confidence=0.85)
            break

    for line in text.splitlines():
        if "Issuing Authority" in line and ":" in line:
            auth = line.split(":", 1)[1].strip()
            if auth:
                fields["issuing_authority"] = FieldResult(value=auth, confidence=0.85)
            break

    return fields


def _extract_caste(text: str) -> dict[str, FieldResult]:
    fields: dict[str, FieldResult] = {}

    for line in text.splitlines():
        if line.strip().startswith("Name:"):
            name = line.split(":", 1)[1].strip()
            if name:
                fields["name"] = FieldResult(value=name, confidence=0.88)
            break

    for line in text.splitlines():
        if line.strip().startswith("Caste:"):
            caste = line.split(":", 1)[1].strip()
            if caste:
                fields["caste"] = FieldResult(value=caste, confidence=0.90)
            break

    for line in text.splitlines():
        if "Sub-Caste" in line and ":" in line:
            sub = line.split(":", 1)[1].strip()
            if sub:
                fields["sub_caste"] = FieldResult(value=sub, confidence=0.88)
            break

    district = _extract_district(text)
    if district:
        fields["district"] = FieldResult(value=district, confidence=0.88)

    return fields


_EXTRACTORS = {
    "aadhaar": _extract_aadhaar,
    "pan": _extract_pan,
    "income_cert": _extract_income_cert,
    "domicile_cert": _extract_domicile,
    "caste_cert": _extract_caste,
}


def extract_fields(doc_type: str, text: str, words: list) -> ExtractionResult:
    extractor = _EXTRACTORS.get(doc_type)
    if not extractor:
        return ExtractionResult(doc_type=doc_type)
    return ExtractionResult(doc_type=doc_type, fields=extractor(text))
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_extract.py -v
```

Expected: all tests pass (some name tests may need tuning if regex misses — adjust `_NAME_LINE_RE` if needed).

- [ ] **Step 5: Commit**

```bash
cd BLOCKATHON
git add backend/pipeline/extract.py backend/tests/test_extract.py
git commit -m "feat: field extraction stage — doc classifier + per-type regex extractors"
```

---

### Task 8: Cross-validation stage

**Files:**
- Create: `backend/pipeline/validate.py`
- Create: `backend/tests/test_validate.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_validate.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.validate import validate, ValidationResult


def _doc(doc_type: str, **fields) -> dict:
    return {
        "doc_type": doc_type,
        "fields": {k: {"value": v, "confidence": 0.95} for k, v in fields.items()},
    }


class TestNameMatch:
    def test_exact_match(self):
        docs = [_doc("aadhaar", name="Ramesh Kumar Negi"), _doc("pan", name="Ramesh Kumar Negi")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "name_match")
        assert check.status == "MATCH"

    def test_fuzzy_match(self):
        # Slight variance still matches (Levenshtein ≥ 85%)
        docs = [_doc("aadhaar", name="Ramesh Kumar Negi"), _doc("pan", name="Ramesh K Negi")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "name_match")
        assert check.status == "MATCH"

    def test_clear_mismatch(self):
        docs = [_doc("aadhaar", name="Ramesh Kumar Negi"), _doc("pan", name="Sunita Devi")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "name_match")
        assert check.status == "MISMATCH"

    def test_only_one_doc_with_name_is_missing(self):
        docs = [_doc("aadhaar", uid="XXXX XXXX 1234")]
        result = validate(docs)
        name_checks = [c for c in result.checks if c.field == "name_match"]
        assert len(name_checks) == 0 or name_checks[0].status == "MISSING"


class TestDOBMatch:
    def test_exact_match(self):
        docs = [_doc("aadhaar", dob="14/03/1988"), _doc("pan", dob="14/03/1988")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "dob_match")
        assert check.status == "MATCH"

    def test_different_separator_match(self):
        docs = [_doc("aadhaar", dob="14/03/1988"), _doc("pan", dob="14-03-1988")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "dob_match")
        assert check.status == "MATCH"

    def test_dob_mismatch(self):
        docs = [_doc("aadhaar", dob="14/03/1988"), _doc("pan", dob="01/01/1990")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "dob_match")
        assert check.status == "MISMATCH"

    def test_missing_when_only_one_doc(self):
        docs = [_doc("aadhaar", dob="14/03/1988")]
        result = validate(docs)
        dob_checks = [c for c in result.checks if c.field == "dob_match"]
        assert len(dob_checks) == 0 or dob_checks[0].status == "MISSING"


class TestDistrictMatch:
    def test_district_match(self):
        docs = [_doc("domicile_cert", district="Chamoli"), _doc("income_cert", district="Chamoli")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "district_match")
        assert check.status == "MATCH"

    def test_district_mismatch(self):
        docs = [_doc("domicile_cert", district="Chamoli"), _doc("income_cert", district="Dehradun")]
        result = validate(docs)
        check = next(c for c in result.checks if c.field == "district_match")
        assert check.status == "MISMATCH"


class TestOverallConfidence:
    def test_confidence_in_range(self):
        docs = [_doc("aadhaar", name="Ramesh Kumar Negi", dob="14/03/1988"),
                _doc("pan", name="Ramesh Kumar Negi", dob="14/03/1988")]
        result = validate(docs)
        assert 0 <= result.overall_confidence <= 100

    def test_all_match_high_confidence(self):
        docs = [_doc("aadhaar", name="Ramesh Kumar Negi", dob="14/03/1988"),
                _doc("pan", name="Ramesh Kumar Negi", dob="14/03/1988")]
        result = validate(docs)
        assert result.overall_confidence >= 70

    def test_returns_validation_result(self):
        docs = [_doc("aadhaar", name="Ramesh")]
        result = validate(docs)
        assert isinstance(result, ValidationResult)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_validate.py -v
```

Expected: `ImportError` — validate.py doesn't exist yet.

- [ ] **Step 3: Implement validate.py**

```python
import re
from dataclasses import dataclass, field
from Levenshtein import ratio as levenshtein_ratio


@dataclass
class ValidationCheck:
    field: str
    status: str  # MATCH | MISMATCH | MISSING
    documents: list[str]
    values: dict[str, str]


@dataclass
class ValidationResult:
    checks: list[ValidationCheck]
    overall_confidence: float  # 0–100


_DATE_SEP_RE = re.compile(r"[-/]")


def _normalise_date(date_str: str) -> str:
    """Normalise date separators so 14/03/1988 == 14-03-1988."""
    return _DATE_SEP_RE.sub("/", date_str.strip())


def _check_name_match(docs: list[dict]) -> ValidationCheck | None:
    named = [(d["doc_type"], d["fields"]["name"]["value"]) for d in docs if "name" in d["fields"]]
    if len(named) < 2:
        return None

    doc_types = [n[0] for n in named]
    values = {n[0]: n[1] for n in named}

    names = [n[1].lower() for n in named]
    # Compare all pairs — if any pair has ratio < 0.85, it's a mismatch
    status = "MATCH"
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if levenshtein_ratio(names[i], names[j]) < 0.85:
                status = "MISMATCH"
                break

    return ValidationCheck(field="name_match", status=status, documents=doc_types, values=values)


def _check_dob_match(docs: list[dict]) -> ValidationCheck | None:
    dob_docs = [(d["doc_type"], d["fields"]["dob"]["value"]) for d in docs if "dob" in d["fields"]]
    if len(dob_docs) < 2:
        return None

    doc_types = [d[0] for d in dob_docs]
    values = {d[0]: d[1] for d in dob_docs}

    normalised = [_normalise_date(d[1]) for d in dob_docs]
    status = "MATCH" if len(set(normalised)) == 1 else "MISMATCH"

    return ValidationCheck(field="dob_match", status=status, documents=doc_types, values=values)


def _check_district_match(docs: list[dict]) -> ValidationCheck | None:
    target_types = {"domicile_cert", "income_cert"}
    district_docs = [
        (d["doc_type"], d["fields"]["district"]["value"])
        for d in docs
        if d["doc_type"] in target_types and "district" in d["fields"]
    ]
    if len(district_docs) < 2:
        return None

    doc_types = [d[0] for d in district_docs]
    values = {d[0]: d[1] for d in district_docs}

    districts = [d[1].lower().strip() for d in district_docs]
    status = "MATCH" if len(set(districts)) == 1 else "MISMATCH"

    return ValidationCheck(field="district_match", status=status, documents=doc_types, values=values)


def validate(docs: list[dict]) -> ValidationResult:
    checks: list[ValidationCheck] = []

    name_check = _check_name_match(docs)
    if name_check:
        checks.append(name_check)

    dob_check = _check_dob_match(docs)
    if dob_check:
        checks.append(dob_check)

    district_check = _check_district_match(docs)
    if district_check:
        checks.append(district_check)

    # OCR confidence: average of all field confidence values
    all_confidences = [
        f["confidence"]
        for d in docs
        for f in d["fields"].values()
    ]
    avg_ocr_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.5

    # Cross-val pass rate
    if checks:
        pass_rate = sum(1 for c in checks if c.status == "MATCH") / len(checks)
    else:
        pass_rate = 1.0  # no checks to run = no contradictions

    overall = ((avg_ocr_conf * 0.5) + (pass_rate * 0.5)) * 100

    return ValidationResult(checks=checks, overall_confidence=round(overall, 1))
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_validate.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
cd BLOCKATHON
git add backend/pipeline/validate.py backend/tests/test_validate.py
git commit -m "feat: cross-validation stage — name/DOB/district checks + confidence scoring"
```

---

### Task 9: Blockchain stage

**Files:**
- Create: `backend/pipeline/blockchain.py`
- Create: `backend/tests/test_blockchain.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_blockchain.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from pipeline.blockchain import store_verification, BlockchainResult


def _make_mock_w3(tx_hash_hex: str = "0x" + "ab" * 32, block_number: int = 12345):
    mock_w3 = MagicMock()
    mock_receipt = MagicMock()
    mock_receipt.transactionHash = bytes.fromhex(tx_hash_hex[2:])
    mock_receipt.blockNumber = block_number
    mock_w3.eth.wait_for_transaction_receipt.return_value = mock_receipt
    mock_w3.eth.get_transaction_count.return_value = 1
    mock_w3.eth.gas_price = 30_000_000_000
    mock_w3.eth.account.sign_transaction.return_value = MagicMock(
        rawTransaction=b"raw_tx"
    )
    mock_w3.eth.send_raw_transaction.return_value = bytes.fromhex(tx_hash_hex[2:])
    mock_w3.to_checksum_address = lambda x: x
    return mock_w3


_TEST_ENV = {
    "CONTRACT_ADDRESS": "0xTEST000000000000000000000000000000000001",
    "DEPLOYER_PRIVATE_KEY": "0x" + "aa" * 32,
    "POLYGON_RPC_URL": "https://rpc-amoy.polygon.technology/",
}


def test_store_verification_returns_result(mocker):
    mock_w3 = _make_mock_w3()
    mock_contract = MagicMock()
    mock_contract.functions.storeVerification.return_value.build_transaction.return_value = {
        "gas": 200000, "gasPrice": 30_000_000_000, "nonce": 1, "data": "0x"
    }

    mocker.patch.dict("os.environ", _TEST_ENV)
    mocker.patch("pipeline.blockchain._get_w3", return_value=mock_w3)
    mocker.patch("pipeline.blockchain._get_contract", return_value=mock_contract)
    mocker.patch("pipeline.blockchain._get_account_address", return_value="0xDEAD")

    result = store_verification("UK-2024-00183", [b"a" * 32], 91, True)

    assert isinstance(result, BlockchainResult)
    assert result.block_number == 12345
    assert result.tx_hash.startswith("0x")
    assert result.contract_address == _TEST_ENV["CONTRACT_ADDRESS"]


def test_store_verification_failure_returns_none(mocker):
    mocker.patch("pipeline.blockchain._get_w3", side_effect=Exception("RPC unreachable"))

    result = store_verification("UK-2024-00183", [b"a" * 32], 91, True)
    assert result is None


def test_blockchain_result_has_polygonscan_url(mocker):
    mock_w3 = _make_mock_w3()
    mock_contract = MagicMock()
    mock_contract.functions.storeVerification.return_value.build_transaction.return_value = {
        "gas": 200000, "gasPrice": 30_000_000_000, "nonce": 1, "data": "0x"
    }

    mocker.patch.dict("os.environ", _TEST_ENV)
    mocker.patch("pipeline.blockchain._get_w3", return_value=mock_w3)
    mocker.patch("pipeline.blockchain._get_contract", return_value=mock_contract)
    mocker.patch("pipeline.blockchain._get_account_address", return_value="0xDEAD")

    result = store_verification("UK-2024-00183", [b"a" * 32], 91, True)
    assert result is not None
    assert "amoy.polygonscan.com" in result.polygonscan_url
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_blockchain.py -v
```

Expected: `ImportError` — blockchain.py doesn't exist yet.

- [ ] **Step 3: Implement blockchain.py**

```python
import os
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

CONTRACT_ABI_PATH = Path(__file__).parent.parent.parent / "contracts" / "artifacts" / "contracts" / "DocumentVerification.sol" / "DocumentVerification.json"


@dataclass
class BlockchainResult:
    tx_hash: str
    block_number: int
    contract_address: str
    polygonscan_url: str


def _get_w3() -> Web3:
    rpc_url = os.environ["POLYGON_RPC_URL"]
    return Web3(Web3.HTTPProvider(rpc_url))


def _get_contract(w3: Web3):
    contract_address = os.environ["CONTRACT_ADDRESS"]
    abi_json = json.loads(CONTRACT_ABI_PATH.read_text())
    abi = abi_json["abi"]
    return w3.eth.contract(
        address=w3.to_checksum_address(contract_address),
        abi=abi,
    )


def _get_account_address() -> str:
    private_key = os.environ["DEPLOYER_PRIVATE_KEY"]
    from eth_account import Account
    return Account.from_key(private_key).address


def store_verification(
    applicant_id: str,
    doc_hashes: list[bytes],
    confidence: int,
    is_verified: bool,
) -> BlockchainResult | None:
    try:
        w3 = _get_w3()
        contract = _get_contract(w3)
        account_address = _get_account_address()
        private_key = os.environ["DEPLOYER_PRIVATE_KEY"]
        contract_address = os.environ["CONTRACT_ADDRESS"]

        # Convert raw bytes to bytes32
        doc_hashes_bytes32 = [h[:32].ljust(32, b"\x00") for h in doc_hashes]

        tx = contract.functions.storeVerification(
            applicant_id,
            doc_hashes_bytes32,
            confidence,
            is_verified,
        ).build_transaction({
            "from": account_address,
            "nonce": w3.eth.get_transaction_count(account_address),
            "gas": 300_000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=60)

        tx_hash = "0x" + receipt.transactionHash.hex()

        return BlockchainResult(
            tx_hash=tx_hash,
            block_number=receipt.blockNumber,
            contract_address=contract_address,
            polygonscan_url=f"https://amoy.polygonscan.com/tx/{tx_hash}",
        )

    except Exception as e:
        logger.error(f"Blockchain write failed: {e}")
        return None
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd BLOCKATHON/backend
python -m pytest tests/test_blockchain.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Run all backend tests**

```bash
cd BLOCKATHON/backend
python -m pytest tests/ -v
```

Expected: all tests pass (compress, extract, validate, ocr, blockchain).

- [ ] **Step 6: Commit**

```bash
cd BLOCKATHON
git add backend/pipeline/blockchain.py backend/tests/test_blockchain.py
git commit -m "feat: blockchain stage — Polygon Amoy write with web3.py, graceful failure"
```

---

## Chunk 3: Frontend

### Task 10: React + Vite + Tailwind setup

**Files:**
- Create: `frontend/` (scaffolded by Vite)
- Create: `frontend/src/index.css`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/vite.config.js`

- [ ] **Step 1: Scaffold React app with Vite**

```bash
cd BLOCKATHON
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install axios react-router-dom
```

- [ ] **Step 2: Configure Tailwind**

Edit `frontend/tailwind.config.js`:

```javascript
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

- [ ] **Step 3: Write global CSS with design system**

Replace `frontend/src/index.css`:

```css
:root {
  --sky-blue-light: #8ecae6;
  --blue-green: #219ebc;
  --deep-space-blue: #023047;
  --amber-flame: #ffb703;
  --princeton-orange: #fb8500;
}

@tailwind base;
@tailwind components;
@tailwind utilities;

* { box-sizing: border-box; }

body {
  background: #0b1a26;
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  margin: 0;
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes chipPop {
  0%   { transform: scale(0.7); opacity: 0; }
  70%  { transform: scale(1.08); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes fillBar {
  from { width: 0; }
}

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 6px var(--amber-flame); }
  50%       { box-shadow: 0 0 16px var(--amber-flame), 0 0 32px rgba(255,183,3,0.3); }
}

@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}

@keyframes blink {
  0%, 100% { opacity: 1; } 50% { opacity: 0.3; }
}

.animate-fade-slide { animation: fadeSlideIn 0.5s ease both; }
.animate-chip-pop   { animation: chipPop 0.4s ease both; }
.animate-fill-bar   { animation: fillBar 1.2s cubic-bezier(0.4,0,0.2,1) both; }
.animate-pulse-glow { animation: pulseGlow 2s ease-in-out infinite; }
.animate-blink      { animation: blink 2s ease-in-out infinite; }

.btn-shimmer {
  position: relative;
  overflow: hidden;
}
.btn-shimmer::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  animation: shimmer 2.5s ease-in-out infinite;
}
```

- [ ] **Step 4: Configure Vite proxy**

Replace `frontend/vite.config.js`:

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

- [ ] **Step 5: Verify dev server starts**

```bash
cd BLOCKATHON/frontend
npm run dev
```

Expected: `Local: http://localhost:5173/`. Ctrl+C to stop.

- [ ] **Step 6: Commit**

```bash
cd BLOCKATHON
git add frontend/
git commit -m "chore: React + Vite + Tailwind frontend scaffold with design system CSS"
```

---

### Task 11: API client and UploadPage

**Files:**
- Create: `frontend/src/api.js`
- Create: `frontend/src/pages/UploadPage.jsx`
- Create: `frontend/src/components/DocChip.jsx`

- [ ] **Step 1: Create frontend/.env.local**

```
VITE_OFFICER_KEY=demo-officer-key-change-in-prod
```

Keep this in sync with `OFFICER_API_KEY` in the root `.env`.

- [ ] **Step 2: Create api.js**

```javascript
// frontend/src/api.js
import axios from "axios";

const OFFICER_KEY = import.meta.env.VITE_OFFICER_KEY || "demo-officer-key-change-in-prod";

export async function verifyDocuments(applicantId, files) {
  const form = new FormData();
  form.append("applicant_id", applicantId);
  files.forEach((f) => form.append("files", f));
  const { data } = await axios.post("/api/verify", form);
  return data;
}

export async function listVerifications() {
  const { data } = await axios.get("/api/verifications", {
    headers: { "X-Officer-Key": OFFICER_KEY },
  });
  return data.verifications;
}

export async function getVerification(applicantId) {
  const { data } = await axios.get(`/api/verifications/${applicantId}`, {
    headers: { "X-Officer-Key": OFFICER_KEY },
  });
  return data;
}
```

- [ ] **Step 3: Create DocChip.jsx**

```jsx
// frontend/src/components/DocChip.jsx
export default function DocChip({ label, ready, delay = 0 }) {
  return (
    <div
      className="animate-chip-pop flex items-center gap-2 px-3 py-1 rounded-full border text-xs"
      style={{
        animationDelay: `${delay}ms`,
        background: "#0d3350",
        borderColor: "#1a4a6a",
        color: "var(--sky-blue-light)",
      }}
    >
      <span
        className={ready ? "animate-blink" : ""}
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: ready ? "#22c55e" : "var(--amber-flame)",
          display: "inline-block",
        }}
      />
      {label}
    </div>
  );
}
```

- [ ] **Step 4: Create UploadPage.jsx**

```jsx
// frontend/src/pages/UploadPage.jsx
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import DocChip from "../components/DocChip";
import { verifyDocuments } from "../api";

const DOC_TYPES = [
  "Aadhaar Card",
  "PAN Card",
  "Income Cert.",
  "Domicile Cert.",
  "Caste Cert.",
];

export default function UploadPage() {
  const [applicantId, setApplicantId] = useState("");
  const [fullName, setFullName] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onDrop = useCallback((e) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer?.files || e.target.files || []);
    setFiles((prev) => [...prev, ...dropped].slice(0, 5));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!applicantId.trim()) return setError("Application ID is required");
    if (!fullName.trim()) return setError("Full name is required");
    if (files.length === 0) return setError("Upload at least one document");
    setError("");
    setLoading(true);
    try {
      const result = await verifyDocuments(applicantId.trim(), files);
      navigate(`/result/${result.applicant_id}`, { state: { result } });
    } catch (err) {
      setError(err.response?.data?.detail || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div
        className="animate-fade-slide w-full max-w-md rounded-xl border p-6"
        style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}
      >
        {/* Nav */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b" style={{ borderColor: "#0d3350" }}>
          <span className="font-bold text-white">
            Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
          </span>
          <span className="text-xs px-2 py-1 rounded-full border" style={{ background: "#0d3350", borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
            Apuni Sarkar
          </span>
        </div>

        <form onSubmit={handleSubmit}>
          <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Application Details</p>

          <div className="mb-3">
            <label className="text-xs mb-1 block" style={{ color: "#7a9bb5" }}>Application ID</label>
            <input
              className="w-full rounded-md px-3 py-2 text-sm outline-none transition-all"
              style={{ background: "#011e30", border: "1px solid #1a4a6a", color: "var(--sky-blue-light)" }}
              placeholder="UK-2024-00183"
              value={applicantId}
              onChange={(e) => setApplicantId(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label className="text-xs mb-1 block" style={{ color: "#7a9bb5" }}>Full Name (as on Aadhaar)</label>
            <input
              className="w-full rounded-md px-3 py-2 text-sm outline-none transition-all"
              style={{ background: "#011e30", border: "1px solid #1a4a6a", color: "var(--sky-blue-light)" }}
              placeholder="Ramesh Kumar Negi"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <p className="text-xs uppercase tracking-widest mb-2 mt-4" style={{ color: "#4a7a99" }}>Upload Documents</p>

          <div
            className="rounded-lg p-4 mb-3 text-center cursor-pointer transition-all"
            style={{ border: "1.5px dashed #1a4a6a", background: "#011e30" }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            onClick={() => document.getElementById("file-input").click()}
          >
            <div className="text-2xl mb-1">📄</div>
            <p className="text-xs" style={{ color: "#4a7a99" }}>
              <strong style={{ color: "var(--sky-blue-light)" }}>Click to upload</strong> or drag & drop
            </p>
            <p className="text-xs mt-1" style={{ color: "#2a5a77" }}>JPEG · PNG · PDF · Max 20MB each</p>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.pdf"
              className="hidden"
              onChange={onDrop}
            />
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {DOC_TYPES.map((label, i) => (
              <DocChip
                key={label}
                label={label}
                ready={files.length > i}
                delay={i * 80}
              />
            ))}
          </div>

          {files.length > 0 && (
            <p className="text-xs mb-3" style={{ color: "var(--blue-green)" }}>
              {files.length} file{files.length > 1 ? "s" : ""} selected: {files.map((f) => f.name).join(", ")}
            </p>
          )}

          {error && <p className="text-xs mb-3" style={{ color: "#f87171" }}>{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="btn-shimmer w-full py-2.5 rounded-md font-semibold text-sm text-white transition-all"
            style={{ background: loading ? "#555" : "var(--princeton-orange)" }}
          >
            {loading ? "Verifying..." : "Submit for Verification →"}
          </button>

          <p className="text-center text-xs mt-2" style={{ color: "#2a5a77" }}>
            Documents are compressed & verified automatically. Hashed on Polygon blockchain.
          </p>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
cd BLOCKATHON
git add frontend/.env.local frontend/src/api.js frontend/src/pages/UploadPage.jsx frontend/src/components/DocChip.jsx
git commit -m "feat: citizen upload page with drag-and-drop, full name field, doc chips, API wiring"
```

---

### Task 12: Officer Dashboard + components

**Files:**
- Create: `frontend/src/components/BlockchainReceipt.jsx`
- Create: `frontend/src/components/VerificationCard.jsx`
- Create: `frontend/src/pages/DashboardPage.jsx`

- [ ] **Step 1: Create BlockchainReceipt.jsx**

```jsx
// frontend/src/components/BlockchainReceipt.jsx
export default function BlockchainReceipt({ blockchain }) {
  if (!blockchain) return null;

  return (
    <div
      className="rounded-lg p-3 mt-2 transition-all"
      style={{ background: "#011e30", border: "1px solid #1a4a6a" }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className="animate-pulse-glow"
          style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--amber-flame)", display: "inline-block" }}
        />
        <span className="text-xs uppercase tracking-widest" style={{ color: "var(--amber-flame)" }}>
          Polygon Blockchain Receipt
        </span>
      </div>
      <div className="space-y-1">
        {[
          ["TX Hash", blockchain.tx_hash],
          ["Block", blockchain.block_number?.toLocaleString()],
          ["Network", "Polygon Amoy"],
          ["Contract", blockchain.contract_address?.slice(0, 10) + "..."],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs">
            <span style={{ color: "#4a7a99" }}>{k}</span>
            <span className="font-mono" style={{ color: "var(--sky-blue-light)", fontSize: "0.62rem" }}>{v}</span>
          </div>
        ))}
      </div>
      {blockchain.polygonscan_url && (
        <a
          href={blockchain.polygonscan_url}
          target="_blank"
          rel="noreferrer"
          className="inline-block mt-2 text-xs px-2 py-1 rounded border transition-all hover:text-white"
          style={{ color: "var(--blue-green)", borderColor: "#1a4a6a" }}
        >
          ↗ View on Polygonscan
        </a>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create VerificationCard.jsx**

```jsx
// frontend/src/components/VerificationCard.jsx
import { useState } from "react";
import BlockchainReceipt from "./BlockchainReceipt";

function statusBadge(confidence, isVerified) {
  if (isVerified && confidence >= 75) return { label: "VERIFIED", bg: "#14532d", color: "#4ade80" };
  if (confidence < 55) return { label: "FLAGGED", bg: "#450a0a", color: "#f87171" };
  return { label: "REVIEW", bg: "#451a03", color: "#fbbf24" };
}

function ConfidenceBar({ value }) {
  return (
    <div style={{ background: "#0d3350", borderRadius: 20, height: 4, flex: 1, marginLeft: 8, overflow: "hidden" }}>
      <div
        className="animate-fill-bar"
        style={{ height: 4, borderRadius: 20, background: "var(--blue-green)", width: `${value}%` }}
      />
    </div>
  );
}

export default function VerificationCard({ verification, detail, loadingDetail, onOpen }) {
  const [open, setOpen] = useState(false);
  const badge = statusBadge(verification.overall_confidence, verification.is_verified);

  const handleToggle = () => {
    const next = !open;
    setOpen(next);
    if (next && !detail) onOpen(verification.applicant_id);
  };

  return (
    <div
      className="rounded-lg mb-2 transition-all"
      style={{ background: "#011e30", border: `1px solid ${open ? "var(--blue-green)" : "#0d3350"}` }}
    >
      {/* Row */}
      <div className="flex items-center justify-between px-3 py-2.5 cursor-pointer" onClick={handleToggle}>
        <div>
          <p className="text-sm font-medium text-white">{verification.applicant_id}</p>
          <p className="text-xs mt-0.5" style={{ color: "#4a7a99" }}>
            {verification.overall_confidence}% confidence · {verification.created_at?.slice(0, 16).replace("T", " ")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
            style={{ background: badge.bg, color: badge.color }}>
            {badge.label}
          </span>
          <span style={{ color: "#4a7a99" }}>{open ? "▲" : "▼"}</span>
        </div>
      </div>

      {/* Detail panel */}
      {open && loadingDetail && (
        <div className="px-3 pb-3 border-t text-xs" style={{ borderColor: "#0d3350", color: "#4a7a99" }}>
          Loading detail...
        </div>
      )}
      {open && !loadingDetail && detail && (
        <div className="px-3 pb-3 border-t" style={{ borderColor: "#0d3350" }}>
          {/* Documents */}
          {detail.documents?.map((doc) => (
            <div key={doc.doc_type} className="mt-3 rounded-lg p-3"
              style={{ background: "#021e2e", border: "1px solid #0d3350" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wider" style={{ color: "var(--blue-green)" }}>
                  {doc.doc_type.replace("_", " ")}
                </span>
                <div className="flex items-center gap-1 text-xs" style={{ color: "#22c55e" }}>
                  {Math.round(Object.values(doc.fields || {}).reduce((a, f) => a + f.confidence, 0)
                    / Math.max(Object.keys(doc.fields || {}).length, 1) * 100)}%
                  <ConfidenceBar value={Object.values(doc.fields || {}).reduce((a, f) => a + f.confidence, 0)
                    / Math.max(Object.keys(doc.fields || {}).length, 1) * 100} />
                </div>
              </div>
              {Object.entries(doc.fields || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs mb-1">
                  <span style={{ color: "#4a7a99" }}>{k}</span>
                  <span className="font-medium">
                    {v.value}
                    <span className="ml-1 text-xs" style={{ color: "#22c55e" }}>
                      {Math.round(v.confidence * 100)}%
                    </span>
                  </span>
                </div>
              ))}
              <div className="text-xs mt-1" style={{ color: "var(--amber-flame)" }}>
                {(doc.original_size / 1024).toFixed(0)} KB →{" "}
                {(doc.compressed_size / 1024).toFixed(0)} KB ({" "}
                {Math.round((1 - doc.compressed_size / doc.original_size) * 100)}% ↓)
              </div>
            </div>
          ))}

          {/* Cross-validation */}
          {detail.cross_validation?.length > 0 && (
            <div className="mt-3 rounded-lg p-3" style={{ background: "#021e2e", border: "1px solid #0d3350" }}>
              <p className="text-xs uppercase tracking-wider mb-2" style={{ color: "#4ade80" }}>Cross-Validation</p>
              {detail.cross_validation.map((check) => (
                <div key={check.field} className="flex items-center gap-2 text-xs mb-1.5">
                  <span>{check.status === "MATCH" ? "✅" : check.status === "MISMATCH" ? "❌" : "⚠️"}</span>
                  <span style={{ color: "#7a9bb5", flex: 1 }}>{check.field.replace("_", " ")}</span>
                  <span className="font-semibold text-xs"
                    style={{ color: check.status === "MATCH" ? "#22c55e" : check.status === "MISMATCH" ? "#f87171" : "#fbbf24" }}>
                    {check.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          <BlockchainReceipt blockchain={detail.blockchain} />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create DashboardPage.jsx**

```jsx
// frontend/src/pages/DashboardPage.jsx
import { useState, useEffect } from "react";
import { listVerifications, getVerification } from "../api";
import VerificationCard from "../components/VerificationCard";

export default function DashboardPage() {
  const [verifications, setVerifications] = useState([]);
  const [details, setDetails] = useState({});
  const [loadingDetails, setLoadingDetails] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listVerifications()
      .then(setVerifications)
      .catch(() => setError("Failed to load verifications. Check officer key."))
      .finally(() => setLoading(false));
  }, []);

  const handleCardOpen = async (applicantId) => {
    if (details[applicantId]) return; // already loaded
    setLoadingDetails((prev) => ({ ...prev, [applicantId]: true }));
    try {
      const detail = await getVerification(applicantId);
      setDetails((prev) => ({ ...prev, [applicantId]: detail }));
    } catch {
      // fail silently — card still shows summary
    } finally {
      setLoadingDetails((prev) => ({ ...prev, [applicantId]: false }));
    }
  };

  const verified = verifications.filter((v) => v.is_verified && v.overall_confidence >= 75).length;
  const flagged = verifications.filter((v) => v.overall_confidence < 55).length;
  const pending = verifications.length - verified - flagged;

  const stats = [
    { label: "Pending", value: pending, color: "var(--princeton-orange)" },
    { label: "Verified", value: verified, color: "#22c55e" },
    { label: "Flagged", value: flagged, color: "#f87171" },
  ];

  return (
    <div className="min-h-screen p-6 max-w-2xl mx-auto">
      {/* Nav */}
      <div className="animate-fade-slide flex items-center justify-between mb-6 pb-4 border-b" style={{ borderColor: "#0d3350" }}>
        <span className="font-bold text-white">
          Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
        </span>
        <span className="text-xs px-2 py-1 rounded-full border" style={{ background: "#0d3350", borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
          Officer View
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {stats.map(({ label, value, color }, i) => (
          <div
            key={label}
            className="animate-fade-slide rounded-lg p-3 transition-all"
            style={{ animationDelay: `${i * 80}ms`, background: "#011e30", border: "1px solid #0d3350" }}
          >
            <div className="text-xl font-bold" style={{ color }}>{value}</div>
            <div className="text-xs uppercase tracking-wider mt-0.5" style={{ color: "#4a7a99" }}>{label}</div>
          </div>
        ))}
      </div>

      <p className="text-xs uppercase tracking-widest mb-3" style={{ color: "#4a7a99" }}>Recent Applications</p>

      {loading && <p className="text-sm" style={{ color: "#4a7a99" }}>Loading...</p>}
      {error && <p className="text-sm" style={{ color: "#f87171" }}>{error}</p>}

      {verifications.map((v) => (
        <VerificationCard
          key={v.applicant_id}
          verification={v}
          detail={details[v.applicant_id]}
          loadingDetail={!!loadingDetails[v.applicant_id]}
          onOpen={handleCardOpen}
        />
      ))}

      {!loading && verifications.length === 0 && !error && (
        <p className="text-sm text-center mt-8" style={{ color: "#4a7a99" }}>No verifications yet. Submit documents to get started.</p>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
cd BLOCKATHON
git add frontend/src/components/ frontend/src/pages/DashboardPage.jsx
git commit -m "feat: officer dashboard with verification cards, confidence bars, blockchain receipt"
```

---

### Task 13: Router, App.jsx, and final wiring

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/pages/ResultPage.jsx`
- Modify: `frontend/index.html`

- [ ] **Step 1: Create ResultPage.jsx (post-submit redirect)**

```jsx
// frontend/src/pages/ResultPage.jsx
import { useLocation, useNavigate, Link } from "react-router-dom";
import BlockchainReceipt from "../components/BlockchainReceipt";

export default function ResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const result = state?.result;

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p style={{ color: "#4a7a99" }}>No result data. </p>
          <button onClick={() => navigate("/")} style={{ color: "var(--blue-green)" }}>Go back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 max-w-lg mx-auto">
      <div className="animate-fade-slide rounded-xl p-6 border" style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}>
        <div className="flex items-center justify-between mb-4">
          <span className="font-bold text-white">
            Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
          </span>
          <span className={`text-xs px-2 py-1 rounded-full font-semibold`}
            style={{
              background: result.is_verified ? "#14532d" : "#450a0a",
              color: result.is_verified ? "#4ade80" : "#f87171"
            }}>
            {result.is_verified ? "✓ VERIFIED" : "⚠ REVIEW REQUIRED"}
          </span>
        </div>

        <p className="text-xs mb-1" style={{ color: "#4a7a99" }}>Application ID</p>
        <p className="font-medium mb-4">{result.applicant_id}</p>

        <p className="text-xs mb-1" style={{ color: "#4a7a99" }}>Overall Confidence</p>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg font-bold" style={{ color: "var(--blue-green)" }}>{result.overall_confidence}%</span>
          <div style={{ flex: 1, background: "#0d3350", borderRadius: 20, height: 6, overflow: "hidden" }}>
            <div className="animate-fill-bar" style={{ height: 6, borderRadius: 20, background: "var(--blue-green)", width: `${result.overall_confidence}%` }} />
          </div>
        </div>

        <p className="text-xs uppercase tracking-wider mb-2" style={{ color: "#4a7a99" }}>Documents Processed</p>
        {result.documents?.map((doc) => (
          <div key={doc.doc_type} className="rounded-lg p-3 mb-2" style={{ background: "#011e30", border: "1px solid #0d3350" }}>
            <p className="text-xs font-medium mb-1" style={{ color: "var(--blue-green)" }}>
              {doc.doc_type.replace(/_/g, " ").toUpperCase()}
            </p>
            <p className="text-xs" style={{ color: "var(--amber-flame)" }}>
              {(doc.original_size / 1024).toFixed(0)} KB → {(doc.compressed_size / 1024).toFixed(0)} KB
              ({Math.round((1 - doc.compressed_size / doc.original_size) * 100)}% reduction)
            </p>
          </div>
        ))}

        <BlockchainReceipt blockchain={result.blockchain} />

        <div className="flex gap-3 mt-4">
          <button onClick={() => navigate("/")} className="flex-1 py-2 rounded-md text-sm border transition-all"
            style={{ borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
            Upload More
          </button>
          <Link to="/dashboard" className="flex-1 py-2 rounded-md text-sm text-center font-semibold"
            style={{ background: "var(--princeton-orange)", color: "#fff" }}>
            Officer View →
          </Link>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create App.jsx**

```jsx
// frontend/src/App.jsx
import { Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import ResultPage from "./pages/ResultPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/result/:id" element={<ResultPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
    </Routes>
  );
}
```

- [ ] **Step 3: Create main.jsx**

```jsx
// frontend/src/main.jsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
```

- [ ] **Step 4: Update index.html title**

Edit `frontend/index.html` — change `<title>` to `<title>DocVerify — Apuni Sarkar</title>`.

- [ ] **Step 5: Start both servers and do full end-to-end smoke test**

Terminal 1 (backend):
```bash
cd BLOCKATHON/backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Terminal 2 (frontend):
```bash
cd BLOCKATHON/frontend
npm run dev
```

Open http://localhost:5173 — verify:
- [ ] Upload page renders with correct color scheme
- [ ] Can select files (doc chips turn green as files are selected)
- [ ] Submitting calls `/api/verify` (check backend terminal)
- [ ] Result page shows confidence bar and blockchain receipt
- [ ] `/dashboard` loads and shows the verification

- [ ] **Step 6: Run all backend tests one final time**

```bash
cd BLOCKATHON/backend
source .venv/bin/activate
python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Final commit**

```bash
cd BLOCKATHON
git add frontend/src/
git commit -m "feat: React router, result page, full frontend wiring — end-to-end complete"
```

---

## Quick Reference

### Running the project

```bash
# Backend
cd BLOCKATHON/backend && source .venv/bin/activate && uvicorn main:app --reload

# Frontend
cd BLOCKATHON/frontend && npm run dev

# Tests
cd BLOCKATHON/backend && python -m pytest tests/ -v

# Deploy contract
cd BLOCKATHON/contracts && npx hardhat run scripts/deploy.js --network amoy

# Contract tests
cd BLOCKATHON/contracts && npx hardhat test
```

### Environment variables needed before running

| Variable | Where to get it |
|---|---|
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP Console → IAM → Service Accounts → JSON key |
| `POLYGON_RPC_URL` | Alchemy/Infura Amoy endpoint (or `https://rpc-amoy.polygon.technology/`) |
| `DEPLOYER_PRIVATE_KEY` | MetaMask → Account Details → Export Private Key |
| `CONTRACT_ADDRESS` | Output of `npx hardhat run scripts/deploy.js --network amoy` |
| `OFFICER_API_KEY` | Any string (used as `X-Officer-Key` header in backend) |
| `VITE_OFFICER_KEY` | Same value as `OFFICER_API_KEY` — set in `frontend/.env.local` for Vite |
