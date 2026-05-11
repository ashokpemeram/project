// Loosely follows the HTML `type="email"` constraint validation pattern (dot after @ is optional).
const EMAIL_RE =
  /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
const ALPHA_NAME_RE = /^[A-Za-z ]+$/;
const PATIENT_ID_RE = /^PAT\d{3,}$/i;

export function validateEmail(email) {
  const value = String(email ?? "").trim();
  if (!value) return "Email is required.";
  if (!EMAIL_RE.test(value)) return "Enter a valid email address.";
  return "";
}

export function validateAlphaName(name, label = "Name") {
  const value = String(name ?? "").trim();
  if (!value) return `${label} is required.`;
  if (!ALPHA_NAME_RE.test(value)) return `${label} must contain only letters and spaces.`;
  const letterCount = value.replace(/ /g, "").length;
  if (letterCount < 3) return `${label} must be at least 3 letters.`;
  return "";
}

export function validatePatientId(patientId) {
  const value = String(patientId ?? "").trim();
  if (!value) return "Patient ID is required.";
  if (!PATIENT_ID_RE.test(value)) return "Patient ID must look like PAT001.";
  return "";
}
