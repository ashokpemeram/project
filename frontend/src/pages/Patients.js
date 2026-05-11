import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminDeletePatient, listPatients, resolveImageUrl } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Patients.css";

export default function Patients() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const basePath = user?.role === "admin" ? "/admin" : "";
  const [deletingId, setDeletingId] = useState("");

  useEffect(() => {
    const loadPatients = async () => {
      setLoading(true);
      try {
        const data = await listPatients(token);
        setPatients(data.patients || []);
      } catch (err) {
        setError(err.message || "Failed to load patients");
      } finally {
        setLoading(false);
      }
    };
    loadPatients();
  }, [token]);

  const handleDelete = async (patient) => {
    if (user?.role !== "admin") return;
    if (!patient?.id) return;
    const label = patient.patient_id ? `${patient.patient_name} (${patient.patient_id})` : patient.patient_name;
    if (!window.confirm(`Delete patient record ${label}?`)) return;

    setDeletingId(patient.id);
    setError("");
    try {
      await adminDeletePatient(patient.id, token);
      setPatients((prev) => (Array.isArray(prev) ? prev.filter((p) => p.id !== patient.id) : []));
    } catch (err) {
      setError(err.message || "Failed to delete patient");
    } finally {
      setDeletingId("");
    }
  };

  return (
    <div className="patients-page grid">
      <div className="page-header">
        <div>
          <h2>Patient Records</h2>
          <p>Review protected scans and launch tamper analysis.</p>
        </div>
      </div>

      {loading && <div className="card">Loading patient records...</div>}
      {error && <div className="card form-error">{error}</div>}

      {!loading && !patients.length && (
        <div className="card">No patient records yet. Upload a scan to get started.</div>
      )}

      <div className="patients-grid">
        {patients.map((patient) => (
          <div key={patient.id} className="card patient-card fade-up">
            <div className="patient-card-header">
              <div>
                <h3>{patient.patient_name}</h3>
                <p>Patient ID: {patient.patient_id}</p>
              </div>
              <span className={`tag ${patient.status === "Attacked" ? "attacked" : "protected"}`}>
                {patient.status || "Protected"}
              </span>
            </div>
            <div className="patient-card-body">
              <img src={resolveImageUrl(patient.protected_url)} alt="Protected" />
              <div>
                <p>Scan type: {patient.scan_type}</p>
                <p>Created: {patient.created_at?.slice(0, 10)}</p>
                <p className="notes">{patient.diagnosis_notes || "No diagnosis notes"}</p>
              </div>
            </div>
            <div className="patient-actions">
              <button className="button ghost" onClick={() => navigate(`${basePath}/patients/${patient.id}`)}>
                View Details
              </button>
              <button className="button ghost" onClick={() => navigate(`${basePath}/analysis?patient=${patient.id}`)}>
                Simulate Attack
              </button>
              {user?.role === "admin" && (
                <button
                  className="button ghost danger"
                  onClick={() => handleDelete(patient)}
                  disabled={deletingId === patient.id}
                >
                  {deletingId === patient.id ? "Deleting..." : "Delete"}
                </button>
              )}
              <a className="button primary" href={resolveImageUrl(patient.protected_url)} download>
                Download Protected
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
