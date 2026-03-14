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
