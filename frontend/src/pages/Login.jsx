import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 card p-8">
      <h1 className="text-2xl font-bold mb-6">Sign in</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="email"
          required
          placeholder="Email"
          className="input"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          type="password"
          required
          placeholder="Password"
          className="input"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <p className="text-sm mt-4 text-gray-500">
        No account?{" "}
        <Link to="/register" className="text-brand-600 font-medium">
          Register
        </Link>
      </p>
    </div>
  );
}
