import { Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import ResultPage from "./pages/ResultPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/result/:id" element={<ResultPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
    </Routes>
  );
}
