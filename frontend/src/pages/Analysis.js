import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listPatients, resolveImageUrl, runAttack } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Analysis.css";

export default function Analysis() {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();
  const [patients, setPatients] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [attackType, setAttackType] = useState("combined");
  const [threshold, setThreshold] = useState(0.25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    const loadPatients = async () => {
      try {
        const data = await listPatients(token);
        const list = data.patients || [];
        setPatients(list);
        const paramId = searchParams.get("patient");
        if (paramId) {
          setSelectedId(paramId);
        } else if (list.length) {
          setSelectedId(list[0].id);
        }
      } catch (err) {
        setError(err.message || "Failed to load patients");
      }
    };
    loadPatients();
  }, [token, searchParams]);

  const selectedPatient = useMemo(
    () => patients.find((patient) => patient.id === selectedId),
    [patients, selectedId]
  );

  useEffect(() => {
    setResult(null);
  }, [selectedId]);

  const handleSimulate = async () => {
    if (!selectedId) {
      setError("Please select a protected image.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await runAttack(
        {
          patient_id: selectedId,
          attack_type: attackType,
          tamper_threshold: Number(threshold),
        },
        token
      );
      setResult(data);
    } catch (err) {
      setError(err.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-page grid">
      <div className="card fade-up">
        <h2>Tamper Simulation and Analysis</h2>
        <p>Select a protected image and apply simulated attacks.</p>
        <div className="analysis-controls">
          <label>
            Protected image
            <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.patient_name} ({patient.patient_id})
                </option>
              ))}
            </select>
          </label>
          <label>
            Attack type
            <select value={attackType} onChange={(e) => setAttackType(e.target.value)}>
              <option value="combined">Combined</option>
              <option value="noise">Noise</option>
              <option value="patch">Patch</option>
              <option value="cutout">Cutout</option>
            </select>
          </label>
          <label>
            Tamper threshold
            <input
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          </label>
          <button className="button primary" onClick={handleSimulate} disabled={loading}>
            {loading ? "Simulating..." : "Simulate Attack"}
          </button>
        </div>
        {error && <div className="form-error">{error}</div>}
      </div>

      {selectedPatient && (
        <div className="card fade-up">
          <h3>Protected Image Preview</h3>
          <img
            className="preview-image"
            src={resolveImageUrl(selectedPatient.protected_url)}
            alt="Protected preview"
          />
        </div>
      )}

      {result && (
        <div className="grid analysis-results">
          <div className="card">
            <h3>Protected Image</h3>
            <img src={resolveImageUrl(result.protected_image_url)} alt="Protected" />
          </div>
          <div className="card">
            <h3>Attacked Image</h3>
            <img src={result.attacked_image} alt="Attacked" />
          </div>
          <div className="card">
            <h3>Difference Map</h3>
            <img src={result.tamper_map} alt="Tamper map" />
          </div>
          <div className="card">
            <h3>Tamper Mask</h3>
            <img src={result.tamper_mask} alt="Tamper mask" />
          </div>
          <div className="card">
            <h3>Attack Metrics</h3>
            <div className="metric-list">
              <div>
                <span>MSE</span>
                <strong>{result.metrics?.mse_attacked_vs_protected?.toFixed(4)}</strong>
              </div>
              <div>
                <span>PSNR</span>
                <strong>{result.metrics?.psnr_attacked_vs_protected?.toFixed(2)}</strong>
              </div>
              <div>
                <span>SSIM</span>
                <strong>{result.metrics?.ssim_attacked_vs_protected?.toFixed(3)}</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
