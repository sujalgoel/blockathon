import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { verifyDocuments } from "../api";

function generateAppId() {
  const year = new Date().getFullYear();
  const num = String(Math.floor(10000 + Math.random() * 90000));
  return `UK-${year}-${num}`;
}

function DropZone({ slot, label, hint, file, onFile }) {
  const inputId = `file-${slot}`;
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const f = Array.from(e.dataTransfer?.files || e.target.files || [])[0];
    if (f) onFile(slot, f);
  }, [slot, onFile]);

  return (
    <div>
      <p className="text-xs mb-1.5" style={{ color: "#7a9bb5" }}>{label}</p>
      <div
        className="rounded-lg p-4 text-center cursor-pointer transition-all"
        style={{
          border: `1.5px dashed ${file ? "#166534" : "#1a4a6a"}`,
          background: file ? "#052e16" : "#011e30",
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => document.getElementById(inputId).click()}
      >
        {file ? (
          <div>
            <div className="text-lg mb-0.5">✅</div>
            <p className="text-xs font-medium" style={{ color: "#4ade80" }}>{file.name}</p>
            <p className="text-xs mt-0.5" style={{ color: "#166534" }}>
              {(file.size / 1024).toFixed(0)} KB · click to replace
            </p>
          </div>
        ) : (
          <div>
            <div className="text-xl mb-1">📄</div>
            <p className="text-xs" style={{ color: "#4a7a99" }}>
              <strong style={{ color: "var(--sky-blue-light)" }}>Click</strong> or drag & drop
            </p>
            {hint && <p className="text-xs mt-0.5" style={{ color: "#2a5a77" }}>{hint}</p>}
          </div>
        )}
        <input id={inputId} type="file" accept=".jpg,.jpeg,.png,.pdf" className="hidden" onChange={handleDrop} />
      </div>
    </div>
  );
}

const DOC_OPTIONS = [
  {
    id: "aadhaar",
    label: "Aadhaar Card",
    icon: "🪪",
    desc: "Upload front & back",
    slots: ["aadhaar_front", "aadhaar_back"],
    hint: "Both sides required",
  },
  {
    id: "pan",
    label: "PAN Card",
    icon: "🏦",
    desc: "Upload front only",
    slots: ["pan"],
    hint: "Front side required",
  },
];

const SLOT_META = {
  aadhaar_front: { label: "Front side", hint: "Name · DOB · UID number" },
  aadhaar_back:  { label: "Back side",  hint: "Address · QR code" },
  pan:           { label: "Front side", hint: "PAN number · Name · DOB" },
};

export default function UploadPage() {
  const applicantId = useRef(generateAppId()).current;
  const [docType, setDocType] = useState(null);
  const [uploads, setUploads] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onFile = useCallback((slot, file) => {
    setUploads((prev) => ({ ...prev, [slot]: file }));
    setError("");
  }, []);

  const selected = DOC_OPTIONS.find((d) => d.id === docType);
  const ready = selected && selected.slots.every((s) => uploads[s]);

  const handleSelect = (id) => {
    setDocType(id);
    setUploads({});
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ready) return;

    if (docType === "aadhaar") {
      const af = uploads.aadhaar_front;
      const ab = uploads.aadhaar_back;
      if (af.name === ab.name && af.size === ab.size)
        return setError("Front and back appear to be the same file.");
    }

    setError("");
    setLoading(true);
    try {
      const result = await verifyDocuments(applicantId, docType, uploads);
      navigate(`/result/${result.applicant_id}`, { state: { result } });
    } catch (err) {
      setError(err.response?.data?.detail || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-6" style={{ background: "#0b1a26" }}>
      <div className="max-w-md mx-auto">

        {/* Brand header */}
        <div className="animate-fade-slide flex items-center justify-between py-5 mb-6 border-b" style={{ borderColor: "#0d3350" }}>
          <span className="text-lg font-bold text-white">
            Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
          </span>
          <span className="text-xs px-2 py-1 rounded-full border" style={{ background: "#0d3350", borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
            Apuni Sarkar · Uttarakhand
          </span>
        </div>

        <div className="animate-fade-slide rounded-xl border p-6" style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}>
          <form onSubmit={handleSubmit}>

            {/* Reference ID */}
            <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Reference</p>
            <div className="rounded-md px-3 py-2 mb-5 flex items-center justify-between font-mono text-sm"
              style={{ background: "#011e30", border: "1px solid #0d3350", color: "var(--sky-blue-light)" }}>
              {applicantId}
              <span className="text-xs px-1.5 py-0.5 rounded-full ml-2" style={{ background: "#0d3350", color: "#4a7a99" }}>auto</span>
            </div>

            {/* Step 1: Choose doc type */}
            <p className="text-xs uppercase tracking-widest mb-3" style={{ color: "#4a7a99" }}>Select Document Type</p>
            <div className="grid grid-cols-2 gap-3 mb-5">
              {DOC_OPTIONS.map((opt) => {
                const active = docType === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => handleSelect(opt.id)}
                    className="rounded-lg p-4 text-left transition-all"
                    style={{
                      background: active ? "#011e30" : "#011520",
                      border: `1.5px solid ${active ? "var(--princeton-orange)" : "#1a4a6a"}`,
                    }}
                  >
                    <div className="text-2xl mb-2">{opt.icon}</div>
                    <p className="text-sm font-semibold" style={{ color: active ? "var(--sky-blue-light)" : "#4a7a99" }}>
                      {opt.label}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: active ? "#4a7a99" : "#2a5a77" }}>
                      {opt.desc}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Step 2: Upload zones */}
            {selected && (
              <div className="animate-fade-slide">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-px flex-1" style={{ background: "#0d3350" }} />
                  <p className="text-xs uppercase tracking-widest px-2" style={{ color: "var(--amber-flame)" }}>
                    {selected.label}
                  </p>
                  <div className="h-px flex-1" style={{ background: "#0d3350" }} />
                </div>

                <div className={`grid gap-3 mb-5 ${selected.slots.length > 1 ? "grid-cols-2" : "grid-cols-1"}`}>
                  {selected.slots.map((slot) => (
                    <DropZone
                      key={slot}
                      slot={slot}
                      label={SLOT_META[slot].label}
                      hint={SLOT_META[slot].hint}
                      file={uploads[slot] || null}
                      onFile={onFile}
                    />
                  ))}
                </div>

                {error && <p className="text-xs mb-3" style={{ color: "#f87171" }}>{error}</p>}

                <button
                  type="submit"
                  disabled={loading || !ready}
                  className="btn-shimmer w-full py-2.5 rounded-md font-semibold text-sm"
                  style={{
                    background: ready && !loading ? "var(--princeton-orange)" : "#0d2a3a",
                    color: ready && !loading ? "#fff" : "#4a7a99",
                  }}
                >
                  {loading ? "Verifying…" : ready ? "Submit for Verification →" : `Upload ${selected.slots.length > 1 ? "both sides" : "the document"} to continue`}
                </button>

                <p className="text-center text-xs mt-2" style={{ color: "#2a5a77" }}>
                  Compressed · OCR'd · Hashed on Polygon
                </p>
              </div>
            )}

          </form>
        </div>

      </div>
    </div>
  );
}
