import React, { useEffect, useMemo, useState } from "react";
import { adminCreateDoctor, adminDeleteDoctor, adminListDoctors } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { validateAlphaName, validateEmail } from "../utils/validation";
import "./Doctors.css";

const initialForm = {
  name: "",
  email: "",
  password: "",
};

export default function Doctors() {
  const { token, user } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const sortedDoctors = useMemo(() => {
    const list = Array.isArray(doctors) ? doctors : [];
    return [...list].sort((a, b) => String(a?.name || "").localeCompare(String(b?.name || "")));
  }, [doctors]);

  const loadDoctors = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await adminListDoctors(token);
      setDoctors(data.doctors || []);
    } catch (err) {
      setError(err.message || "Failed to load doctors");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDoctors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const updateField = (field) => (event) => {
    const value = field === "email" ? event.target.value.replace(/\s/g, "") : event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: "" }));
    }
    if (error) setError("");
  };

  const handleCreate = async (event) => {
    event.preventDefault();
    setError("");

    const nextErrors = {};
    const nameError = validateAlphaName(form.name, "Doctor name");
    if (nameError) nextErrors.name = nameError;
    const emailError = validateEmail(form.email);
    if (emailError) nextErrors.email = emailError;
    if (!String(form.password ?? "").trim()) nextErrors.password = "Password is required.";
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSaving(true);
    try {
      await adminCreateDoctor(
        { name: form.name.trim(), email: form.email.trim(), password: form.password },
        token
      );
      setForm(initialForm);
      await loadDoctors();
    } catch (err) {
      setError(err.message || "Failed to create doctor");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (doctor) => {
    if (!doctor?.id) return;
    const label = doctor.email ? `${doctor.name} (${doctor.email})` : doctor.name || "this doctor";
    if (!window.confirm(`Delete ${label}?`)) return;

    setError("");
    try {
      await adminDeleteDoctor(doctor.id, token);
      setDoctors((prev) => (Array.isArray(prev) ? prev.filter((d) => d.id !== doctor.id) : []));
    } catch (err) {
      setError(err.message || "Failed to delete doctor");
    }
  };

  return (
    <div className="doctors-page grid">
      <div className="page-header">
        <div>
          <h2>Doctor Management</h2>
          <p>Create and remove doctor accounts. Admin: {user?.email}</p>
        </div>
      </div>

      <div className="grid doctors-layout">
        <div className="card fade-up">
          <h3>Create Doctor</h3>
          <p className="section-subtitle">Share credentials with the doctor after creation.</p>
          <form className="doctors-form" onSubmit={handleCreate} noValidate>
            <div className="form-grid">
              <label>
                Doctor name
                <input
                  value={form.name}
                  onChange={updateField("name")}
                  className={fieldErrors.name ? "input-error" : ""}
                  required
                />
                {fieldErrors.name && <div className="field-error">{fieldErrors.name}</div>}
              </label>
              <label>
                Doctor email
                <input
                  type="text"
                  inputMode="email"
                  autoComplete="email"
                  value={form.email}
                  onChange={updateField("email")}
                  className={fieldErrors.email ? "input-error" : ""}
                  required
                />
                {fieldErrors.email && <div className="field-error">{fieldErrors.email}</div>}
              </label>
              <label>
                Temporary password
                <input
                  type="password"
                  value={form.password}
                  onChange={updateField("password")}
                  className={fieldErrors.password ? "input-error" : ""}
                  required
                />
                {fieldErrors.password && <div className="field-error">{fieldErrors.password}</div>}
              </label>
            </div>
            {error && <div className="form-error">{error}</div>}
            <button className="button primary" type="submit" disabled={saving}>
              {saving ? "Creating..." : "Create Doctor"}
            </button>
          </form>
        </div>

        <div className="card fade-up">
          <h3>Doctors</h3>
          {loading && <div className="muted">Loading doctors...</div>}
          {!loading && !sortedDoctors.length && <div className="muted">No doctors found.</div>}
          {!loading && sortedDoctors.length > 0 && (
            <div className="doctors-list">
              {sortedDoctors.map((doctor) => (
                <div key={doctor.id} className="doctor-row">
                  <div>
                    <div className="doctor-name">{doctor.name || "Doctor"}</div>
                    <div className="doctor-email">{doctor.email}</div>
                  </div>
                  <button className="button ghost danger" onClick={() => handleDelete(doctor)}>
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
