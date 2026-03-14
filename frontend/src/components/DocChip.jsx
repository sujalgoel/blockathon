export default function DocChip({ label, delay = 0 }) {
  return (
    <div
      className="animate-chip-pop flex items-center gap-2 px-3 py-1 rounded-full border text-xs"
      style={{
        animationDelay: `${delay}ms`,
        background: "#0d3350",
        borderColor: "#1a4a6a",
        color: "var(--sky-blue-light)",
      }}
    >
      <span style={{
        width: 6,
        height: 6,
        borderRadius: "50%",
        background: "var(--amber-flame)",
        display: "inline-block",
        flexShrink: 0,
      }} />
      {label}
    </div>
  );
}
