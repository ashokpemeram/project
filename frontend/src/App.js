import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import AppShell from "./components/AppShell";
import AdminShell from "./components/AdminShell";
import Login from "./pages/Login";
import AdminLogin from "./pages/AdminLogin";
import Dashboard from "./pages/Dashboard";
import Patients from "./pages/Patients";
import PatientDetails from "./pages/PatientDetails";
import Analysis from "./pages/Analysis";
import Doctors from "./pages/Doctors";

function RequireAuth({ children, role }) {
  const { token, user } = useAuth();
  if (!token) {
    const redirect = role === "admin" ? "/admin/login" : "/login";
    return <Navigate to={redirect} replace />;
  }
  if (role && user?.role !== role) {
    const redirect = user?.role === "admin" ? "/admin" : "/dashboard";
    return <Navigate to={redirect} replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/signup" element={<Navigate to="/login" replace />} />
          <Route
            element={
              <RequireAuth role="doctor">
                <AppShell />
              </RequireAuth>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/patients" element={<Patients />} />
            <Route path="/patients/:patientId" element={<PatientDetails />} />
            <Route path="/analysis" element={<Analysis />} />
          </Route>

          <Route
            path="/admin"
            element={
              <RequireAuth role="admin">
                <AdminShell />
              </RequireAuth>
            }
          >
            <Route index element={<Navigate to="/admin/doctors" replace />} />
            <Route path="doctors" element={<Doctors />} />
            <Route path="patients" element={<Patients />} />
            <Route path="patients/:patientId" element={<PatientDetails />} />
            <Route path="analysis" element={<Analysis />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
