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
