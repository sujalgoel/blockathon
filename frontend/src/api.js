import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "";
const OFFICER_KEY = import.meta.env.VITE_OFFICER_KEY || "18ca1fdc64eb3f5f3b109ac3908624776866c6a00cf101a2f25676d05fac4335";

export async function verifyDocuments(applicantId, docType, uploads) {
  const form = new FormData();
  form.append("applicant_id", applicantId);
  form.append("doc_type", docType);
  if (uploads.aadhaar_front) form.append("aadhaar_front", uploads.aadhaar_front);
  if (uploads.aadhaar_back)  form.append("aadhaar_back",  uploads.aadhaar_back);
  if (uploads.pan)           form.append("pan",           uploads.pan);
  const { data } = await axios.post(`${BASE}/api/verify`, form);
  return data;
}

export async function listVerifications() {
  const { data } = await axios.get(`${BASE}/api/verifications`, {
    headers: { "X-Officer-Key": OFFICER_KEY },
  });
  return data.verifications;
}

export async function getVerification(applicantId) {
  const { data } = await axios.get(`${BASE}/api/verifications/${applicantId}`, {
    headers: { "X-Officer-Key": OFFICER_KEY },
  });
  return data;
}
