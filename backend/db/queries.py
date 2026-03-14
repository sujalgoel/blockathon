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
                """INSERT INTO documents (verification_id, doc_type, original_size, compressed_size, fields_json, compressed_url)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    verification_id,
                    doc["doc_type"],
                    doc["original_size"],
                    doc["compressed_size"],
                    json.dumps(doc["fields"]),
                    doc.get("compressed_url"),
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
            "SELECT doc_type, original_size, compressed_size, fields_json, compressed_url FROM documents WHERE verification_id = ?",
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
            **({"compressed_url": r["compressed_url"]} if r["compressed_url"] else {}),
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
