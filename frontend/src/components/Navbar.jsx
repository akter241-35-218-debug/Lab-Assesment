import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Today" },
  { to: "/medicines", label: "Medicines" },
  { to: "/companies", label: "Companies" },
  { to: "/import", label: "Import" },
  { to: "/dashboard", label: "Dashboard" },
];

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand">💊 Pharmacy Shelf</div>
        <nav>
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
