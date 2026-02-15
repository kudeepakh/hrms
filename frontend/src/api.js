import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

// ── Token helpers ──────────────────────────────────────
export function getToken() {
  return localStorage.getItem("hrms_token");
}

export function setToken(token) {
  localStorage.setItem("hrms_token", token);
}

export function clearToken() {
  localStorage.removeItem("hrms_token");
  localStorage.removeItem("hrms_user");
}

export function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("hrms_user"));
  } catch {
    return null;
  }
}

export function setStoredUser(user) {
  localStorage.setItem("hrms_user", JSON.stringify(user));
}

// ── Axios instance with auth header ────────────────────
const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) {
      clearToken();
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

// ── Auth API ───────────────────────────────────────────
export async function login(email, password) {
  const response = await api.post("/auth/login", { email, password });
  return response.data; // { access_token, token_type, user }
}

export async function register(name, email, password) {
  const response = await api.post("/auth/register", { name, email, password });
  return response.data; // { access_token, token_type, user }
}

// ── Chat API ───────────────────────────────────────────
export async function sendMessage(message, sessionId = "default") {
  const response = await api.post("/chat", {
    message,
    session_id: sessionId,
  });
  return response.data;
}

// ── Employee API ───────────────────────────────────────
export async function getEmployees() {
  const response = await api.get("/employees");
  return response.data;
}

// ── Health API ─────────────────────────────────────────
export async function checkHealth() {
  const response = await api.get("/health");
  return response.data;
}

// ── Salary Preview API ─────────────────────────────────
export async function salaryPreview(annualCtc) {
  const response = await api.post("/employees/salary-preview", {
    annual_ctc: annualCtc,
  });
  return response.data;
}
