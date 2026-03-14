# DocVerify — Intelligent Document Verification Engine

> Apuni Sarkar · Uttarakhand Government Portal
> IIT Roorkee Blockathon 2026 · PS01

**Team:** Team CORE &nbsp;|&nbsp; **Participant:** Sujal Goel &nbsp;|&nbsp; **ID:** cogni2053350

A full-stack pipeline that compresses citizen documents, runs bilingual OCR, extracts structured fields, cross-validates identity data, and writes tamper-proof verification receipts to the Polygon Amoy blockchain.

---

## Live Demo

| | |
|---|---|
| **Frontend** | https://doc-verify-core.vercel.app |
| **Backend API** | https://blockathon-production.up.railway.app |
| **Officer Dashboard Key** | `18ca1fdc64eb3f5f3b109ac3908624776866c6a00cf101a2f25676d05fac4335` |

---

## What It Does

Citizens upload their **Aadhaar Card** (front + back) or **PAN Card** through a government-themed portal. The system:

1. **Compresses** images up to 95% using Pillow + PyMuPDF while preserving text and QR legibility
2. **OCRs** documents via Google Vision API with Hindi + English language hints and per-word confidence scores
3. **Extracts** structured fields — name, DOB, UID, PAN number, father's name, gender, address, PIN, district
4. **Validates** that key identifying fields exist (PAN number for PAN cards, UID for Aadhaar)
5. **Cross-validates** extracted data across documents (fuzzy name match, exact DOB match)
6. **Hashes** compressed files with SHA-256 and writes to Polygon Amoy — tamper-proof and auditable on Polygonscan
7. **Uploads** optimised images to Cloudflare R2 and returns public URLs in the API response

---

## Architecture

```
Citizen Browser
      │
      ▼
React + Vite (Tailwind CSS)
      │  POST /api/verify
      ▼
FastAPI Backend
  ├── Compress     (Pillow / PyMuPDF)
  ├── OCR          (Google Cloud Vision)
  ├── Extract      (regex + label-based parsing)
  ├── Validate     (required fields + Levenshtein fuzzy match)
  ├── Store Image  (Cloudflare R2 via boto3)
  ├── Blockchain   (web3.py → Polygon Amoy)
  └── Persist      (SQLite)
      │
      ▼
Officer Dashboard  ←→  GET /api/verifications/:id?key=...
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TailwindCSS |
| Backend | Python 3.13, FastAPI |
| Compression | Pillow, PyMuPDF |
| OCR | Google Cloud Vision API |
| Field Extraction | Regex, label-based parsing, Levenshtein |
| Storage | SQLite (records), Cloudflare R2 (images) |
| Blockchain | Solidity 0.8.24, Hardhat, web3.py, Polygon Amoy |

---

## Smart Contract

Deployed on **Polygon Amoy** testnet:

```
Contract: 0x1a49660EA85eaE31d0157F8AE47D107D2C99C6C3
Network:  Polygon Amoy (chainId: 80002)
Explorer: https://amoy.polygonscan.com/address/0x1a49660EA85eaE31d0157F8AE47D107D2C99C6C3
```

Each verification stores:
- SHA-256 hashes of compressed documents (as `bytes32[]`)
- Confidence score (0–100)
- Verification status (`bool`)
- Applicant ID (`string`)
- Block timestamp (automatic)

---

## API

### `POST /api/verify`

Submit documents for verification.

```
Form fields:
  applicant_id   string          Auto-generated reference ID
  doc_type       "aadhaar"|"pan"
  aadhaar_front  file            Required if doc_type=aadhaar
  aadhaar_back   file            Required if doc_type=aadhaar
  pan            file            Required if doc_type=pan
```

**Response:**
```json
{
  "applicant_id": "UK-2026-38291",
  "documents": [
    {
      "doc_type": "pan",
      "original_size": 1653629,
      "compressed_size": 112321,
      "compressed_url": "https://pub-xxx.r2.dev/compressed/UK-2026-38291/pan.jpg",
      "fields": {
        "pan_number":  { "value": "ABCDE1234F", "confidence": 0.98 },
        "name":        { "value": "SUJAL GOEL", "confidence": 0.99 },
        "father_name": { "value": "SANJAY GOEL", "confidence": 0.99 },
        "dob":         { "value": "10/03/2005", "confidence": 0.99 }
      }
    }
  ],
  "cross_validation": [
    { "field": "pan_number_present", "status": "MATCH", "documents": [...], "values": {...} }
  ],
  "overall_confidence": 97,
  "is_verified": true,
  "blockchain": {
    "tx_hash": "0xabc...",
    "block_number": 35180285,
    "contract_address": "0x1a49...",
    "polygonscan_url": "https://amoy.polygonscan.com/tx/0xabc..."
  }
}
```

### `GET /api/verifications?key=<officer_key>`

List all verifications (officer only).

### `GET /api/verifications/:id?key=<officer_key>`

Full detail for a single application including compressed image URLs.

---

## Running Locally

### Prerequisites

- Python 3.13+
- Node.js 18+
- Google Cloud Vision API service account (set individual `GCP_*` env vars)
- Cloudflare R2 bucket
- Polygon Amoy wallet with MATIC (get from [faucet](https://faucet.polygon.technology/))

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env
# Fill in your values in .env

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Create .env.local:
echo "VITE_API_URL=http://localhost:8000" > .env.local
echo "VITE_OFFICER_KEY=your-officer-key" >> .env.local
npm run dev
```

Open **http://localhost:5173**

### Environment Variables

| Variable | Description |
|---|---|
| `GCP_PROJECT_ID` | GCP project ID |
| `GCP_PRIVATE_KEY_ID` | Service account private key ID |
| `GCP_PRIVATE_KEY` | Service account private key (with `\n` escaping) |
| `GCP_CLIENT_EMAIL` | Service account email |
| `GCP_CLIENT_ID` | Service account client ID |
| `POLYGON_RPC_URL` | Amoy RPC endpoint |
| `DEPLOYER_PRIVATE_KEY` | Wallet private key for blockchain writes |
| `CONTRACT_ADDRESS` | Deployed smart contract address |
| `OFFICER_API_KEY` | Secret key for officer dashboard access |
| `R2_ACCOUNT_ID` | Cloudflare R2 account ID |
| `R2_ACCESS_KEY_ID` | R2 access key |
| `R2_SECRET_ACCESS_KEY` | R2 secret key |
| `R2_BUCKET_NAME` | R2 bucket name |
| `R2_PUBLIC_URL` | R2 public domain |

---

## Confidence Score

```
Overall = (avg OCR confidence × 50%) + (cross-validation pass rate × 50%)
```

- **≥ 75%** → VERIFIED (written to blockchain)
- **55–74%** → REVIEW
- **< 55%** → FLAGGED

Documents missing key fields (PAN number, Aadhaar UID) are automatically flagged regardless of OCR confidence.
