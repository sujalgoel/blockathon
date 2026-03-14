import { useState, useEffect } from "react";
import { listVerifications, getVerification } from "../api";
import VerificationCard from "../components/VerificationCard";

export default function DashboardPage() {
  const [verifications, setVerifications] = useState([]);
  const [details, setDetails] = useState({});
  const [loadingDetails, setLoadingDetails] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listVerifications()
      .then(setVerifications)
      .catch(() => setError("Failed to load verifications. Check officer key."))
      .finally(() => setLoading(false));
  }, []);

  const handleCardOpen = async (applicantId) => {
    if (details[applicantId]) return;
    setLoadingDetails((prev) => ({ ...prev, [applicantId]: true }));
    try {
      const detail = await getVerification(applicantId);
      setDetails((prev) => ({ ...prev, [applicantId]: detail }));
    } catch {
      // fail silently — card still shows summary
    } finally {
      setLoadingDetails((prev) => ({ ...prev, [applicantId]: false }));
    }
  };

  const verified = verifications.filter((v) => v.is_verified && v.overall_confidence >= 75).length;
  const flagged = verifications.filter((v) => v.overall_confidence < 55).length;
  const pending = verifications.length - verified - flagged;

  const stats = [
    { label: "Pending", value: pending, color: "var(--princeton-orange)" },
    { label: "Verified", value: verified, color: "#22c55e" },
    { label: "Flagged", value: flagged, color: "#f87171" },
  ];

  return (
    <div className="min-h-screen p-6 max-w-2xl mx-auto">
      {/* Nav */}
      <div className="animate-fade-slide flex items-center justify-between mb-6 pb-4 border-b" style={{ borderColor: "#0d3350" }}>
        <span className="font-bold text-white">
          Doc<span style={{ color: "var(--amber-flame)" }}>Verify</span>
        </span>
        <span className="text-xs px-2 py-1 rounded-full border" style={{ background: "#0d3350", borderColor: "#1a4a6a", color: "var(--sky-blue-light)" }}>
          Officer View
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {stats.map(({ label, value, color }, i) => (
          <div
            key={label}
            className="animate-fade-slide rounded-lg p-3 transition-all"
            style={{ animationDelay: `${i * 80}ms`, background: "#011e30", border: "1px solid #0d3350" }}
          >
            <div className="text-xl font-bold" style={{ color }}>{value}</div>
            <div className="text-xs uppercase tracking-wider mt-0.5" style={{ color: "#4a7a99" }}>{label}</div>
          </div>
        ))}
      </div>

      <p className="text-xs uppercase tracking-widest mb-3" style={{ color: "#4a7a99" }}>Recent Applications</p>

      {loading && <p className="text-sm" style={{ color: "#4a7a99" }}>Loading...</p>}
      {error && <p className="text-sm" style={{ color: "#f87171" }}>{error}</p>}

      {verifications.map((v) => (
        <VerificationCard
          key={v.applicant_id}
          verification={v}
          detail={details[v.applicant_id]}
          loadingDetail={!!loadingDetails[v.applicant_id]}
          onOpen={handleCardOpen}
        />
      ))}

      {!loading && verifications.length === 0 && !error && (
        <p className="text-sm text-center mt-8" style={{ color: "#4a7a99" }}>No verifications yet. Submit documents to get started.</p>
      )}
    </div>
  );
}
