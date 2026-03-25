import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listPatients, resolveImageUrl } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Patients.css";

export default function Patients() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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
              <button className="button ghost" onClick={() => navigate(`/patients/${patient.id}`)}>
                View Details
              </button>
              <button className="button ghost" onClick={() => navigate(`/analysis?patient=${patient.id}`)}>
                Simulate Attack
              </button>
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
