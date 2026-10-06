import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import clsx from "clsx";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  PlusSquare,
  Sun,
  User,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analyze", label: "Analyze URL", icon: PlusSquare },
  { to: "/history", label: "History", icon: History },
  { to: "/model-insights", label: "Model Insights", icon: BrainCircuit },
  { to: "/how-it-works", label: "How It Works", icon: Activity },
  { to: "/profile", label: "Profile", icon: User },
];

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-soft">
        <BarChart3 className="h-5 w-5" />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-bold text-slate-900 dark:text-white">SentimentAI</p>
        <p className="text-[11px] text-slate-400">Real-time analysis</p>
      </div>
    </div>
  );
}

function NavItems({ onNavigate }) {
  return (
    <nav className="space-y-1">
      {NAV.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={onNavigate}
          className={({ isActive }) => clsx("sidebar-link", isActive && "sidebar-link-active")}
        >
          <Icon className="h-[18px] w-[18px]" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const initials = (user?.full_name || "U")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Sidebar desktop */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r bg-white px-4 py-5 dark:bg-slate-900 lg:flex">
        <Brand />
        <div className="mt-8 flex-1">
          <NavItems />
        </div>
        <div className="border-t pt-4">
          <div className="mb-3 flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 dark:bg-brand-500/20 dark:text-brand-300">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">{user?.full_name}</p>
              <p className="truncate text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="sidebar-link w-full text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10">
            <LogOut className="h-[18px] w-[18px]" /> Log out
          </button>
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 flex w-72 flex-col bg-white px-4 py-5 dark:bg-slate-900">
            <div className="flex items-center justify-between">
              <Brand />
              <button className="btn-ghost !p-1.5" onClick={() => setMobileOpen(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-6 flex-1" onClick={() => setMobileOpen(false)}>
              <NavItems />
            </div>
            <button onClick={handleLogout} className="sidebar-link w-full text-red-600">
              <LogOut className="h-[18px] w-[18px]" /> Log out
            </button>
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-white/80 px-4 backdrop-blur dark:bg-slate-900/80 sm:px-6">
          <button className="btn-ghost !p-2 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
          <div className="hidden lg:block">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Welcome back, <span className="font-semibold text-slate-800 dark:text-slate-100">{user?.full_name?.split(" ")[0]}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleTheme} className="btn-ghost !p-2" aria-label="Toggle theme">
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 dark:bg-brand-500/20 dark:text-brand-300">
              {initials}
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
