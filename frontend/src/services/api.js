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

function extractApiErrorMessage(payload) {
  if (!payload) return "";
  if (typeof payload === "string") return payload.trim();
  if (typeof payload !== "object") return "";

  if (typeof payload.detail === "string") return payload.detail.trim();
  if (typeof payload.error === "string") return payload.error.trim();

  if (Array.isArray(payload.detail)) {
    const messages = payload.detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : ""))
      .filter(Boolean);
    if (messages.length) return messages.join(", ");
  }

  return "";
}

function buildNetworkErrorMessage(url) {
  let origin = "";
  try {
    origin = window?.location?.origin || "";
  } catch {
    origin = "";
  }

  const hints = [
    `Could not reach the server at ${url}.`,
    origin ? `Frontend origin: ${origin}.` : "",
    `Check that the backend is running and that CORS allows this origin.`,
  ].filter(Boolean);

  return hints.join(" ");
}

async function requestJson(url, options, fallbackErrorMessage) {
  try {
    const response = await fetch(url, options);
    const data = await parseResponse(response);
    if (!response.ok) {
      const message = extractApiErrorMessage(data) || fallbackErrorMessage;
      throw new Error(message);
    }
    return data;
  } catch (err) {
    const msg = String(err?.message || "");
    if (
      err instanceof TypeError ||
      msg.toLowerCase().includes("failed to fetch") ||
      msg.toLowerCase().includes("networkerror")
    ) {
      throw new Error(buildNetworkErrorMessage(url));
    }
    throw err;
  }
}

export function resolveImageUrl(path) {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

export async function signup(payload) {
  return requestJson(
    `${API_BASE}/api/auth/signup`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Signup failed"
  );
}

export async function login(payload) {
  return requestJson(
    `${API_BASE}/api/auth/login`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "Login failed"
  );
}

export async function uploadPatient(formData, token) {
  return requestJson(
    `${API_BASE}/api/upload`,
    {
      method: "POST",
      headers: { ...authHeaders(token) },
      body: formData,
    },
    "Upload failed"
  );
}

export async function listPatients(token) {
  return requestJson(
    `${API_BASE}/api/patients`,
    {
      headers: { ...authHeaders(token) },
    },
    "Failed to load patients"
  );
}

export async function getPatient(patientId, token) {
  return requestJson(
    `${API_BASE}/api/patients/${patientId}`,
    {
      headers: { ...authHeaders(token) },
    },
    "Failed to load patient"
  );
}

export async function runAttack(payload, token) {
  return requestJson(
    `${API_BASE}/api/attack`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body: JSON.stringify(payload),
    },
    "Attack simulation failed"
  );
}

export async function adminListDoctors(token) {
  return requestJson(
    `${API_BASE}/api/admin/doctors`,
    {
      headers: { ...authHeaders(token) },
    },
    "Failed to load doctors"
  );
}

export async function adminCreateDoctor(payload, token) {
  return requestJson(
    `${API_BASE}/api/admin/doctors`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body: JSON.stringify(payload),
    },
    "Failed to create doctor"
  );
}

export async function adminDeleteDoctor(doctorId, token) {
  return requestJson(
    `${API_BASE}/api/admin/doctors/${doctorId}`,
    {
      method: "DELETE",
      headers: { ...authHeaders(token) },
    },
    "Failed to delete doctor"
  );
}

export async function adminDeletePatient(patientId, token) {
  return requestJson(
    `${API_BASE}/api/admin/patients/${patientId}`,
    {
      method: "DELETE",
      headers: { ...authHeaders(token) },
    },
    "Failed to delete patient"
  );
}

/* Legacy implementation (kept until next cleanup)
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

export async function adminListDoctors(token) {
  const response = await fetch(`${API_BASE}/api/admin/doctors`, {
    headers: { ...authHeaders(token) },
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Failed to load doctors");
  }
  return data;
}

export async function adminCreateDoctor(payload, token) {
  const response = await fetch(`${API_BASE}/api/admin/doctors`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(payload),
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Failed to create doctor");
  }
  return data;
}

export async function adminDeleteDoctor(doctorId, token) {
  const response = await fetch(`${API_BASE}/api/admin/doctors/${doctorId}`, {
    method: "DELETE",
    headers: { ...authHeaders(token) },
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Failed to delete doctor");
  }
  return data;
}

export async function adminDeletePatient(patientId, token) {
  const response = await fetch(`${API_BASE}/api/admin/patients/${patientId}`, {
    method: "DELETE",
    headers: { ...authHeaders(token) },
  });
  const data = await parseResponse(response);
  if (!response.ok) {
    throw new Error(data.detail || data.error || "Failed to delete patient");
  }
  return data;
}
*/
