import clsx from "clsx";
import {
  AlertCircle,
  Frown,
  HelpCircle,
  Meh,
  Smile,
} from "lucide-react";

const STYLES = {
  Positive: {
    text: "text-emerald-700 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-500/10",
    ring: "ring-emerald-200 dark:ring-emerald-500/20",
    dot: "bg-emerald-500",
    icon: Smile,
  },
  Negative: {
    text: "text-red-700 dark:text-red-300",
    bg: "bg-red-50 dark:bg-red-500/10",
    ring: "ring-red-200 dark:ring-red-500/20",
    dot: "bg-red-500",
    icon: Frown,
  },
  Neutral: {
    text: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-500/10",
    ring: "ring-amber-200 dark:ring-amber-500/20",
    dot: "bg-amber-500",
    icon: Meh,
  },
  Irrelevant: {
    text: "text-slate-700 dark:text-slate-300",
    bg: "bg-slate-100 dark:bg-slate-500/10",
    ring: "ring-slate-200 dark:ring-slate-500/20",
    dot: "bg-slate-500",
    icon: HelpCircle,
  },
};

export const SENTIMENT_COLORS = {
  Positive: "#10b981",
  Negative: "#ef4444",
  Neutral: "#f59e0b",
  Irrelevant: "#64748b",
};

export function SentimentBadge({ label, size = "md", showIcon = true }) {
  const style = STYLES[label] || STYLES.Neutral;
  const Icon = style.icon;
  return (
    <span
      className={clsx(
        "badge ring-1",
        style.bg,
        style.text,
        style.ring,
        size === "sm" ? "px-2 py-0.5 text-[11px]" : ""
      )}
    >
      {showIcon && <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} />}
      {label}
    </span>
  );
}

export function SentimentDot({ label }) {
  const style = STYLES[label] || STYLES.Neutral;
  return <span className={clsx("inline-block h-2.5 w-2.5 rounded-full", style.dot)} />;
}

export function confidenceColor(c) {
  if (c >= 0.75) return "text-emerald-600 dark:text-emerald-400";
  if (c >= 0.5) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export function StatusMessage({ kind = "info", title, children }) {
  const kinds = {
    info: "bg-brand-50 text-brand-800 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-200 dark:ring-brand-500/20",
    error: "bg-red-50 text-red-800 ring-red-200 dark:bg-red-500/10 dark:text-red-200 dark:ring-red-500/20",
    warning: "bg-amber-50 text-amber-800 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-200 dark:ring-amber-500/20",
    success: "bg-emerald-50 text-emerald-800 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-200 dark:ring-emerald-500/20",
  };
  return (
    <div className={clsx("flex gap-3 rounded-xl p-4 text-sm ring-1", kinds[kind])}>
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        {title && <p className="font-semibold">{title}</p>}
        <div>{children}</div>
      </div>
    </div>
  );
}
