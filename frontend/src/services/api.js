import axios from "axios";

// In production (Vercel), point at the deployed Render backend via
// VITE_API_BASE_URL. In local dev, falls back to the Vite proxy at /api.
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || "/api" });

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
export const getAnalytics = () => api.get("/reviews/analytics");
export const compareReviews = (a, b) => api.get("/reviews/compare", { params: { a, b } });
export const generateRefactor = (id) => api.post(`/reviews/${id}/refactor`);
export const getRefactor = (id) => api.get(`/reviews/${id}/refactor`);

// ---- Reports ----
export const downloadReport = (id, format) =>
  api.get(`/reports/${id}/${format}`, { responseType: "blob" });

// ---- Workspaces ----
export const listWorkspaces = () => api.get("/workspaces");
export const createWorkspace = (data) => api.post("/workspaces", data);
export const getWorkspace = (id) => api.get(`/workspaces/${id}`);
export const inviteWorkspaceMember = (id, data) => api.post(`/workspaces/${id}/members`, data);
export const removeWorkspaceMember = (id, memberUserId) =>
  api.delete(`/workspaces/${id}/members/${memberUserId}`);
export const getWorkspaceProjects = (id) => api.get(`/workspaces/${id}/projects`);
export const moveProjectToWorkspace = (projectId, workspaceId) =>
  api.patch(`/workspaces/projects/${projectId}`, { workspace_id: workspaceId });

export default api;
