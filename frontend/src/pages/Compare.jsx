import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { compareReviews } from "../services/api";
import ScoreBadge from "../components/ScoreBadge.jsx";

const METRIC_LABELS = {
  total_lines_of_code: "Total Lines of Code",
  num_functions: "Number of Functions",
  num_classes: "Number of Classes",
  average_cyclomatic_complexity: "Avg. Cyclomatic Complexity",
  maintainability_index: "Maintainability Index",
  average_function_length: "Avg. Function Length",
};

const SEVERITIES = ["critical", "high", "medium", "low", "info"];

export default function Compare() {
  const [params] = useSearchParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const a = params.get("a");
  const b = params.get("b");

  useEffect(() => {
    if (!a || !b) return;
    compareReviews(a, b)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to compare reviews"));
  }, [a, b]);

  if (!a || !b) return <p className="text-gray-500">Select two reviews from the dashboard to compare.</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return <p>Loading...</p>;

  const { a: reviewA, b: reviewB, score_delta, metrics_diff, severity_counts } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Compare Reviews</h1>
        <Link to="/dashboard" className="text-sm text-brand-600 hover:underline">
          &larr; Back to Dashboard
        </Link>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {[reviewA, reviewB].map((r, idx) => (
          <div key={r.id} className="card p-6">
            <div className="flex items-center justify-between mb-2">
              <Link to={`/reviews/${r.id}`} className="font-semibold text-brand-600 hover:underline">
                {r.project_name}
              </Link>
              <ScoreBadge score={r.review_score} />
            </div>
            <p className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</p>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">{r.summary}</p>
            <p className="text-xs text-gray-400 mt-2">{idx === 0 ? "A" : "B"}</p>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-4">
          Score Delta:{" "}
          <span className={score_delta >= 0 ? "text-green-600" : "text-red-600"}>
            {score_delta >= 0 ? "+" : ""}
            {score_delta}
          </span>{" "}
          (B vs A)
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500">
              <th className="py-1">Metric</th>
              <th className="py-1">A</th>
              <th className="py-1">B</th>
              <th className="py-1">Delta</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics_diff).map(([key, v]) => (
              <tr key={key} className="border-t border-gray-200 dark:border-gray-700">
                <td className="py-1">{METRIC_LABELS[key] || key}</td>
                <td className="py-1">{v.a ?? "—"}</td>
                <td className="py-1">{v.b ?? "—"}</td>
                <td className={`py-1 ${v.delta > 0 ? "text-green-600" : v.delta < 0 ? "text-red-600" : ""}`}>
                  {v.delta ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-4">Findings by Severity</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500">
              <th className="py-1">Severity</th>
              <th className="py-1">A</th>
              <th className="py-1">B</th>
            </tr>
          </thead>
          <tbody>
            {SEVERITIES.map((s) => (
              <tr key={s} className="border-t border-gray-200 dark:border-gray-700">
                <td className="py-1 capitalize">{s}</td>
                <td className="py-1">{severity_counts.a[s] || 0}</td>
                <td className="py-1">{severity_counts.b[s] || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
