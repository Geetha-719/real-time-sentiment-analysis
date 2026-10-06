import clsx from "clsx";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export function StatCard({ label, value, icon: Icon, tone = "brand", hint, trend }) {
  const tones = {
    brand: "bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300",
    positive: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300",
    negative: "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-300",
    neutral: "bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-300",
    slate: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  };
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        {Icon && (
          <div className={clsx("flex h-11 w-11 items-center justify-center rounded-xl", tones[tone])}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
      {typeof trend === "number" && (
        <div
          className={clsx(
            "mt-3 inline-flex items-center gap-1 text-xs font-semibold",
            trend >= 0 ? "text-emerald-600" : "text-red-600"
          )}
        >
          {trend >= 0 ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
          {Math.abs(trend)}%
        </div>
      )}
    </div>
  );
}
