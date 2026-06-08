# DocVerify — CLAUDE.md

DocVerify (PS01, IIT Roorkee Blockathon 2026): a document verification pipeline that compresses citizen ID documents, runs bilingual OCR, extracts and cross-validates fields, and anchors tamper-proof receipts on the Polygon Amoy blockchain. FastAPI backend + React/Vite frontend + Solidity contract.

## Hard rules

- **Never deploy.** Do not run `vercel`, `vercel --prod`, `railway up`, or any deploy command. Deploys are done by hand. Frontend → Vercel, backend → Railway.
- **Commits:** one-line messages. Don't commit or push unless explicitly asked.
- **Secrets:** real values live in `.env` (gitignored) and `gcp-credentials.json` (gitignored). Never commit them, never echo their contents. `.env.example` is the committed template.

## Layout

```
backend/      FastAPI monolith — main.py orchestrates the pipeline/ stages
  pipeline/   per file:  compress.py → ocr.py → extract.py
              per request: storage.py (R2) → validate.py → blockchain.py
  db/         schema.sql + queries.py (SQLite: db/verifications.db)
  tests/      pytest, one file per pipeline stage
contracts/    Solidity 0.8.24 + Hardhat — DocumentVerification.sol, scripts/deploy.js, tests
frontend/     React 18 + Vite + Tailwind — pages/ (Upload, Dashboard, Result), components/
docs/superpowers/   design spec + implementation plan
.superpowers/brainstorm/   early architecture + UI explorations
```

Pipeline is a synchronous FastAPI monolith: one `POST /api/verify` request runs every stage in order. `compress → ocr → extract` run once per uploaded file; the request then uploads each compressed file to R2, cross-validates across documents, anchors the receipt on-chain, and persists to SQLite. Each stage is an isolated module with a clean interface. The R2 upload is best-effort — a failure logs and skips rather than aborting the request. Routes live in `backend/main.py`: `POST /api/verify`, `GET /api/verifications`, `GET /api/verifications/{applicant_id}` (officer routes gated by `OFFICER_API_KEY`).

## Commands

```bash
# Backend (Python 3.13)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
pytest                          # tests; pytest.ini sets pythonpath=. and disables pytest_ethereum

# Frontend (Node 18+)
cd frontend && npm install
npm run dev                     # http://localhost:5173
npm run build

# Contracts (Hardhat)
cd contracts && npm install
npx hardhat test
npx hardhat run scripts/deploy.js --network amoy   # deploy is manual; network "amoy", chainId 80002
```

## Environment

Backend reads `.env` (see `.env.example`), grouped as: `GCP_*` (Vision OCR), `R2_*` (Cloudflare R2 document storage), `POLYGON_RPC_URL` / `DEPLOYER_PRIVATE_KEY` / `CONTRACT_ADDRESS` (Amoy chain writes), and `OFFICER_API_KEY` (officer-route auth). Frontend reads `frontend/.env.local` — **not** the root `.env` (Vite only loads env vars from its own dir and they must be `VITE_`-prefixed):

```
VITE_API_URL=http://localhost:8000
VITE_OFFICER_KEY=<officer key>
```

GCP credentials load from **individual** `GCP_*` env vars (not a `GOOGLE_APPLICATION_CREDENTIALS` file path) — this is what makes it work on Railway. `GCP_PRIVATE_KEY` keeps literal `\n` escaping.

## Gotchas (already handled — don't reintroduce)

- Polygon **Mumbai is deprecated** → use **Amoy** (chainId 80002). RPC: `https://rpc-amoy.polygon.technology/`.
- FastAPI 0.111: `@app.on_event("startup")` is deprecated → use the `lifespan` context manager (already wired in `main.py`).
- Compression of PNGs outputs JPEG bytes → the `format` field is set to `"jpeg"` for all images on purpose.
- Solidity events: `string indexed` breaks `withArgs` matching in tests → the contract avoids `indexed` on string params.
- Blockchain tests need `mocker.patch.dict("os.environ", ...)` for `CONTRACT_ADDRESS` + `DEPLOYER_PRIVATE_KEY`.
- R2 uploads must use the correct file extension (`.pdf` vs `.jpg`) based on the actual output type.
- `VerificationCard` (frontend) toggles via an `onOpen` prop + `handleToggle`, not an outer `onClick` wrapper, to avoid event-propagation bugs.

## Confidence model

`overall = avg OCR confidence × 50% + cross-validation pass rate × 50%`. Thresholds: ≥75 VERIFIED (written on-chain), 55–74 REVIEW, <55 FLAGGED. Docs missing key fields (PAN number for PAN, UID for Aadhaar) are flagged regardless of OCR confidence.
