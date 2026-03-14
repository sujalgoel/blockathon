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
_UID_RE       = re.compile(r"\b(\d{4})\s(\d{4})\s(\d{4})\b")
_DOB_FULL_RE  = re.compile(r"\b(\d{2}[/\-]\d{2}[/\-]\d{4}|\d{4}[/\-]\d{2}[/\-]\d{2})\b")
_YOB_RE       = re.compile(r"\b(19\d{2}|20[0-2]\d)\b")
_PAN_RE       = re.compile(r"\b([A-Z]{5}\d{4}[A-Z])\b")
_PIN_RE       = re.compile(r"\b(\d{6})\b")
_GENDER_RE    = re.compile(r"\b(Male|Female|Transgender|MALE|FEMALE|पुरुष|महिला)\b")
# Matches Title Case ("Sujal Goyal") OR ALL CAPS ("SUJAI GOYAL")
_TITLE_NAME   = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+)+$")
_CAPS_NAME    = re.compile(r"^[A-Z]{2,}(?: [A-Z]{2,})+$")


def _avg_conf(words: list, fragment: str) -> float:
    frags = set(fragment.lower().split())
    matched = [w for w in words if w.text.lower() in frags]
    if matched:
        return round(sum(w.confidence for w in matched) / len(matched), 3)
    return 0.9


def _after_label(text: str, *labels) -> str | None:
    """Extract the first non-empty line after any of the given labels."""
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\s*[:/]?\s*\n\s*([^\n]+)", re.IGNORECASE)
        m = pattern.search(text)
        if m:
            return m.group(1).strip()
    return None


def _name_lines(text: str, skip_words: set) -> list[str]:
    """Find name-like lines (Title Case or ALL CAPS), excluding known noise words."""
    lines = [l.strip() for l in text.splitlines()]
    result = []
    for l in lines:
        if any(s in l for s in skip_words):
            continue
        if _TITLE_NAME.match(l) or _CAPS_NAME.match(l):
            result.append(l)
    return result


def extract_fields(doc_type: str, text: str, words: list) -> ExtractionResult:
    if doc_type == "aadhaar_front":
        return _aadhaar_front(text, words)
    if doc_type == "aadhaar_back":
        return _aadhaar_back(text, words)
    if doc_type == "pan":
        return _pan(text, words)
    return ExtractionResult(doc_type=doc_type)


# ─── Aadhaar Front ───────────────────────────────────────────────────────────

_AADHAAR_SKIP = {
    "Government", "India", "Unique", "Identification", "Authority",
    "Download", "GOVERNMENT", "INDIA", "UIDAI", "Aadhaar",
}


def _aadhaar_front(text: str, words: list) -> ExtractionResult:
    fields = {}

    # UID (12-digit in groups of 4)
    uid_m = _UID_RE.search(text)
    if uid_m:
        v = f"{uid_m.group(1)} {uid_m.group(2)} {uid_m.group(3)}"
        fields["uid"] = FieldResult(value=v, confidence=_avg_conf(words, v))

    # DOB — full date preferred, fallback to year of birth
    dob_m = _DOB_FULL_RE.search(text)
    if dob_m:
        fields["dob"] = FieldResult(value=dob_m.group(1), confidence=_avg_conf(words, dob_m.group(1)))
    else:
        yob_m = _YOB_RE.search(text)
        if yob_m:
            fields["year_of_birth"] = FieldResult(value=yob_m.group(1), confidence=0.85)

    # Gender
    gender_m = _GENDER_RE.search(text)
    if gender_m:
        g = gender_m.group(1)
        if g == "पुरुष":    g = "Male"
        elif g == "महिला": g = "Female"
        fields["gender"] = FieldResult(value=g.capitalize(), confidence=0.95)

    # Name — try label-based first, then fallback to name-line scan
    name_via_label = _after_label(text, "Name", "नाम")
    if name_via_label and (_TITLE_NAME.match(name_via_label) or _CAPS_NAME.match(name_via_label)):
        fields["name"] = FieldResult(value=name_via_label, confidence=_avg_conf(words, name_via_label))
    else:
        names = _name_lines(text, _AADHAAR_SKIP)
        if names:
            fields["name"] = FieldResult(value=names[0], confidence=_avg_conf(words, names[0]))

    # Mobile (masked — shows last 3 digits only)
    mob_m = re.search(r"XXXXXXX(\d{3})", text)
    if mob_m:
        fields["mobile_last3"] = FieldResult(value=f"XXXXXXX{mob_m.group(1)}", confidence=0.98)

    return ExtractionResult(doc_type="aadhaar_front", fields=fields)


# ─── Aadhaar Back ────────────────────────────────────────────────────────────

def _aadhaar_back(text: str, words: list) -> ExtractionResult:
    fields = {}

    # PIN code (6-digit)
    pin_m = _PIN_RE.search(text)
    if pin_m:
        fields["pin"] = FieldResult(value=pin_m.group(1), confidence=_avg_conf(words, pin_m.group(1)))

    # Address — capture lines starting from S/O, W/O, D/O, C/O, House, Vill, Near, or "Address"
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    addr_lines, capture = [], False
    for line in lines:
        if re.search(r"\bAddress\b|S/O|W/O|D/O|C/O|House|Vill|Near|Ward|Plot|Flat|Door", line, re.IGNORECASE):
            capture = True
        if capture:
            addr_lines.append(line)
        if capture and len(addr_lines) >= 6:
            break

    if addr_lines:
        full_addr = ", ".join(addr_lines[:6])
        fields["address"] = FieldResult(value=full_addr, confidence=0.88)

    # District — look for known Uttarakhand districts
    district_re = re.compile(
        r"\b(Chamoli|Dehradun|Haridwar|Nainital|Almora|Pithoragarh|Pauri|Tehri|"
        r"Rudraprayag|Uttarkashi|Bageshwar|Champawat|Udham Singh Nagar)\b",
        re.IGNORECASE,
    )
    dist_m = district_re.search(text)
    if dist_m:
        fields["district"] = FieldResult(value=dist_m.group(1).title(), confidence=0.92)

    # State
    state_m = re.search(r"\b(Uttarakhand|Uttar Pradesh|Delhi|Maharashtra|Karnataka|Tamil Nadu|Rajasthan|Gujarat|Bihar|West Bengal)\b", text, re.IGNORECASE)
    if state_m:
        fields["state"] = FieldResult(value=state_m.group(1).title(), confidence=0.92)

    return ExtractionResult(doc_type="aadhaar_back", fields=fields)


# ─── PAN Card ────────────────────────────────────────────────────────────────

_PAN_SKIP = {
    "Income", "Tax", "Department", "Government", "India", "Permanent",
    "Account", "INCOME", "TAX", "DEPARTMENT", "GOVT", "PERMANENT",
}


def _pan(text: str, words: list) -> ExtractionResult:
    fields = {}

    # PAN number (ABCDE1234F)
    pan_m = _PAN_RE.search(text)
    if pan_m:
        fields["pan_number"] = FieldResult(value=pan_m.group(1), confidence=_avg_conf(words, pan_m.group(1)))

    # DOB
    dob_m = _DOB_FULL_RE.search(text)
    if dob_m:
        fields["dob"] = FieldResult(value=dob_m.group(1), confidence=_avg_conf(words, dob_m.group(1)))

    # Name — label-based (most reliable for PAN)
    name_via_label = _after_label(text, "Name", "नाम")
    if name_via_label and (_TITLE_NAME.match(name_via_label) or _CAPS_NAME.match(name_via_label)):
        fields["name"] = FieldResult(value=name_via_label, confidence=_avg_conf(words, name_via_label))

    # Father's name — label-based
    father_via_label = _after_label(text, "Father's Name", "पिता का नाम")
    if father_via_label and (_TITLE_NAME.match(father_via_label) or _CAPS_NAME.match(father_via_label)):
        fields["father_name"] = FieldResult(value=father_via_label, confidence=_avg_conf(words, father_via_label))

    # Fallback: scan name lines if label-based failed
    if "name" not in fields or "father_name" not in fields:
        names = _name_lines(text, _PAN_SKIP)
        if "name" not in fields and len(names) >= 1:
            fields["name"] = FieldResult(value=names[0], confidence=_avg_conf(words, names[0]))
        if "father_name" not in fields and len(names) >= 2:
            fields["father_name"] = FieldResult(value=names[1], confidence=_avg_conf(words, names[1]))

    # Issue date (8-digit DDMMYYYY at end, different from DOB)
    # DOB already consumed the first date; find a second one
    all_dates = _DOB_FULL_RE.findall(text)
    if len(all_dates) >= 2:
        fields["issue_date"] = FieldResult(value=all_dates[-1], confidence=0.85)

    return ExtractionResult(doc_type="pan", fields=fields)
