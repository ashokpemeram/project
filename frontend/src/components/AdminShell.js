import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./AppShell.css";

const navClass = ({ isActive }) => `nav-link${isActive ? " active" : ""}`;

export default function AdminShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/admin/login");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">HIS</div>
          <div>
            <div className="brand-title">Hospital Imaging</div>
            <div className="brand-subtitle">Admin Console</div>
          </div>
        </div>
        <nav className="nav">
          <NavLink to="/admin/doctors" className={navClass}>
            Doctors
          </NavLink>
          <NavLink to="/admin/patients" className={navClass}>
            Patients
          </NavLink>
          <NavLink to="/admin/analysis" className={navClass}>
            Tamper Simulation
          </NavLink>
        </nav>
        <div className="sidebar-note">
          Admin access: create doctors, review patient records, and audit tamper simulations.
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <div className="topbar-title">Admin Console</div>
            <div className="topbar-subtitle">Secure Hospital Imaging System</div>
          </div>
          <div className="topbar-actions">
            <div className="user-badge">
              <div className="user-name">{user?.name || "Admin"}</div>
              <div className="user-role">{user?.role || "admin"}</div>
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

