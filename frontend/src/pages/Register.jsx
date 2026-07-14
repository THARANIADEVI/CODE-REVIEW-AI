import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(form.name, form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 card p-8">
      <h1 className="text-2xl font-bold mb-6">Create account</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          required
          placeholder="Name"
          className="input"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
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
          placeholder="Password (min 6 chars)"
          className="input"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Creating..." : "Create account"}
        </button>
      </form>
      <div className="flex items-center gap-3 my-4">
        <div className="h-px bg-gray-200 flex-1" />
        <span className="text-xs text-gray-400">OR</span>
        <div className="h-px bg-gray-200 flex-1" />
      </div>
      <button
        type="button"
        onClick={() =>
          (window.location.href = `${
            import.meta.env.VITE_API_BASE_URL || "/api"
          }/oauth/github/login`)
        }
        className="w-full bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-lg font-medium transition-colors"
      >
        Continue with GitHub
      </button>
      <p className="text-sm mt-4 text-gray-500">
        Already have an account?{" "}
        <Link to="/login" className="text-brand-600 font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}
