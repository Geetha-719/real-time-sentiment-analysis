import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { Check, Loader2 } from "lucide-react";
import clsx from "clsx";
import { useAuth } from "../context/AuthContext.jsx";
import { apiError } from "../services/api.js";
import { AuthShell } from "./LoginPage.jsx";

function strength(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const pwScore = useMemo(() => strength(form.password), [form.password]);
  const pwLabels = ["Too weak", "Weak", "Fair", "Good", "Strong"];
  const pwColors = ["bg-red-500", "bg-red-500", "bg-amber-500", "bg-emerald-500", "bg-emerald-500"];

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.full_name.trim() || !form.email || !form.password) {
      setError("Please fill in all fields.");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (!/[A-Za-z]/.test(form.password) || !/[0-9]/.test(form.password)) {
      setError("Password must contain at least one letter and one number.");
      return;
    }
    if (form.password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirm_password,
      });
      toast.success("Account created! Welcome aboard.");
      navigate("/dashboard");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Create your account" subtitle="Start analyzing sentiment in real time.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-500/10 dark:text-red-300 dark:ring-red-500/20">
            {error}
          </div>
        )}
        <div>
          <label className="label">Full name</label>
          <input
            className="input"
            placeholder="Jane Doe"
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            autoComplete="name"
          />
        </div>
        <div>
          <label className="label">Email</label>
          <input
            type="email"
            className="input"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            autoComplete="email"
          />
        </div>
        <div>
          <label className="label">Password</label>
          <input
            type="password"
            className="input"
            placeholder="At least 8 characters"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            autoComplete="new-password"
          />
          {form.password && (
            <div className="mt-2">
              <div className="flex gap-1">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={clsx(
                      "h-1 flex-1 rounded-full",
                      i < pwScore ? pwColors[pwScore] : "bg-slate-200 dark:bg-slate-700"
                    )}
                  />
                ))}
              </div>
              <p className="mt-1 text-xs text-slate-400">Strength: {pwLabels[pwScore]}</p>
            </div>
          )}
        </div>
        <div>
          <label className="label">Confirm password</label>
          <input
            type="password"
            className="input"
            placeholder="Repeat your password"
            value={form.confirm_password}
            onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
            autoComplete="new-password"
          />
          {form.confirm_password && form.password === form.confirm_password && (
            <p className="mt-1 inline-flex items-center gap-1 text-xs text-emerald-600">
              <Check className="h-3 w-3" /> Passwords match
            </p>
          )}
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Creating account..." : "Create account"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Already have an account?{" "}
        <Link to="/login" className="link">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}
