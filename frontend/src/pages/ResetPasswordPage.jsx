import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { Loader2 } from "lucide-react";
import { authApi, apiError } from "../services/api.js";
import { AuthShell } from "./LoginPage.jsx";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") || "";
  const [form, setForm] = useState({ new_password: "", confirm_password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!token) {
      setError("This reset link is missing its token. Please request a new one.");
      return;
    }
    if (form.new_password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (!/[A-Za-z]/.test(form.new_password) || !/[0-9]/.test(form.new_password)) {
      setError("Password must contain at least one letter and one number.");
      return;
    }
    if (form.new_password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await authApi.resetPassword({ token, ...form });
      toast.success(data.message || "Password reset successfully.");
      navigate("/login");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Set a new password" subtitle="Choose a strong password you don't use elsewhere.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-500/10 dark:text-red-300 dark:ring-red-500/20">
            {error}
          </div>
        )}
        <div>
          <label className="label">New password</label>
          <input
            type="password"
            className="input"
            value={form.new_password}
            onChange={(e) => setForm({ ...form, new_password: e.target.value })}
            autoComplete="new-password"
          />
        </div>
        <div>
          <label className="label">Confirm new password</label>
          <input
            type="password"
            className="input"
            value={form.confirm_password}
            onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
            autoComplete="new-password"
          />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Resetting..." : "Reset password"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        <Link to="/login" className="link">
          Back to login
        </Link>
      </p>
    </AuthShell>
  );
}
