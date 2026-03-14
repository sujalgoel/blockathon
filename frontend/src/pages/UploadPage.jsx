import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import DocChip from "../components/DocChip";
import { verifyDocuments } from "../api";

const DOC_TYPES = [
  "Aadhaar Card",
  "PAN Card",
  "Income Cert.",
  "Domicile Cert.",
  "Caste Cert.",
];

export default function UploadPage() {
  const [applicantId, setApplicantId] = useState("");
  const [fullName, setFullName] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onDrop = useCallback((e) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer?.files || e.target.files || []);
    setFiles((prev) => [...prev, ...dropped].slice(0, 5));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!applicantId.trim()) return setError("Application ID is required");
    if (!fullName.trim()) return setError("Full name is required");
    if (files.length === 0) return setError("Upload at least one document");
    setError("");
    setLoading(true);
    try {
      const result = await verifyDocuments(applicantId.trim(), files);
      navigate(`/result/${result.applicant_id}`, { state: { result } });
    } catch (err) {
      setError(err.response?.data?.detail || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div
        className="animate-fade-slide w-full max-w-md rounded-xl border p-6"
        style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}
      >
        {/* Nav */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b" style={{ borderColor: "#0d3350" }}>
          <span className="font-bold text-white">
            Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
          </span>
          <span className="text-xs px-2 py-1 rounded-full border" style={{ background: "#0d3350", borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
            Apuni Sarkar
          </span>
        </div>

        <form onSubmit={handleSubmit}>
          <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Application Details</p>

          <div className="mb-3">
            <label className="text-xs mb-1 block" style={{ color: "#7a9bb5" }}>Application ID</label>
            <input
              className="w-full rounded-md px-3 py-2 text-sm outline-none transition-all"
              style={{ background: "#011e30", border: "1px solid #1a4a6a", color: "var(--sky-blue-light)" }}
              placeholder="UK-2024-00183"
              value={applicantId}
              onChange={(e) => setApplicantId(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <label className="text-xs mb-1 block" style={{ color: "#7a9bb5" }}>Full Name (as on Aadhaar)</label>
            <input
              className="w-full rounded-md px-3 py-2 text-sm outline-none transition-all"
              style={{ background: "#011e30", border: "1px solid #1a4a6a", color: "var(--sky-blue-light)" }}
              placeholder="Ramesh Kumar Negi"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <p className="text-xs uppercase tracking-widest mb-2 mt-4" style={{ color: "#4a7a99" }}>Upload Documents</p>

          <div
            className="rounded-lg p-4 mb-3 text-center cursor-pointer transition-all"
            style={{ border: "1.5px dashed #1a4a6a", background: "#011e30" }}
            onDragOver={(e) => e.preventDefault()}
            onDrop={onDrop}
            onClick={() => document.getElementById("file-input").click()}
          >
            <div className="text-2xl mb-1">📄</div>
            <p className="text-xs" style={{ color: "#4a7a99" }}>
              <strong style={{ color: "var(--sky-blue-light)" }}>Click to upload</strong> or drag & drop
            </p>
            <p className="text-xs mt-1" style={{ color: "#2a5a77" }}>JPEG · PNG · PDF · Max 20MB each</p>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.pdf"
              className="hidden"
              onChange={onDrop}
            />
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {DOC_TYPES.map((label, i) => (
              <DocChip
                key={label}
                label={label}
                ready={files.length > i}
                delay={i * 80}
              />
            ))}
          </div>

          {files.length > 0 && (
            <p className="text-xs mb-3" style={{ color: "var(--blue-green)" }}>
              {files.length} file{files.length > 1 ? "s" : ""} selected: {files.map((f) => f.name).join(", ")}
            </p>
          )}

          {error && <p className="text-xs mb-3" style={{ color: "#f87171" }}>{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="btn-shimmer w-full py-2.5 rounded-md font-semibold text-sm text-white transition-all"
            style={{ background: loading ? "#555" : "var(--princeton-orange)" }}
          >
            {loading ? "Verifying..." : "Submit for Verification →"}
          </button>

          <p className="text-center text-xs mt-2" style={{ color: "#2a5a77" }}>
            Documents are compressed & verified automatically. Hashed on Polygon blockchain.
          </p>
        </form>
      </div>
    </div>
  );
}
