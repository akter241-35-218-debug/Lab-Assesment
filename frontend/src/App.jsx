import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import DailyDigest from "./pages/DailyDigest";
import MedicineRegister from "./pages/MedicineRegister";
import CompanyPolicies from "./pages/CompanyPolicies";
import ImportData from "./pages/ImportData";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<DailyDigest />} />
          <Route path="/medicines" element={<MedicineRegister />} />
          <Route path="/companies" element={<CompanyPolicies />} />
          <Route path="/import" element={<ImportData />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
