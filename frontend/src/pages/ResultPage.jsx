import { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";

const DOC_LABELS = {
  aadhaar_front: "Aadhaar · Front",
  aadhaar_back: "Aadhaar · Back",
  pan: "PAN Card",
};

const FIELD_LABELS = {
  name: "Name",
  dob: "Date of Birth",
  gender: "Gender",
  uid: "Aadhaar UID",
  address: "Address",
  pin: "PIN Code",
  pan_number: "PAN Number",
  father_name: "Father's Name",
};

export default function ResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const result = state?.result;
  const [showJson, setShowJson] = useState(false);

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="animate-fade-slide w-full max-w-md rounded-xl border p-6 text-center"
          style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}>
          <p className="text-sm mb-4" style={{ color: "#4a7a99" }}>No result found.</p>
          <button onClick={() => navigate("/")}
            className="btn-shimmer px-5 py-2 rounded-md text-sm font-semibold text-white"
            style={{ background: "var(--princeton-orange)" }}>
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const verified = result.is_verified;
  const confidence = result.overall_confidence;

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: "#0b1a26" }}>
      <div className="animate-fade-slide w-full max-w-md rounded-xl border p-6"
        style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}>

        {/* Nav */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b" style={{ borderColor: "#0d3350" }}>
          <span className="font-bold text-white">
            Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
          </span>
          <span className="text-xs px-2 py-1 rounded-full border font-semibold"
            style={{
              background: verified ? "#0a2e1a" : "#2a0a0a",
              borderColor: verified ? "#14532d" : "#450a0a",
              color: verified ? "#4ade80" : "#f87171",
            }}>
            {verified ? "✓ VERIFIED" : "⚠ REVIEW"}
          </span>
        </div>

        {/* Applicant ID */}
        <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Application Reference</p>
        <div className="rounded-md px-3 py-2 mb-4" style={{ background: "#011e30", border: "1px solid #0d3350" }}>
          <p className="text-sm font-mono" style={{ color: "var(--sky-blue-light)" }}>{result.applicant_id}</p>
        </div>

        {/* Confidence */}
        <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Confidence Score</p>
        <div className="flex items-center gap-3 mb-5">
          <span className="text-2xl font-bold" style={{ color: verified ? "#4ade80" : "#fbbf24" }}>{confidence}%</span>
          <div style={{ flex: 1, background: "#0d3350", borderRadius: 20, height: 6, overflow: "hidden" }}>
            <div className="animate-fill-bar"
              style={{ height: 6, borderRadius: 20, background: verified ? "#4ade80" : "#fbbf24", width: `${confidence}%` }} />
          </div>
        </div>

        {/* Documents — structured extracted data */}
        <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Extracted Data</p>
        <div className="space-y-3 mb-5">
          {result.documents?.map((doc) => {
            const reduction = Math.round((1 - doc.compressed_size / doc.original_size) * 100);
            const fieldEntries = Object.entries(doc.fields || {});
            return (
              <div key={doc.doc_type} className="rounded-lg p-3" style={{ background: "#011e30", border: "1px solid #0d3350" }}>
                {/* Doc header */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--amber-flame)" }}>
                    {DOC_LABELS[doc.doc_type] || doc.doc_type.replace(/_/g, " ")}
                  </span>
                  <div className="flex items-center gap-2">
                    {doc.compressed_url && (
                      <a href={doc.compressed_url} target="_blank" rel="noreferrer"
                        className="text-xs border px-1.5 py-0.5 rounded transition-all hover:text-white"
                        style={{ color: "var(--blue-green)", borderColor: "#1a4a6a" }}>
                        img ↗
                      </a>
                    )}
                    <span className="text-xs" style={{ color: "#4a7a99" }}>
                      {(doc.original_size / 1024).toFixed(0)} KB
                      <span className="mx-1" style={{ color: "#2a5a77" }}>→</span>
                      {(doc.compressed_size / 1024).toFixed(0)} KB
                      <span className="ml-1 px-1.5 py-0.5 rounded-full text-xs" style={{ background: "#0a2e1a", color: "#4ade80" }}>
                        ↓{reduction}%
                      </span>
                    </span>
                  </div>
                </div>

                {/* Fields */}
                {fieldEntries.length > 0 ? (
                  <div className="space-y-1 pt-2 border-t" style={{ borderColor: "#0d3350" }}>
                    {fieldEntries.map(([k, v]) => (
                      <div key={k} className="flex items-start gap-2">
                        <span className="text-xs w-24 shrink-0" style={{ color: "#4a7a99" }}>
                          {FIELD_LABELS[k] || k}
                        </span>
                        <span className="text-xs flex-1 break-all font-medium" style={{ color: "#c8dae8" }}>{v.value}</span>
                        <span className="text-xs shrink-0" style={{ color: v.confidence >= 0.9 ? "#4ade80" : "#fbbf24" }}>
                          {Math.round(v.confidence * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs pt-2 border-t" style={{ borderColor: "#0d3350", color: "#2a5a77" }}>No fields extracted</p>
                )}
              </div>
            );
          })}
        </div>

        {/* Cross-validation */}
        {result.cross_validation?.length > 0 && (
          <>
            <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Cross-Validation</p>
            <div className="space-y-1.5 mb-5">
              {result.cross_validation.map((check) => (
                <div key={check.field} className="flex items-center gap-2 px-3 py-2 rounded-md"
                  style={{ background: "#011e30", border: "1px solid #0d3350" }}>
                  <span>{check.status === "MATCH" ? "✅" : check.status === "MISMATCH" ? "❌" : "⚠️"}</span>
                  <span className="flex-1 text-xs capitalize" style={{ color: "#7a9bb5" }}>
                    {check.field.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs font-semibold"
                    style={{ color: check.status === "MATCH" ? "#4ade80" : check.status === "MISMATCH" ? "#f87171" : "#fbbf24" }}>
                    {check.status}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Blockchain */}
        {result.blockchain && (
          <>
            <p className="text-xs uppercase tracking-widest mb-2" style={{ color: "#4a7a99" }}>Blockchain Receipt</p>
            <div className="rounded-lg p-3 mb-5" style={{ background: "#011e30", border: "1px solid #1a4a6a" }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="animate-pulse-glow"
                  style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--amber-flame)", display: "inline-block" }} />
                <span className="text-xs" style={{ color: "var(--amber-flame)" }}>
                  Polygon Amoy · Block #{result.blockchain.block_number?.toLocaleString()}
                </span>
              </div>
              <p className="text-xs font-mono mb-3" style={{ color: "#4a7a99", wordBreak: "break-all" }}>
                {result.blockchain.tx_hash}
              </p>
              <a href={result.blockchain.polygonscan_url} target="_blank" rel="noreferrer"
                className="inline-block text-xs px-3 py-1.5 rounded-md border transition-all hover:text-white"
                style={{ color: "var(--blue-green)", borderColor: "#1a4a6a" }}>
                ↗ View on Polygonscan
              </a>
            </div>
          </>
        )}

        {/* Raw JSON */}
        <div className="mb-5">
          <button
            onClick={() => setShowJson((v) => !v)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-md text-xs border transition-all"
            style={{ background: "#011e30", borderColor: "#0d3350", color: "#4a7a99" }}
          >
            <span>{"{ }"} Raw API Response</span>
            <span>{showJson ? "▲ hide" : "▼ show"}</span>
          </button>
          {showJson && (
            <pre className="mt-2 rounded-md p-3 text-xs overflow-auto max-h-64"
              style={{ background: "#010f1a", border: "1px solid #0d3350", color: "#4a7a99" }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2 border-t" style={{ borderColor: "#0d3350" }}>
          <button onClick={() => navigate("/")}
            className="flex-1 py-2.5 rounded-md text-sm border transition-all"
            style={{ borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
            ← Upload More
          </button>
          <Link to="/dashboard"
            className="btn-shimmer flex-1 py-2.5 rounded-md text-sm text-center font-semibold"
            style={{ background: "var(--princeton-orange)", color: "#fff" }}>
            Officer View →
          </Link>
        </div>

      </div>
    </div>
  );
}
