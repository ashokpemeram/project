import React, { useEffect, useState } from "react";
import { listPatients, resolveImageUrl, uploadPatient } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { suggestNextPatientId, formatPatientId, parsePatientIdNumber } from "../utils/patientId";
import { validateAlphaName, validatePatientId } from "../utils/validation";
import "./Dashboard.css";

const initialForm = {
  patientName: "",
  patientId: "",
  scanType: "CT",
  diagnosisNotes: "",
};

export default function Dashboard() {
  const { token } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [latest, setLatest] = useState(null);
  const [patientCount, setPatientCount] = useState(0);
  const [patientIdMax, setPatientIdMax] = useState(0);
  const [suggestedPatientId, setSuggestedPatientId] = useState("PAT001");

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await listPatients(token);
        const patients = data.patients || [];
        setPatientCount(patients.length || 0);

        let max = 0;
        for (const patient of patients) {
          const value = parsePatientIdNumber(patient?.patient_id);
          if (value && value > max) max = value;
        }
        setPatientIdMax(max);

        const suggested = suggestNextPatientId(patients);
        setSuggestedPatientId(suggested);
        setForm((prev) => {
          if (String(prev.patientId ?? "").trim()) return prev;
          return { ...prev, patientId: suggested };
        });
      } catch {
        setPatientCount(0);
        setPatientIdMax(0);
        setSuggestedPatientId("PAT001");
      }
    };
    loadStats();
  }, [token]);

  const updateField = (field) => (event) => {
    const value = event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((prev) => ({ ...prev, [field]: "" }));
    }
    if (error) setError("");
  };

  const handleFileChange = (event) => {
    setFile(event.target.files?.[0] || null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    const nextErrors = {};
    const nameError = validateAlphaName(form.patientName, "Patient name");
    if (nameError) nextErrors.patientName = nameError;
    const patientIdError = validatePatientId(form.patientId);
    if (patientIdError) nextErrors.patientId = patientIdError;
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length) {
      return;
    }

    if (!file) {
      setError("Please select a scan image.");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("patient_name", form.patientName.trim());
      formData.append("patient_id", form.patientId.trim().toUpperCase());
      formData.append("scan_type", form.scanType);
      formData.append("diagnosis_notes", form.diagnosisNotes);

      const data = await uploadPatient(formData, token);
      setLatest(data.patient);
      setFieldErrors({});

      const used = parsePatientIdNumber(form.patientId);
      const nextMax = used ? Math.max(patientIdMax, used) : patientIdMax;
      setPatientIdMax(nextMax);
      const nextSuggested = formatPatientId(nextMax + 1);
      setSuggestedPatientId(nextSuggested);

      setForm({ ...initialForm, patientId: nextSuggested });
      setFile(null);
      setPatientCount((count) => count + 1);
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard grid">
      <section className="hero card fade-up">
        <div>
          <h2>Secure Imaging Dashboard</h2>
          <p>
            Upload patient scans, generate protected images, and track tamper analysis in one
            workflow.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <div className="stat-value">{patientCount}</div>
            <div className="stat-label">Protected records</div>
          </div>
          <div>
            <div className="stat-value">100%</div>
            <div className="stat-label">Original-free storage</div>
          </div>
        </div>
      </section>

      <section className="grid dashboard-main">
        <div className="card fade-up">
          <h3>Upload Patient Scan</h3>
          <p className="section-subtitle">Provide patient metadata and the scan to secure.</p>
          <form className="upload-form" onSubmit={handleSubmit}>
            <div className="form-grid">
              <label>
                Patient name
                <input
                  value={form.patientName}
                  onChange={updateField("patientName")}
                  className={fieldErrors.patientName ? "input-error" : ""}
                  required
                />
                {fieldErrors.patientName && (
                  <div className="field-error">{fieldErrors.patientName}</div>
                )}
              </label>
              <label>
                Patient ID
                <input
                  value={form.patientId}
                  onChange={updateField("patientId")}
                  className={fieldErrors.patientId ? "input-error" : ""}
                  required
                />
                <div className="field-hint">Suggested: {suggestedPatientId}</div>
                {fieldErrors.patientId && <div className="field-error">{fieldErrors.patientId}</div>}
              </label>
              <label>
                Scan type
                <select value={form.scanType} onChange={updateField("scanType")}>
                  <option value="CT">CT Scan</option>
                  <option value="X-ray">X-ray</option>
                  <option value="MRI">MRI</option>
                  <option value="Ultrasound">Ultrasound</option>
                </select>
              </label>
              <label>
                Diagnosis notes
                <input value={form.diagnosisNotes} onChange={updateField("diagnosisNotes")} />
              </label>
            </div>
            <label className="file-field">
              Scan image
              <input type="file" accept="image/*" onChange={handleFileChange} />
            </label>
            {error && <div className="form-error">{error}</div>}
            <button className="button primary" type="submit" disabled={loading}>
              {loading ? "Protecting..." : "Protect and Store"}
            </button>
          </form>
          <div className="integrity-note">
            Integrity note: Original images are processed in memory only and never stored. This system ensures integrity of medical images against AI-based tampering attacks.
          </div>
        </div>

        <div className="grid">
          <div className="card soft fade-up">
            <h3>Demo Flow</h3>
            <ol className="demo-steps">
              <li>Doctor logs in</li>
              <li>Upload patient scan</li>
              <li>System generates protected image</li>
              <li>Open patient record</li>
              <li>Run tamper simulation</li>
              <li>Review metrics and masks</li>
            </ol>
          </div>

          {latest && (
            <div className="card fade-up">
              <h3>Latest Protected Record</h3>
              <div className="latest-grid">
                <img src={resolveImageUrl(latest.protected_url)} alt="Protected" />
                <div>
                  <div className="tag protected">Protected</div>
                  <h4>{latest.patient_name}</h4>
                  <p>Patient ID: {latest.patient_id}</p>
                  <p>Scan type: {latest.scan_type}</p>
                  <div className="metrics">
                    <div>
                      <span>MSE</span>
                      <strong>{latest.protection_metrics?.mse_protected_vs_original?.toFixed(4)}</strong>
                    </div>
                    <div>
                      <span>PSNR</span>
                      <strong>{latest.protection_metrics?.psnr_protected_vs_original?.toFixed(2)}</strong>
                    </div>
                    <div>
                      <span>SSIM</span>
                      <strong>{latest.protection_metrics?.ssim_protected_vs_original?.toFixed(3)}</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
