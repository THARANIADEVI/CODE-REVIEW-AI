import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function OAuthCallback() {
  const { loginWithToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const ranOnce = useRef(false);

  useEffect(() => {
    if (ranOnce.current) return;
    ranOnce.current = true;

    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (!token) {
      setError("Missing sign-in token");
      return;
    }

    loginWithToken(token)
      .then(() => navigate("/dashboard"))
      .catch(() => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setError("We couldn't sign you in with GitHub");
      });
  }, [loginWithToken, navigate]);

  if (error) {
    return (
      <div className="max-w-md mx-auto mt-16 card p-8 text-center">
        <h1 className="text-2xl font-bold mb-4">Sign-in failed</h1>
        <p className="text-red-600 text-sm mb-4">{error}</p>
        <Link to="/login" className="text-brand-600 font-medium">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-16 card p-8 text-center">
      <p className="text-gray-500">Signing you in...</p>
    </div>
  );
}
