import axios from "axios";

const TOKEN_KEY = "sentiment_token";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 45000,
});

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let onUnauthorized = null;
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401 && onUnauthorized) {
      onUnauthorized();
    }
    return Promise.reject(error);
  }
);

// Turn an axios error into a friendly, user-safe message.
export function apiError(error) {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || "Invalid value").join(", ");
  }
  if (typeof detail === "string") return detail;
  if (error?.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (!error?.response) return "Cannot reach the server. Please check your connection.";
  return "Something went wrong. Please try again.";
}

/* ----------------------------- Auth ----------------------------- */
export const authApi = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  me: () => api.get("/auth/me"),
  forgotPassword: (data) => api.post("/auth/forgot-password", data),
  resetPassword: (data) => api.post("/auth/reset-password", data),
};

/* -------------------------- Sentiment --------------------------- */
export const sentimentApi = {
  predict: (text) => api.post("/sentiment/predict", { text }),
  list: (params) => api.get("/predictions", { params }),
  get: (id) => api.get(`/predictions/${id}`),
  remove: (id) => api.delete(`/predictions/${id}`),
};

/* ----------------------- URL scraping analysis ------------------ */
export const analyzeApi = {
  url: (url) => api.post("/analyze-url", { url }, { timeout: 60000 }),
  history: (params) => api.get("/url-history", { params }),
  get: (id) => api.get(`/url-history/${id}`),
  remove: (id) => api.delete(`/url-history/${id}`),
};

/* -------------------------- Dashboard --------------------------- */
export const dashboardApi = {
  get: () => api.get("/dashboard"),
  profile: () => api.get("/profile"),
  updateProfile: (data) => api.put("/profile", data),
  modelPerformance: () => api.get("/model-performance"),
};

export const metaApi = {
  health: () => api.get("/health"),
};
