import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BrainCircuit, Database, Layers, Target } from "lucide-react";
import clsx from "clsx";
import { dashboardApi, apiError } from "../services/api.js";
import { EmptyState, FullPageLoader } from "../components/ui.jsx";
import { SENTIMENT_COLORS, StatusMessage } from "../components/SentimentBadge.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { StatCard } from "../components/StatCard.jsx";

export default function ModelInsightsPage() {
  const { theme } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeModel, setActiveModel] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await dashboardApi.modelPerformance();
        setData(data);
        const first = Object.keys(data.models || {})[0];
        setActiveModel(first || null);
      } catch (err) {
        setError(apiError(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const axisColor = theme === "dark" ? "#94a3b8" : "#64748b";
  const gridColor = theme === "dark" ? "#1e293b" : "#e2e8f0";

  if (loading) return <FullPageLoader label="Loading model performance..." />;
  if (error) return <StatusMessage kind="error" title="Could not load model performance">{error}</StatusMessage>;
  if (!data?.available)
    return (
      <StatusMessage kind="warning" title="Model not trained yet">
        Train the model with <code className="font-mono">python -m ml.training.train</code> to see performance here.
      </StatusMessage>
    );

  const models = data.models || {};
  const modelNames = Object.keys(models);
  const comparison = modelNames.map((name) => ({
    name,
    Accuracy: +(models[name].accuracy * 100).toFixed(2),
    "F1 (macro)": +(models[name].f1_macro * 100).toFixed(2),
    "F1 (weighted)": +(models[name].f1_weighted * 100).toFixed(2),
  }));

  const meta = data.metadata || {};
  const dataset = data.dataset || {};
  const chosen = meta.model_name;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Model Insights</h1>
        <p className="text-sm text-slate-500">
          Actual evaluation results from the training run — no fabricated numbers.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Best Model" value={chosen} icon={Target} tone="brand" hint={meta.trained_at ? `Trained ${meta.trained_at.replace("T", " ")}` : undefined} />
        <StatCard label="Classes" value={(dataset.classes || []).length} icon={Layers} tone="slate" hint={(dataset.classes || []).join(", ")} />
        <StatCard label="Training samples" value={(dataset.n_train || 0).toLocaleString()} icon={Database} tone="positive" />
        <StatCard label="TF-IDF features" value={(meta.n_features || 0).toLocaleString()} icon={BrainCircuit} tone="neutral" hint={`n-grams ${meta.ngram_range?.join("–")}, stemming ${meta.stemming ? "on" : "off"}`} />
      </div>

      {/* Comparison chart */}
      <div className="card p-5">
        <h2 className="font-semibold text-slate-900 dark:text-white">Model Comparison</h2>
        <p className="mb-4 text-sm text-slate-500">Accuracy and F1 scores on the held-out test set.</p>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparison} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: axisColor }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: axisColor }} />
            <Tooltip contentStyle={{ borderRadius: 12, border: "none", background: theme === "dark" ? "#0f172a" : "#fff" }} />
            <Legend />
            <Bar dataKey="Accuracy" fill="#6366f1" radius={[6, 6, 0, 0]} />
            <Bar dataKey="F1 (macro)" fill="#10b981" radius={[6, 6, 0, 0]} />
            <Bar dataKey="F1 (weighted)" fill="#f59e0b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Per-model metrics + confusion matrix */}
      <div className="card overflow-hidden">
        <div className="flex flex-wrap gap-1 border-b p-3">
          {modelNames.map((name) => (
            <button
              key={name}
              onClick={() => setActiveModel(name)}
              className={clsx(
                "rounded-lg px-3.5 py-2 text-sm font-semibold transition",
                activeModel === name ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              )}
            >
              {name}
            </button>
          ))}
        </div>
        {activeModel && <ModelPanel name={activeModel} m={models[activeModel]} axisColor={axisColor} />}
      </div>

      {/* Top terms */}
      <div className="grid gap-6 md:grid-cols-2">
        {Object.entries(data.top_terms || {}).map(([label, terms]) => (
          <div key={label} className="card p-5">
            <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: SENTIMENT_COLORS[label] }} />
              Top terms for {label}
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {terms.map((t) => (
                <span key={t} className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-300">
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModelPanel({ name, m, axisColor }) {
  const metrics = [
    { label: "Accuracy", value: m.accuracy },
    { label: "Precision (macro)", value: m.precision_macro },
    { label: "Recall (macro)", value: m.recall_macro },
    { label: "F1 (macro)", value: m.f1_macro },
    { label: "F1 (weighted)", value: m.f1_weighted },
    { label: "ROC-AUC (OVR)", value: m.roc_auc_ovr_macro },
  ];
  const classes = m.classes || [];

  return (
    <div className="p-5">
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {metrics.map((x) => (
          <div key={x.label} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/50">
            <p className="text-xs text-slate-400">{x.label}</p>
            <p className="mt-0.5 text-lg font-bold text-slate-900 dark:text-white">
              {x.value == null ? "—" : `${(x.value * 100).toFixed(2)}%`}
            </p>
          </div>
        ))}
      </div>

      <h3 className="mb-3 mt-6 font-semibold text-slate-900 dark:text-white">Confusion Matrix</h3>
      {m.confusion_matrix ? (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="p-2 text-left text-xs font-medium text-slate-400">actual \ predicted</th>
                {classes.map((c) => (
                  <th key={c} className="p-2 text-center text-xs font-medium text-slate-500">{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {m.confusion_matrix.map((row, i) => (
                <tr key={i}>
                  <td className="p-2 text-xs font-semibold text-slate-600 dark:text-slate-300">{classes[i]}</td>
                  {row.map((v, j) => {
                    const max = Math.max(...m.confusion_matrix.flat()) || 1;
                    const intensity = v / max;
                    return (
                      <td key={j} className="p-2 text-center">
                        <span
                          className="inline-flex h-9 w-full min-w-[48px] items-center justify-center rounded-lg font-semibold"
                          style={{
                            backgroundColor: i === j ? `rgba(16,185,129,${0.12 + intensity * 0.6})` : `rgba(239,68,68,${0.05 + intensity * 0.45})`,
                            color: i === j ? "#065f46" : "#7f1d1d",
                          }}
                        >
                          {v}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="No confusion matrix available" />
      )}
    </div>
  );
}
