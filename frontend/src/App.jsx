import { Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import ResultPage from "./pages/ResultPage";

function Footer() {
  return (
    <div className="text-center py-4 border-t" style={{ borderColor: "#0d3350", background: "#0b1a26" }}>
      <p className="text-xs" style={{ color: "#2a5a77" }}>
        <span style={{ color: "#4a7a99" }}>Sujal Goel</span>
        <span className="mx-2" style={{ color: "#1a3a50" }}>·</span>
        <span style={{ color: "#4a7a99" }}>Team CORE</span>
        <span className="mx-2" style={{ color: "#1a3a50" }}>·</span>
        <span>cogni2053350</span>
        <span className="mx-2" style={{ color: "#1a3a50" }}>·</span>
        <span>IIT Roorkee Blockathon 2026</span>
      </p>
    </div>
  );
}

export default function App() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "#0b1a26" }}>
      <div style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/result/:id" element={<ResultPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </div>
      <Footer />
    </div>
  );
}
