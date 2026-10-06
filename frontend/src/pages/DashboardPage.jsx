import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, ExternalLink, FileText, Globe, Smile, Frown, Meh, Sparkles, Layers } from "lucide-react";
import { dashboardApi, apiError } from "../services/api.js";
import { StatCard } from "../components/StatCard.jsx";
import { EmptyState, Skeleton, SkeletonCard } from "../components/ui.jsx";
import { SentimentBadge, SENTIMENT_COLORS, confidenceColor, StatusMessage } from "../components/SentimentBadge.jsx";
import { useTheme } from "../context/ThemeContext.jsx";

export default function DashboardPage() {
  const { theme } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const { data } = await dashboardApi.get();
        if (active) setData(data);
      } catch (err) {
        if (active) setError(apiError(err));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const axisColor = theme === "dark" ? "#94a3b8" : "#64748b";
  const gridColor = theme === "dark" ? "#1e293b" : "#e2e8f0";

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-56" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (error) return <StatusMessage kind="error" title="Could not load dashboard">{error}</StatusMessage>;

  const distData = (data.distribution || []).filter((d) => d.count > 0).map((d) => ({ name: d.label, value: d.count }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
          <p className="text-sm text-slate-500">Your webpage sentiment analysis at a glance.</p>
        </div>
        <Link to="/analyze" className="btn-primary">
          <Sparkles className="h-4 w-4" /> Analyze a URL
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Webpages Analyzed" value={data.total_analyses} icon={Globe} tone="brand" hint={`Avg confidence ${(data.avg_confidence * 100).toFixed(0)}%`} />
        <StatCard label="Positive" value={data.positive} icon={Smile} tone="positive" />
        <StatCard label="Negative" value={data.negative} icon={Frown} tone="negative" />
        <StatCard label="Neutral" value={data.neutral} icon={Meh} tone="neutral" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <h2 className="font-semibold text-slate-900 dark:text-white">Sentiment Trend (14 days)</h2>
          <p className="mb-4 text-sm text-slate-500">Daily webpage analyses by overall sentiment.</p>
          {data.trend.length === 0 ? (
            <EmptyState icon={Activity} title="No trend data yet" description="Analyze a webpage to start building your trend." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={data.trend} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: axisColor }} />
                <YAxis tick={{ fontSize: 12, fill: axisColor }} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "none", background: theme === "dark" ? "#0f172a" : "#fff" }} />
                <Legend />
                <Line type="monotone" dataKey="Positive" stroke={SENTIMENT_COLORS.Positive} strokeWidth={2} />
                <Line type="monotone" dataKey="Negative" stroke={SENTIMENT_COLORS.Negative} strokeWidth={2} />
                <Line type="monotone" dataKey="Neutral" stroke={SENTIMENT_COLORS.Neutral} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white">Overall Distribution</h2>
          <p className="mb-4 text-sm text-slate-500">Across all analyzed webpages.</p>
          {distData.length === 0 ? (
            <EmptyState icon={Meh} title="No data yet" />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={distData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: axisColor }} />
                <YAxis tick={{ fontSize: 12, fill: axisColor }} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "none", background: theme === "dark" ? "#0f172a" : "#fff" }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {distData.map((d) => (
                    <Cell key={d.name} fill={SENTIMENT_COLORS[d.name]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <h2 className="font-semibold text-slate-900 dark:text-white">Recent Webpage Analyses</h2>
            <Link to="/history" className="link text-sm">
              View all
            </Link>
          </div>
          {data.recent.length === 0 ? (
            <EmptyState
              icon={Globe}
              title="No analyses yet"
              description="Analyze your first webpage to see it here."
              action={
                <Link to="/analyze" className="btn-primary">
                  Analyze a URL
                </Link>
              }
            />
          ) : (
            <ul className="divide-y">
              {data.recent.map((p) => (
                <li key={p.id} className="flex items-start justify-between gap-4 px-5 py-3.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-700 dark:text-slate-200">
                      {p.title || p.url}
                    </p>
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-0.5 inline-flex max-w-full items-center gap-1 truncate text-xs text-slate-400 hover:text-brand-600"
                    >
                      <span className="truncate">{p.url}</span>
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <SentimentBadge label={p.overall_sentiment} size="sm" />
                    <span className={`text-xs font-semibold ${confidenceColor(p.confidence)}`}>
                      {(p.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white">Summary</h2>
          <div className="mt-4 space-y-3 text-sm">
            <SummaryRow icon={Globe} label="Webpages analyzed" value={data.total_analyses} />
            <SummaryRow icon={FileText} label="Total words extracted" value={data.total_words.toLocaleString()} />
            <SummaryRow icon={Layers} label="Irrelevant pages" value={data.irrelevant} />
            <SummaryRow icon={Activity} label="Text analyses" value={data.text_analyses} />
          </div>
          <Link to="/model-insights" className="btn-secondary mt-5 w-full">
            View model insights
          </Link>
        </div>
      </div>
    </div>
  );
}

function SummaryRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-2 text-slate-500">
        <Icon className="h-4 w-4" /> {label}
      </span>
      <span className="font-semibold text-slate-800 dark:text-slate-100">{value}</span>
    </div>
  );
}
