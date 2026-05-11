const PATIENT_ID_RE = /^PAT(\d+)$/i;

export function parsePatientIdNumber(patientId) {
  const raw = String(patientId ?? "").trim();
  const match = raw.match(PATIENT_ID_RE);
  if (!match) return null;
  const value = Number.parseInt(match[1], 10);
  return Number.isFinite(value) ? value : null;
}

export function formatPatientId(number) {
  const value = Number(number);
  if (!Number.isFinite(value) || value <= 0) return "PAT001";
  return `PAT${String(Math.trunc(value)).padStart(3, "0")}`;
}

export function suggestNextPatientId(patients) {
  const list = Array.isArray(patients) ? patients : [];
  let maxPat = 0;

  for (const patient of list) {
    const value = parsePatientIdNumber(patient?.patient_id);
    if (value && value > maxPat) {
      maxPat = value;
    }
  }

  const next = maxPat > 0 ? maxPat + 1 : list.length + 1;
  return formatPatientId(next);
}
