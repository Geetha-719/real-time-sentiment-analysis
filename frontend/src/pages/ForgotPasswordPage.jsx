import { useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, MailCheck } from "lucide-react";
import { authApi, apiError } from "../services/api.js";
import { AuthShell } from "./LoginPage.jsx";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [devLink, setDevLink] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setDevLink("");
    if (!email) {
      setError("Please enter your email address.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await authApi.forgotPassword({ email: email.trim() });
      setMessage(data.message);
      if (data.reset_link) setDevLink(data.reset_link);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Forgot password" subtitle="We'll help you reset it in a couple of steps.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-500/10 dark:text-red-300 dark:ring-red-500/20">
            {error}
          </div>
        )}
        {message && (
          <div className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300">
            <MailCheck className="mb-1 h-4 w-4" />
            {message}
          </div>
        )}
        {devLink && (
          <div className="rounded-xl bg-brand-50 px-4 py-3 text-sm text-brand-700 ring-1 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-300">
            <p className="mb-1 font-semibold">Development reset link</p>
            <Link to={devLink.replace(window.location.origin, "")} className="break-all link">
              {devLink}
            </Link>
          </div>
        )}
        <div>
          <label className="label">Email</label>
          <input
            type="email"
            className="input"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary w-full" disabled={loading}>
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Sending..." : "Send reset link"}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-500">
        Remembered your password?{" "}
        <Link to="/login" className="link">
          Back to login
        </Link>
      </p>
    </AuthShell>
  );
}
