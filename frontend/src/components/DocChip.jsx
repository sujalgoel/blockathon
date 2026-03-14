export default function DocChip({ label, ready, delay = 0 }) {
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
      <span
        className={ready ? "animate-blink" : ""}
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: ready ? "#22c55e" : "var(--amber-flame)",
          display: "inline-block",
        }}
      />
      {label}
    </div>
  );
}
