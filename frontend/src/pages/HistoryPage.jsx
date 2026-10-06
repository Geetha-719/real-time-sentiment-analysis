import { useCallback, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { ChevronLeft, ChevronRight, ExternalLink, Eye, History as HistoryIcon, Search, Trash2 } from "lucide-react";
import clsx from "clsx";
import { analyzeApi, apiError } from "../services/api.js";
import { SentimentBadge, SENTIMENT_COLORS, confidenceColor } from "../components/SentimentBadge.jsx";
import { EmptyState, Skeleton } from "../components/ui.jsx";
import { Modal } from "../components/Modal.jsx";

const FILTERS = ["All", "Positive", "Negative", "Neutral", "Irrelevant"];

export default function HistoryPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [sentiment, setSentiment] = useState("All");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = { page, page_size: 10 };
      if (sentiment !== "All") params.sentiment = sentiment;
      if (search.trim()) params.search = search.trim();
      const { data } = await analyzeApi.history(params);
      setData(data);
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  }, [page, sentiment, search]);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async (id) => {
    if (!window.confirm("Delete this analysis from your history?")) return;
    try {
      await analyzeApi.remove(id);
      toast.success("Analysis deleted.");
      if (selected?.id === id) setSelected(null);
      load();
    } catch (err) {
      toast.error(apiError(err));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Analysis History</h1>
        <p className="text-sm text-slate-500">Recently analyzed webpages and their sentiment.</p>
      </div>

      <div className="card p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setPage(1);
              load();
            }}
            className="relative w-full lg:max-w-sm"
          >
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              className="input pl-10"
              placeholder="Search by URL..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>
          <div className="flex flex-wrap items-center gap-2">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => {
                  setSentiment(f);
                  setPage(1);
                }}
                className={clsx(
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                  sentiment === f
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                )}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-500/10 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="card overflow-hidden">
        {loading ? (
          <div className="space-y-3 p-5">
            {[0, 1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            icon={HistoryIcon}
            title="No analyses yet"
            description={
              search || sentiment !== "All"
                ? "Try adjusting your filters or search."
                : "Analyze a webpage URL to build your history."
            }
          />
        ) : (
          <>
            <ul className="divide-y">
              {data.items.map((p) => (
                <li
                  key={p.id}
                  className="flex items-start justify-between gap-4 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-slate-800/40"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">
                      {p.title || p.url}
                    </p>
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-0.5 inline-flex max-w-full items-center gap-1 truncate text-xs text-brand-600 hover:underline dark:text-brand-400"
                    >
                      <span className="truncate">{p.url}</span>
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                    <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
                      <span>{new Date(p.created_at).toLocaleString()}</span>
                      <span>·</span>
                      <span>{p.word_count.toLocaleString()} words</span>
                      <span>·</span>
                      <span className={clsx("font-semibold", confidenceColor(p.confidence))}>
                        {(p.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <SentimentBadge label={p.overall_sentiment} size="sm" />
                    <button onClick={() => setSelected(p)} className="btn-ghost !p-2" aria-label="View details">
                      <Eye className="h-4 w-4" />
                    </button>
                    <button onClick={() => remove(p.id)} className="btn-ghost !p-2 text-red-600" aria-label="Delete">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between border-t px-5 py-3 text-sm">
              <span className="text-slate-500">
                Page {data.page} of {data.pages} · {data.total} total
              </span>
              <div className="flex gap-2">
                <button
                  className="btn-secondary !px-3 !py-1.5"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft className="h-4 w-4" /> Prev
                </button>
                <button
                  className="btn-secondary !px-3 !py-1.5"
                  disabled={page >= data.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      <Modal open={!!selected} onClose={() => setSelected(null)} title="Analysis details" maxWidth="max-w-2xl">
        {selected && <AnalysisDetails p={selected} />}
      </Modal>
    </div>
  );
}

function AnalysisDetails({ p }) {
  const distribution = ["Positive", "Negative", "Neutral", "Irrelevant"].map((label) => ({
    label,
    value: p.sentiment_distribution?.[label] ?? 0,
  }));
  return (
    <div className="space-y-4 text-sm">
      <div>
        <p className="font-semibold text-slate-800 dark:text-slate-100">{p.title || "(untitled)"}</p>
        <a
          href={p.url}
          target="_blank"
          rel="noreferrer"
          className="mt-0.5 inline-flex items-center gap-1 break-all text-xs text-brand-600 hover:underline dark:text-brand-400"
        >
          {p.url} <ExternalLink className="h-3 w-3 shrink-0" />
        </a>
      </div>
      <div className="flex items-center justify-between">
        <SentimentBadge label={p.overall_sentiment} />
        <span className={clsx("font-bold", confidenceColor(p.confidence))}>
          {(p.confidence * 100).toFixed(1)}%
        </span>
      </div>
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Sentiment distribution</p>
        <div className="space-y-2">
          {distribution.map((d) => (
            <div key={d.label} className="flex items-center gap-2">
              <span className="w-20 text-xs text-slate-500">{d.label}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${d.value}%`, backgroundColor: SENTIMENT_COLORS[d.label] }}
                />
              </div>
              <span className="w-10 text-right text-xs text-slate-500">{d.value.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
      {p.preview && (
        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Text preview</p>
          <p className="whitespace-pre-line rounded-lg bg-slate-50 p-3 text-slate-700 dark:bg-slate-800/50 dark:text-slate-200">
            {p.preview}
          </p>
        </div>
      )}
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
          <p className="text-slate-400">Words</p>
          <p className="font-medium text-slate-700 dark:text-slate-200">{p.word_count.toLocaleString()}</p>
        </div>
        <div className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
          <p className="text-slate-400">Chunks</p>
          <p className="font-medium text-slate-700 dark:text-slate-200">{p.chunks_analyzed}</p>
        </div>
        <div className="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
          <p className="text-slate-400">Model</p>
          <p className="truncate font-medium text-slate-700 dark:text-slate-200">{p.model_name}</p>
        </div>
      </div>
    </div>
  );
}
