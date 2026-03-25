const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function resolveImageUrl(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

export async function signup(payload) {
  const response = await fetch(`${API_BASE}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Signup failed");
  }
  return data;
}

export async function login(payload) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Login failed");
  }
  return data;
}

export async function uploadPatient(formData, token) {
  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    headers: { ...authHeaders(token) },
    body: formData,
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Upload failed");
  }
  return data;
}

export async function listPatients(token) {
  const response = await fetch(`${API_BASE}/api/patients`, {
    headers: { ...authHeaders(token) },
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Failed to load patients");
  }
  return data;
}

export async function getPatient(patientId, token) {
  const response = await fetch(`${API_BASE}/api/patients/${patientId}`, {
    headers: { ...authHeaders(token) },
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Failed to load patient");
  }
  return data;
}

export async function runAttack(payload, token) {
  const response = await fetch(`${API_BASE}/api/attack`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(payload),
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Attack simulation failed");
  }
  return data;
}
