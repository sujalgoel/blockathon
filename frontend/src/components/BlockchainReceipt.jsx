export default function BlockchainReceipt({ blockchain }) {
  if (!blockchain) return null;

  return (
    <div
      className="rounded-lg p-3 mt-2 transition-all"
      style={{ background: "#011e30", border: "1px solid #1a4a6a" }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className="animate-pulse-glow"
          style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--amber-flame)", display: "inline-block" }}
        />
        <span className="text-xs uppercase tracking-widest" style={{ color: "var(--amber-flame)" }}>
          Polygon Blockchain Receipt
        </span>
      </div>
      <div className="space-y-1">
        {[
          ["TX Hash", blockchain.tx_hash],
          ["Block", blockchain.block_number?.toLocaleString()],
          ["Network", "Polygon Amoy"],
          ["Contract", blockchain.contract_address?.slice(0, 10) + "..."],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs">
            <span style={{ color: "#4a7a99" }}>{k}</span>
            <span className="font-mono" style={{ color: "var(--sky-blue-light)", fontSize: "0.62rem" }}>{v}</span>
          </div>
        ))}
      </div>
      {blockchain.polygonscan_url && (
        <a
          href={blockchain.polygonscan_url}
          target="_blank"
          rel="noreferrer"
          className="inline-block mt-2 text-xs px-2 py-1 rounded border transition-all hover:text-white"
          style={{ color: "var(--blue-green)", borderColor: "#1a4a6a" }}
        >
          ↗ View on Polygonscan
        </a>
      )}
    </div>
  );
}
