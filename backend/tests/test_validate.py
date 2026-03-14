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
