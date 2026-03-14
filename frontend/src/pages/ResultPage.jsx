import { useLocation, useNavigate, Link } from "react-router-dom";
import BlockchainReceipt from "../components/BlockchainReceipt";

export default function ResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const result = state?.result;

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p style={{ color: "#4a7a99" }}>No result data. </p>
          <button onClick={() => navigate("/")} style={{ color: "var(--blue-green)" }}>Go back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 max-w-lg mx-auto">
      <div className="animate-fade-slide rounded-xl p-6 border" style={{ background: "var(--deep-space-blue)", borderColor: "#0d3350" }}>
        <div className="flex items-center justify-between mb-4">
          <span className="font-bold text-white">
            Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
          </span>
          <span className="text-xs px-2 py-1 rounded-full font-semibold"
            style={{
              background: result.is_verified ? "#14532d" : "#450a0a",
              color: result.is_verified ? "#4ade80" : "#f87171"
            }}>
            {result.is_verified ? "✓ VERIFIED" : "⚠ REVIEW REQUIRED"}
          </span>
        </div>

        <p className="text-xs mb-1" style={{ color: "#4a7a99" }}>Application ID</p>
        <p className="font-medium mb-4">{result.applicant_id}</p>

        <p className="text-xs mb-1" style={{ color: "#4a7a99" }}>Overall Confidence</p>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg font-bold" style={{ color: "var(--blue-green)" }}>{result.overall_confidence}%</span>
          <div style={{ flex: 1, background: "#0d3350", borderRadius: 20, height: 6, overflow: "hidden" }}>
            <div className="animate-fill-bar" style={{ height: 6, borderRadius: 20, background: "var(--blue-green)", width: `${result.overall_confidence}%` }} />
          </div>
        </div>

        <p className="text-xs uppercase tracking-wider mb-2" style={{ color: "#4a7a99" }}>Documents Processed</p>
        {result.documents?.map((doc) => (
          <div key={doc.doc_type} className="rounded-lg p-3 mb-2" style={{ background: "#011e30", border: "1px solid #0d3350" }}>
            <p className="text-xs font-medium mb-1" style={{ color: "var(--blue-green)" }}>
              {doc.doc_type.replace(/_/g, " ").toUpperCase()}
            </p>
            <p className="text-xs" style={{ color: "var(--amber-flame)" }}>
              {(doc.original_size / 1024).toFixed(0)} KB → {(doc.compressed_size / 1024).toFixed(0)} KB
              ({Math.round((1 - doc.compressed_size / doc.original_size) * 100)}% reduction)
            </p>
          </div>
        ))}

        <BlockchainReceipt blockchain={result.blockchain} />

        <div className="flex gap-3 mt-4">
          <button onClick={() => navigate("/")} className="flex-1 py-2 rounded-md text-sm border transition-all"
            style={{ borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
            Upload More
          </button>
          <Link to="/dashboard" className="flex-1 py-2 rounded-md text-sm text-center font-semibold"
            style={{ background: "var(--princeton-orange)", color: "#fff" }}>
            Officer View →
          </Link>
        </div>
      </div>
    </div>
  );
}
