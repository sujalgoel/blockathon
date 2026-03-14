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
