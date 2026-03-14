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
