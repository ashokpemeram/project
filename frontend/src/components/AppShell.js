import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./AppShell.css";

const navClass = ({ isActive }) => `nav-link${isActive ? " active" : ""}`;

export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">HIS</div>
          <div>
            <div className="brand-title">Hospital Imaging</div>
            <div className="brand-subtitle">Secure Scan Vault</div>
          </div>
        </div>
        <nav className="nav">
          <NavLink to="/dashboard" className={navClass}>
            Dashboard
          </NavLink>
          <NavLink to="/patients" className={navClass}>
            Patient Records
          </NavLink>
          <NavLink to="/analysis" className={navClass}>
            Tamper Simulation
          </NavLink>
        </nav>
        <div className="sidebar-note">
          Original scans are never stored. Only protected images persist.
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <div className="topbar-title">Doctor Console</div>
            <div className="topbar-subtitle">Secure Hospital Imaging System</div>
          </div>
          <div className="topbar-actions">
            <div className="user-badge">
              <div className="user-name">{user?.name || "Doctor"}</div>
              <div className="user-role">{user?.role || "doctor"}</div>
            </div>
            <button className="button ghost" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
