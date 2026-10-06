import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Calendar, Mail, Pencil, Save, User as UserIcon, X } from "lucide-react";
import { dashboardApi, apiError } from "../services/api.js";
import { StatCard } from "../components/StatCard.jsx";
import { FullPageLoader } from "../components/ui.jsx";
import { StatusMessage } from "../components/SentimentBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProfilePage() {
  const { refresh } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const { data } = await dashboardApi.profile();
      setProfile(data);
      setName(data.full_name);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    if (name.trim().length < 2) {
      toast.error("Full name is too short.");
      return;
    }
    setSaving(true);
    try {
      const { data } = await dashboardApi.updateProfile({ full_name: name.trim() });
      setProfile(data);
      setEditing(false);
      await refresh();
      toast.success("Profile updated.");
    } catch (err) {
      toast.error(apiError(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <FullPageLoader label="Loading profile..." />;
  if (error) return <StatusMessage kind="error" title="Could not load profile">{error}</StatusMessage>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Profile</h1>
        <p className="text-sm text-slate-500">Manage your account details.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 text-xl font-bold text-brand-700 dark:bg-brand-500/20 dark:text-brand-300">
              {profile.full_name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()}
            </div>
            <div className="flex-1">
              {editing ? (
                <div className="flex flex-wrap items-center gap-2">
                  <input className="input max-w-xs" value={name} onChange={(e) => setName(e.target.value)} />
                  <button onClick={save} className="btn-primary" disabled={saving}>
                    <Save className="h-4 w-4" /> Save
                  </button>
                  <button onClick={() => { setEditing(false); setName(profile.full_name); }} className="btn-secondary">
                    <X className="h-4 w-4" /> Cancel
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">{profile.full_name}</h2>
                  <button onClick={() => setEditing(true)} className="btn-ghost !p-2" aria-label="Edit name">
                    <Pencil className="h-4 w-4" />
                  </button>
                </div>
              )}
              <p className="mt-1.5 flex items-center gap-2 text-sm text-slate-500">
                <Mail className="h-4 w-4" /> {profile.email}
              </p>
              <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
                <Calendar className="h-4 w-4" /> Member since {new Date(profile.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <StatCard label="Total Analyses" value={profile.total_analyses} icon={UserIcon} tone="brand" />
        </div>
      </div>
    </div>
  );
}
