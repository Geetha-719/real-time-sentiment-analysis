import { Link } from "react-router-dom";
import {
  ArrowDown,
  BarChart3,
  Bot,
  Brain,
  Code,
  FileText,
  Globe,
  Layers,
  Sparkles,
  Type,
} from "lucide-react";

const PIPELINE = [
  { icon: Globe, title: "1. You enter a URL", text: "You paste the address of a publicly accessible webpage, e.g. https://example.com/article." },
  { icon: Bot, title: "2. Backend fetches the page", text: "The server sends an HTTP GET request with requests.get() and downloads the HTML of the page." },
  { icon: Code, title: "3. BeautifulSoup extracts text", text: "BeautifulSoup parses the HTML and removes scripts, styles, navigation and footers, keeping the readable article text." },
  { icon: FileText, title: "4. Text cleaning", text: "Boilerplate (cookies, 'read more', etc.) and extra whitespace are removed." },
  { icon: Type, title: "5. NLP preprocessing", text: "Lowercasing, URL removal, tokenization, conservative stopword removal (negations kept) and optional stemming — exactly as in training." },
  { icon: Layers, title: "6. TF-IDF", text: "The SAVED TF-IDF vectorizer (fitted only on training data) converts the text into numeric features. It is not re-fitted." },
  { icon: Brain, title: "7. Logistic Regression", text: "The saved model predicts the sentiment class of each text chunk." },
  { icon: Sparkles, title: "8. Aggregate to page sentiment", text: "Chunk predictions are combined into an overall sentiment and a percentage distribution." },
  { icon: BarChart3, title: "9. Dashboard", text: "Every analysis is stored in PostgreSQL and shown in your history and dashboard." },
];

export default function HowItWorksPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">How It Works</h1>
        <p className="text-sm text-slate-500">
          From a webpage URL to a sentiment result — explained step by step.
        </p>
      </div>

      <div className="card p-5">
        <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          Sentiment analysis decides whether text expresses a <strong>positive</strong>, <strong>negative</strong>,
          <strong> neutral</strong> or <strong>irrelevant</strong> opinion. This project goes one step further: instead
          of asking you to copy and paste text, it <strong>scrapes a webpage</strong>, extracts the readable content,
          and runs it through a machine learning model trained on real labelled data.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {PIPELINE.map((step, i) => (
          <div key={step.title} className="card relative p-5">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300">
              <step.icon className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-slate-900 dark:text-white">{step.title}</h3>
            <p className="mt-1.5 text-sm text-slate-500">{step.text}</p>
            {i < PIPELINE.length - 1 && (
              <ArrowDown className="absolute -bottom-3 left-1/2 hidden h-5 w-5 -translate-x-1/2 text-slate-200 lg:block dark:text-slate-700" />
            )}
          </div>
        ))}
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-slate-900 dark:text-white">Why we chunk the page</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          The model was trained on short texts (tweets). Classifying an entire long article as one bundle would hurt
          accuracy. So the extracted text is split into short chunks, each chunk is classified, and the results are
          combined into an overall sentiment plus a distribution (e.g. Positive 65%, Negative 20%, Neutral 15%).
        </p>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-slate-900 dark:text-white">Why Logistic Regression?</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          Logistic Regression is fast, interpretable and works very well with TF-IDF features for text classification.
          It also gives calibrated probabilities, which we report as <strong>model confidence</strong>. We compared it
          against Multinomial Naive Bayes during training and selected the better model by macro F1.
        </p>
        <div className="mt-4 flex gap-3">
          <Link to="/analyze" className="btn-primary">
            Analyze a webpage
          </Link>
          <Link to="/model-insights" className="btn-secondary">
            See model performance
          </Link>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-slate-900 dark:text-white">Honest limitations</h2>
        <ul className="mt-2 space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
          <li>• Only publicly accessible pages work; some websites block automated requests (handled gracefully).</li>
          <li>• Pages that load content with JavaScript may have little readable HTML text.</li>
          <li>• Factual or informational pages usually get “Neutral” — that is expected, not a bug.</li>
          <li>• Sarcasm and mixed opinions remain difficult for classical models.</li>
        </ul>
      </div>
    </div>
  );
}
