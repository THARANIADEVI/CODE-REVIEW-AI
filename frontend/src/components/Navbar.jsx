import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { logoutUser } from "../services/api";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {
      // ignore network errors on logout
    }
    logout();
    navigate("/login");
  };

  return (
    <nav className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="font-bold text-lg text-brand-600">
          AI Code Review Assistant
        </Link>
        {user && (
          <div className="flex items-center gap-4 text-sm">
            <Link to="/dashboard" className="hover:text-brand-600">
              Dashboard
            </Link>
            <Link to="/submit" className="hover:text-brand-600">
              New Review
            </Link>
            <Link to="/profile" className="hover:text-brand-600">
              {user.name}
            </Link>
            <button onClick={handleLogout} className="btn-secondary">
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
