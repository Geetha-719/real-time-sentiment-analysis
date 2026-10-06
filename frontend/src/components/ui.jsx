import clsx from "clsx";
import { Loader2 } from "lucide-react";

export function Spinner({ className }) {
  return <Loader2 className={clsx("h-4 w-4 animate-spin", className)} />;
}

export function FullPageLoader({ label = "Loading..." }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-slate-500">
      <Spinner className="h-7 w-7 text-brand-600" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function Skeleton({ className }) {
  return <div className={clsx("skeleton", className)} />;
}

export function SkeletonCard() {
  return (
    <div className="card space-y-3 p-5">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      {Icon && (
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-slate-800">
          <Icon className="h-7 w-7" />
        </div>
      )}
      <div>
        <p className="font-semibold text-slate-700 dark:text-slate-200">{title}</p>
        {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}
