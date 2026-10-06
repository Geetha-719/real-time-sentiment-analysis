import { Link } from "react-router-dom";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Globe2,
  LineChart,
  Moon,
  Newspaper,
  ScanText,
  Sparkles,
  Sun,
  TrendingUp,
} from "lucide-react";
import { useTheme } from "../context/ThemeContext.jsx";

const FEATURES = [
  {
    icon: ScanText,
    title: "Web Scraping",
    text: "Fetch any public webpage with requests and extract its text with BeautifulSoup.",
  },
  {
    icon: BrainCircuit,
    title: "NLP & Machine Learning",
    text: "TF-IDF vectorization with Logistic Regression, trained on real labelled data.",
  },
  {
    icon: BarChart3,
    title: "Interactive Dashboard",
    text: "Track totals, distributions and trends of analyzed webpages with charts.",
  },
  {
    icon: TrendingUp,
    title: "Sentiment Trends",
    text: "See how webpage sentiment changes over time at a glance.",
  },
];

const STEPS = [
  { title: "Paste a URL", text: "Enter any publicly accessible webpage address." },
  { title: "Scrape & Clean", text: "The page is fetched and its readable text extracted." },
  { title: "Vectorize", text: "Text becomes TF-IDF features (unigrams + bigrams)." },
  { title: "Predict", text: "The trained model predicts sentiment and shows why." },
];

export default function LandingPage() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Nav */}
      <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur dark:bg-slate-950/80">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
              <BarChart3 className="h-5 w-5" />
            </div>
            <span className="font-bold text-slate-900 dark:text-white">SentimentAI</span>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={toggleTheme} className="btn-ghost !p-2" aria-label="Toggle theme">
              {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
            <Link to="/login" className="btn-secondary hidden sm:inline-flex">
              Login
            </Link>
            <Link to="/register" className="btn-primary">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-brand-50/70 to-white dark:from-brand-600/5 dark:to-slate-950" />
        <div className="mx-auto max-w-7xl px-4 py-20 text-center sm:px-6 lg:py-28">
          <span className="badge mx-auto mb-6 bg-brand-50 text-brand-700 ring-1 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20">
            <Sparkles className="h-3.5 w-3.5" /> B.Tech AI/ML + Full-Stack Project
          </span>
          <h1 className="mx-auto max-w-4xl text-4xl font-black tracking-tight text-slate-900 dark:text-white sm:text-6xl">
            Real-Time <span className="text-brand-600 dark:text-brand-400">Sentiment Analysis</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
            Analyze the sentiment of a webpage using web scraping and machine learning. Paste a URL and get an
            explained sentiment result in seconds.
          </p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/register" className="btn-primary w-full px-6 py-3 text-base sm:w-auto">
              Get Started <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/login" className="btn-secondary w-full px-6 py-3 text-base sm:w-auto">
              Login
            </Link>
          </div>

          <div className="mx-auto mt-16 grid max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: "Training samples", value: "69,971" },
              { label: "Model accuracy", value: "93%" },
              { label: "Sentiment classes", value: "4" },
              { label: "Input", value: "Webpage URL" },
            ].map((s) => (
              <div key={s.label} className="card p-5">
                <p className="text-2xl font-bold text-slate-900 dark:text-white">{s.value}</p>
                <p className="mt-1 text-xs text-slate-500">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t bg-slate-50 py-20 dark:bg-slate-900/40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeading eyebrow="How It Works" title="From raw text to sentiment in four steps" />
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s, i) => (
              <div key={s.title} className="card relative p-6">
                <span className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white">
                  {i + 1}
                </span>
                <h3 className="font-semibold text-slate-900 dark:text-white">{s.title}</h3>
                <p className="mt-1.5 text-sm text-slate-500">{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeading
            eyebrow="Capabilities"
            title="Everything for modern sentiment analytics"
            subtitle="Built with FastAPI, PostgreSQL and React, and a genuinely trained Classical NLP pipeline."
          />
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6 transition hover:shadow-card">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-white">{f.title}</h3>
                <p className="mt-1.5 text-sm text-slate-500">{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why */}
      <section className="border-t bg-slate-50 py-20 dark:bg-slate-900/40">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-2">
          <div>
            <SectionHeading
              eyebrow="Why It Matters"
              title="Understand opinion at scale"
              align="left"
            />
            <p className="mt-5 text-slate-600 dark:text-slate-400">
              Businesses, researchers and analysts need to know how people feel about products, events and topics.
              Manual reading does not scale. This system turns large volumes of text into clear, measurable sentiment
              signals you can act on.
            </p>
            <ul className="mt-6 space-y-3">
              {[
                "Track public reaction to news and events as they happen.",
                "Monitor brand or product sentiment across sources.",
                "Explain every prediction in plain language, with technical detail on demand.",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-sm text-slate-600 dark:text-slate-300">
                  <span className="mt-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
                    ✓
                  </span>
                  {t}
                </li>
              ))}
            </ul>
            <Link to="/register" className="btn-primary mt-8">
              Start analyzing free <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="card space-y-3 p-5">
              <LineChart className="h-6 w-6 text-brand-600" />
              <p className="text-sm font-semibold text-slate-900 dark:text-white">Sentiment over time</p>
              <div className="h-24 rounded-lg bg-gradient-to-t from-brand-100 to-transparent dark:from-brand-500/10" />
            </div>
            <div className="card mt-6 space-y-3 p-5">
              <Newspaper className="h-6 w-6 text-emerald-600" />
              <p className="text-sm font-semibold text-slate-900 dark:text-white">Live news analysis</p>
              <div className="space-y-2">
                <div className="h-2.5 w-full rounded-full bg-slate-100 dark:bg-slate-800" />
                <div className="h-2.5 w-4/5 rounded-full bg-slate-100 dark:bg-slate-800" />
                <div className="h-2.5 w-3/5 rounded-full bg-slate-100 dark:bg-slate-800" />
              </div>
            </div>
            <div className="card col-span-2 space-y-3 p-5">
              <BrainCircuit className="h-6 w-6 text-amber-600" />
              <p className="text-sm font-semibold text-slate-900 dark:text-white">Model comparison</p>
              <div className="flex items-end gap-3">
                {[["NB", 92], ["LR", 93], ["LSTM", 70]].map(([m, h]) => (
                  <div key={m} className="flex flex-col items-center gap-1">
                    <div className="w-10 rounded-t-lg bg-brand-500" style={{ height: `${h}px` }} />
                    <span className="text-[11px] text-slate-400">{m}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 text-sm text-slate-500 sm:flex-row sm:px-6">
          <p>© {new Date().getFullYear()} SentimentAI · Academic project</p>
          <div className="flex gap-6">
            <Link to="/login" className="hover:text-brand-600">Login</Link>
            <Link to="/register" className="hover:text-brand-600">Get Started</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function SectionHeading({ eyebrow, title, subtitle, align = "center" }) {
  return (
    <div className={align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      <p className="text-sm font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-400">{eyebrow}</p>
      <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">{title}</h2>
      {subtitle && <p className="mt-4 text-slate-600 dark:text-slate-400">{subtitle}</p>}
    </div>
  );
}
