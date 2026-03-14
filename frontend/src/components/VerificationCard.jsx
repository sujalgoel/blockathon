import { useState } from "react";
import BlockchainReceipt from "./BlockchainReceipt";

function statusBadge(confidence, isVerified) {
  if (isVerified && confidence >= 75) return { label: "VERIFIED", bg: "#14532d", color: "#4ade80" };
  if (confidence < 55) return { label: "FLAGGED", bg: "#450a0a", color: "#f87171" };
  return { label: "REVIEW", bg: "#451a03", color: "#fbbf24" };
}

function ConfidenceBar({ value }) {
  return (
    <div style={{ background: "#0d3350", borderRadius: 20, height: 4, flex: 1, marginLeft: 8, overflow: "hidden" }}>
      <div
        className="animate-fill-bar"
        style={{ height: 4, borderRadius: 20, background: "var(--blue-green)", width: `${value}%` }}
      />
    </div>
  );
}

export default function VerificationCard({ verification, detail, loadingDetail, onOpen }) {
  const [open, setOpen] = useState(false);
  const badge = statusBadge(verification.overall_confidence, verification.is_verified);

  const handleToggle = () => {
    const next = !open;
    setOpen(next);
    if (next && !detail) onOpen(verification.applicant_id);
  };

  return (
    <div
      className="rounded-lg mb-2 transition-all"
      style={{ background: "#011e30", border: `1px solid ${open ? "var(--blue-green)" : "#0d3350"}` }}
    >
      {/* Row */}
      <div className="flex items-center justify-between px-3 py-2.5 cursor-pointer" onClick={handleToggle}>
        <div>
          <p className="text-sm font-medium text-white">{verification.applicant_id}</p>
          <p className="text-xs mt-0.5" style={{ color: "#4a7a99" }}>
            {verification.overall_confidence}% confidence · {verification.created_at?.slice(0, 16).replace("T", " ")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={`http://localhost:8000/api/verifications/${verification.applicant_id}?key=${import.meta.env.VITE_OFFICER_KEY || "18ca1fdc64eb3f5f3b109ac3908624776866c6a00cf101a2f25676d05fac4335"}`}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="text-xs px-2 py-0.5 rounded border transition-all hover:text-white"
            style={{ color: "var(--blue-green)", borderColor: "#1a4a6a" }}
          >
            JSON ↗
          </a>
          <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
            style={{ background: badge.bg, color: badge.color }}>
            {badge.label}
          </span>
          <span style={{ color: "#4a7a99" }}>{open ? "▲" : "▼"}</span>
        </div>
      </div>

      {/* Detail panel */}
      {open && loadingDetail && (
        <div className="px-3 pb-3 border-t text-xs" style={{ borderColor: "#0d3350", color: "#4a7a99" }}>
          Loading detail...
        </div>
      )}
      {open && !loadingDetail && detail && (
        <div className="px-3 pb-3 border-t" style={{ borderColor: "#0d3350" }}>
          {/* Documents */}
          {detail.documents?.map((doc) => (
            <div key={doc.doc_type} className="mt-3 rounded-lg p-3"
              style={{ background: "#021e2e", border: "1px solid #0d3350" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wider" style={{ color: "var(--blue-green)" }}>
                  {doc.doc_type.replace("_", " ")}
                </span>
                <div className="flex items-center gap-1 text-xs" style={{ color: "#22c55e" }}>
                  {Math.round(Object.values(doc.fields || {}).reduce((a, f) => a + f.confidence, 0)
                    / Math.max(Object.keys(doc.fields || {}).length, 1) * 100)}%
                  <ConfidenceBar value={Object.values(doc.fields || {}).reduce((a, f) => a + f.confidence, 0)
                    / Math.max(Object.keys(doc.fields || {}).length, 1) * 100} />
                </div>
              </div>
              {Object.entries(doc.fields || {}).map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs mb-1">
                  <span style={{ color: "#4a7a99" }}>{k}</span>
                  <span className="font-medium">
                    {v.value}
                    <span className="ml-1 text-xs" style={{ color: "#22c55e" }}>
                      {Math.round(v.confidence * 100)}%
                    </span>
                  </span>
                </div>
              ))}
              <div className="text-xs mt-1" style={{ color: "var(--amber-flame)" }}>
                {(doc.original_size / 1024).toFixed(0)} KB →{" "}
                {(doc.compressed_size / 1024).toFixed(0)} KB ({" "}
                {Math.round((1 - doc.compressed_size / doc.original_size) * 100)}% ↓)
              </div>
            </div>
          ))}

          {/* Cross-validation */}
          {detail.cross_validation?.length > 0 && (
            <div className="mt-3 rounded-lg p-3" style={{ background: "#021e2e", border: "1px solid #0d3350" }}>
              <p className="text-xs uppercase tracking-wider mb-2" style={{ color: "#4ade80" }}>Cross-Validation</p>
              {detail.cross_validation.map((check) => (
                <div key={check.field} className="flex items-center gap-2 text-xs mb-1.5">
                  <span>{check.status === "MATCH" ? "✅" : check.status === "MISMATCH" ? "❌" : "⚠️"}</span>
                  <span style={{ color: "#7a9bb5", flex: 1 }}>{check.field.replace("_", " ")}</span>
                  <span className="font-semibold text-xs"
                    style={{ color: check.status === "MATCH" ? "#22c55e" : check.status === "MISMATCH" ? "#f87171" : "#fbbf24" }}>
                    {check.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          <BlockchainReceipt blockchain={detail.blockchain} />
        </div>
      )}
    </div>
  );
}
