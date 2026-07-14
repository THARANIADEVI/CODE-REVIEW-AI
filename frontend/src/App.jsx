import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import PrivateRoute from "./components/PrivateRoute.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Submit from "./pages/Submit.jsx";
import ReviewDetail from "./pages/ReviewDetail.jsx";
import Profile from "./pages/Profile.jsx";
import Analytics from "./pages/Analytics.jsx";
import Compare from "./pages/Compare.jsx";
import OAuthCallback from "./pages/OAuthCallback.jsx";
import Workspaces from "./pages/Workspaces.jsx";
import WorkspaceDetail from "./pages/WorkspaceDetail.jsx";

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/oauth/callback" element={<OAuthCallback />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/submit"
            element={
              <PrivateRoute>
                <Submit />
              </PrivateRoute>
            }
          />
          <Route
            path="/reviews/:id"
            element={
              <PrivateRoute>
                <ReviewDetail />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <PrivateRoute>
                <Analytics />
              </PrivateRoute>
            }
          />
          <Route
            path="/compare"
            element={
              <PrivateRoute>
                <Compare />
              </PrivateRoute>
            }
          />
          <Route
            path="/workspaces"
            element={
              <PrivateRoute>
                <Workspaces />
              </PrivateRoute>
            }
          />
          <Route
            path="/workspaces/:id"
            element={
              <PrivateRoute>
                <WorkspaceDetail />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}
