import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  FileText,
  Globe,
  History,
  Link2,
  Loader2,
  RotateCcw,
  Search,
  Sparkles,
} from "lucide-react";
import clsx from "clsx";
import { analyzeApi, apiError } from "../services/api.js";
import { SentimentBadge, SENTIMENT_COLORS, confidenceColor } from "../components/SentimentBadge.jsx";

const EXAMPLES = [
  "https://en.wikipedia.org/wiki/Sentiment_analysis",
  "https://www.bbc.com/news",
  "https://example.com",
];

function isValidUrl(value) {
  if (!value.trim()) return false;
  try {
    const url = new URL(value.trim().startsWith("http") ? value.trim() : `https://${value.trim()}`);
    return !!url.hostname && url.hostname.includes(".");
  } catch {
    return false;
  }
}

export default function AnalyzePage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const analyze = async (target) => {
    const value = (target ?? url).trim();
    setError("");
    if (!value) {
      setError("Please enter a webpage URL.");
      return;
    }
    if (!isValidUrl(value)) {
      setError("That does not look like a valid URL. Example: https://example.com/article");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const { data } = await analyzeApi.url(value);
      setResult(data);
      toast.success("Analysis completed successfully.");
    } catch (err) {
      setError(apiError(err));
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setUrl("");
    setResult(null);
    setError("");
  };

  const distribution = result
    ? ["Positive", "Negative", "Neutral", "Irrelevant"].map((label) => ({
        label,
        value: result.sentiment_distribution?.[label] ?? 0,
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Analyze a Webpage&apos;s Sentiment
        </h1>
        <p className="text-sm text-slate-500">
          Paste a public webpage URL. We scrape it, extract the text, and predict its sentiment.
        </p>
      </div>

      {/* URL input */}
      <div className="card p-5 sm:p-6">
        <label className="label flex items-center gap-2">
          <Globe className="h-4 w-4 text-brand-600" /> Enter a public webpage URL
        </label>
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Link2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="url"
              className="input pl-10"
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && analyze()}
              disabled={loading}
            />
          </div>
          <button onClick={() => analyze()} className="btn-primary sm:w-auto" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            {loading ? "Analyzing..." : "Analyze Sentiment"}
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-400">Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setUrl(ex);
                analyze(ex);
              }}
              disabled={loading}
              className="rounded-lg border bg-slate-50 px-2.5 py-1 text-slate-600 transition hover:border-brand-300 hover:text-brand-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-300"
            >
              {ex.replace("https://", "")}
            </button>
          ))}
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-500/10 dark:text-red-300 dark:ring-red-500/20">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="card flex flex-col items-center justify-center gap-3 p-12 text-center">
          <Loader2 className="h-9 w-9 animate-spin text-brand-600" />
          <p className="font-semibold text-slate-700 dark:text-slate-200">Fetching and analyzing the webpage...</p>
          <div className="text-xs text-slate-400">
            URL → HTTP request → HTML → BeautifulSoup → text extraction → TF-IDF → model
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !result && (
        <div className="card flex flex-col items-center justify-center gap-3 p-12 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-500 dark:bg-brand-500/10">
            <FileText className="h-7 w-7" />
          </div>
          <p className="font-semibold text-slate-700 dark:text-slate-200">No analysis yet</p>
          <p className="max-w-md text-sm text-slate-500">
            Enter a publicly accessible webpage URL above and click <strong>Analyze Sentiment</strong>. The backend
            will download the page, extract its text and predict the sentiment.
          </p>
        </div>
      )}

      {/* Result */}
      {!loading && result && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            {/* Summary card */}
            <div className="card animate-fade-in overflow-hidden">
              <div
                className="h-1.5 w-full"
                style={{ backgroundColor: SENTIMENT_COLORS[result.overall_sentiment] }}
              />
              <div className="p-5 sm:p-6">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Webpage title</p>
                    <h2 className="mt-1 text-lg font-bold leading-snug text-slate-900 dark:text-white">
                      {result.title}
                    </h2>
                    <a
                      href={result.final_url || result.url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-1 inline-flex max-w-full items-center gap-1 truncate text-xs text-brand-600 hover:underline dark:text-brand-400"
                    >
                      <span className="truncate">{result.final_url || result.url}</span>
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                  </div>
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/50">
                    <p className="text-xs text-slate-400">Overall sentiment</p>
                    <div className="mt-1">
                      <SentimentBadge label={result.overall_sentiment} />
                    </div>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/50">
                    <p className="text-xs text-slate-400">Confidence</p>
                    <p
                      className={clsx("mt-1 text-2xl font-bold", confidenceColor(result.confidence))}
                    >
                      {(result.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/50">
                    <p className="text-xs text-slate-400">Words analyzed</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">
                      {result.word_count.toLocaleString()}
                    </p>
                  </div>
                </div>

                {result.note && (
                  <div className="mt-4 flex items-start gap-2 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{result.note}</span>
                  </div>
                )}

                <div className="mt-5 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-4 w-4" /> Analysis completed successfully.
                </div>
              </div>
            </div>

            {/* Preview */}
            <div className="card p-5 sm:p-6">
              <div className="mb-3 flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-400" />
                <h3 className="font-semibold text-slate-900 dark:text-white">Extracted Text Preview</h3>
              </div>
              <p className="whitespace-pre-line rounded-xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-600 dark:bg-slate-800/50 dark:text-slate-300">
                {result.preview || "(no preview available)"}
              </p>
            </div>
          </div>

          {/* Distribution */}
          <div className="space-y-6">
            <div className="card p-5">
              <h3 className="font-semibold text-slate-900 dark:text-white">Sentiment Distribution</h3>
              <p className="mb-4 text-sm text-slate-500">
                Across {result.chunks_analyzed} text chunks from the page.
              </p>
              <div className="space-y-3">
                {distribution.map((d) => (
                  <div key={d.label}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: SENTIMENT_COLORS[d.label] }}
                        />
                        {d.label}
                      </span>
                      <span className="font-semibold text-slate-700 dark:text-slate-200">
                        {d.value.toFixed(0)}%
                      </span>
                    </div>
                    <div className="mt-1 h-2.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${d.value}%`, backgroundColor: SENTIMENT_COLORS[d.label] }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card p-5">
              <h3 className="mb-3 font-semibold text-slate-900 dark:text-white">Details</h3>
              <dl className="space-y-2 text-sm">
                <Detail label="Model" value={result.model_name} />
                <Detail label="Chunks analyzed" value={result.chunks_analyzed} />
                <Detail label="Words extracted" value={result.word_count.toLocaleString()} />
                <Detail
                  label="Analyzed at"
                  value={result.created_at ? new Date(result.created_at).toLocaleString() : "just now"}
                />
              </dl>
              <button onClick={reset} className="btn-secondary mt-4 w-full">
                <RotateCcw className="h-4 w-4" /> Analyze Another URL
              </button>
              <Link to="/history" className="btn-ghost mt-2 w-full">
                <History className="h-4 w-4" /> View history
              </Link>
            </div>

            <div className="rounded-xl border border-dashed p-4 text-xs text-slate-400">
              <Sparkles className="mb-1 h-3.5 w-3.5" />
              Only publicly accessible pages are analyzed. We respect robots.txt and never bypass logins,
              paywalls or CAPTCHAs. Some sites may block automated requests.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-slate-400">{label}</dt>
      <dd className="truncate font-medium text-slate-700 dark:text-slate-200">{value}</dd>
    </div>
  );
}
