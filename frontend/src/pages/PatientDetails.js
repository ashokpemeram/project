import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getPatient, resolveImageUrl } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./PatientDetails.css";

export default function PatientDetails() {
  const { patientId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [attacks, setAttacks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadPatient = async () => {
      try {
        const data = await getPatient(patientId, token);
        setPatient(data.patient);
        setAttacks(data.attacks || []);
      } catch (err) {
        setError(err.message || "Failed to load patient");
      }
    };
    loadPatient();
  }, [patientId, token]);

  if (error) {
    return <div className="card form-error">{error}</div>;
  }

  if (!patient) {
    return <div className="card">Loading patient details...</div>;
  }

  const metrics = patient.protection_metrics || {};

  return (
    <div className="patient-detail grid">
      <div className="card detail-header">
        <div>
          <h2>{patient.patient_name}</h2>
          <p>Patient ID: {patient.patient_id}</p>
          <p>Scan type: {patient.scan_type}</p>
        </div>
        <span className={`tag ${patient.status === "Attacked" ? "attacked" : "protected"}`}>
          {patient.status || "Protected"}
        </span>
      </div>

      <div className="detail-grid">
        <div className="card">
          <h3>Protected Image</h3>
          <img src={resolveImageUrl(patient.protected_url)} alt="Protected" />
          <div className="detail-actions">
            <a className="button primary" href={resolveImageUrl(patient.protected_url)} download>
              Download Protected
            </a>
            <button className="button ghost" onClick={() => navigate(`/analysis?patient=${patient.id}`)}>
              View Analysis
            </button>
          </div>
        </div>
        <div className="card">
          <h3>Protection Metrics</h3>
          <div className="metric-list">
            <div>
              <span>MSE</span>
              <strong>{metrics.mse_protected_vs_original?.toFixed(4)}</strong>
            </div>
            <div>
              <span>PSNR</span>
              <strong>{metrics.psnr_protected_vs_original?.toFixed(2)}</strong>
            </div>
            <div>
              <span>SSIM</span>
              <strong>{metrics.ssim_protected_vs_original?.toFixed(3)}</strong>
            </div>
          </div>
          <div className="integrity-note">
            Integrity note: original scans are not stored after protection.
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Attack History</h3>
        {attacks.length === 0 ? (
          <p>No attacks recorded yet.</p>
        ) : (
          <div className="attack-table">
            {attacks.map((attack) => (
              <div key={attack.id} className="attack-row">
                <div>
                  <strong>{attack.attack_type}</strong>
                  <p>{attack.created_at?.slice(0, 19)}</p>
                </div>
                <div>
                  <span>MSE</span>
                  <strong>{attack.metrics?.mse_attacked_vs_protected?.toFixed(4)}</strong>
                </div>
                <div>
                  <span>PSNR</span>
                  <strong>{attack.metrics?.psnr_attacked_vs_protected?.toFixed(2)}</strong>
                </div>
                <div>
                  <span>SSIM</span>
                  <strong>{attack.metrics?.ssim_attacked_vs_protected?.toFixed(3)}</strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
