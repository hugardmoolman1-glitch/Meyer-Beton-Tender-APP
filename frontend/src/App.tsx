import { NavLink, Route, Routes } from "react-router-dom";
import PriceHistoryPage from "./pages/PriceHistoryPage";
import SuppliersPage from "./pages/SuppliersPage";
import TenderDetailPage from "./pages/TenderDetailPage";
import TendersPage from "./pages/TendersPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">Meyer Beton &mdash; Tender Desk</div>
        <nav>
          <NavLink to="/" end>
            Tenders
          </NavLink>
          <NavLink to="/suppliers">Suppliers</NavLink>
          <NavLink to="/prices">Price History</NavLink>
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<TendersPage />} />
          <Route path="/tenders/:id" element={<TenderDetailPage />} />
          <Route path="/suppliers" element={<SuppliersPage />} />
          <Route path="/prices" element={<PriceHistoryPage />} />
        </Routes>
      </main>
    </div>
  );
}
