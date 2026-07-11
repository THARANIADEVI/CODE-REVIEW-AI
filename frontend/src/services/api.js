import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// ---- Auth ----
export const registerUser = (data) => api.post("/auth/register", data);
export const loginUser = (data) => api.post("/auth/login", data);
export const logoutUser = () => api.post("/auth/logout");
export const getProfile = () => api.get("/auth/profile");
export const updateProfile = (data) => api.put("/auth/profile", data);
export const resetPassword = (data) => api.post("/auth/reset-password", data);

// ---- Upload ----
export const uploadFiles = (formData) =>
  api.post("/upload/files", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const uploadSnippet = (data) => api.post("/upload/snippet", data);
export const uploadGithubRepo = (data) => api.post("/upload/github", data);

// ---- Reviews ----
export const listReviews = (params) => api.get("/reviews", { params });
export const getReview = (id, params) => api.get(`/reviews/${id}`, { params });
export const deleteReview = (id) => api.delete(`/reviews/${id}`);

// ---- Reports ----
export const downloadReport = (id, format) =>
  api.get(`/reports/${id}/${format}`, { responseType: "blob" });

export default api;
