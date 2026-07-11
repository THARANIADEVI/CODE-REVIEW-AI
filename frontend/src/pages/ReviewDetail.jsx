import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getReview, downloadReport } from "../services/api";
import ScoreBadge from "../components/ScoreBadge.jsx";
import SeverityBadge from "../components/SeverityBadge.jsx";
import SeverityChart from "../components/SeverityChart.jsx";

const METRIC_LABELS = {
  total_lines_of_code: "Total Lines of Code",
  num_functions: "Number of Functions",
  num_classes: "Number of Classes",
  average_cyclomatic_complexity: "Avg. Cyclomatic Complexity",
  maintainability_index: "Maintainability Index",
  average_function_length: "Avg. Function Length",
};

export default function ReviewDetail() {
  const { id } = useParams();
  const [review, setReview] = useState(null);
  const [error, setError] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [exporting, setExporting] = useState("");

  const load = async () => {
    try {
      const params = severityFilter ? { severity: severityFilter } : {};
      const res = await getReview(id, params);
      setReview(res.data.review);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to load review");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, severityFilter]);

  const handleExport = async (format) => {
    setExporting(format);
    try {
      const res = await downloadReport(id, format);
      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `review_${id}.${format === "markdown" ? "md" : format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Export failed");
    } finally {
      setExporting("");
    }
  };

  if (error) return <p className="text-red-600">{error}</p>;
  if (!review) return <p>Loading...</p>;

  const metrics = review.metrics || {};
  const docFiles = review.documentation?.files || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold">{review.project_name}</h1>
          <p className="text-xs text-gray-500">{new Date(review.created_at).toLocaleString()}</p>
        </div>
        <div className="flex items-center gap-3">
          <ScoreBadge score={review.review_score} />
          <button className="btn-secondary" disabled={exporting === "pdf"} onClick={() => handleExport("pdf")}>
            {exporting === "pdf" ? "Exporting..." : "Export PDF"}
          </button>
          <button className="btn-secondary" disabled={exporting === "markdown"} onClick={() => handleExport("markdown")}>
            {exporting === "markdown" ? "Exporting..." : "Export Markdown"}
          </button>
          <button className="btn-secondary" disabled={exporting === "html"} onClick={() => handleExport("html")}>
            {exporting === "html" ? "Exporting..." : "Export HTML"}
          </button>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-2">Summary</h2>
        <p className="text-sm text-gray-700 dark:text-gray-300">{review.summary}</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Complexity Analysis</h2>
          <dl className="grid grid-cols-2 gap-y-3 text-sm">
            {Object.entries(METRIC_LABELS).map(([key, label]) => (
              <div key={key}>
                <dt className="text-gray-500">{label}</dt>
                <dd className="font-medium">{metrics[key] ?? "—"}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Findings by Severity</h2>
          <SeverityChart findings={review.findings || []} />
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">
            Findings ({(review.findings || []).length})
          </h2>
          <select className="input max-w-[10rem]" value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
        </div>
        <div className="space-y-3">
          {(review.findings || []).length === 0 && <p className="text-gray-500 text-sm">No findings.</p>}
          {(review.findings || []).map((f) => (
            <div key={f.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <SeverityBadge severity={f.severity} />
                <span className="badge bg-gray-100 text-gray-600">{f.category}</span>
                <span className="badge bg-gray-100 text-gray-600">{f.source}</span>
                <span className="font-medium">{f.issue}</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300">{f.explanation}</p>
              {f.suggestion && (
                <p className="text-sm text-brand-600 mt-1">
                  <strong>Suggestion:</strong> {f.suggestion}
                </p>
              )}
              <p className="text-xs text-gray-400 mt-1">
                {f.file_name}
                {f.line_number ? `:${f.line_number}` : ""}
              </p>
            </div>
          ))}
        </div>
      </div>

      {docFiles.length > 0 && (
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Generated Documentation</h2>
          {docFiles.map((doc, idx) => (
            <div key={idx} className="mb-4">
              <h3 className="font-mono text-sm font-semibold">{doc.filename}</h3>
              {doc.documentation?.module && (
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{doc.documentation.module}</p>
              )}
              {doc.documentation?.classes?.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs uppercase text-gray-400 font-semibold">Classes</p>
                  <ul className="text-sm list-disc list-inside">
                    {doc.documentation.classes.map((c) => (
                      <li key={c.name}>
                        <code>{c.name}</code> — {c.docstring}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {doc.documentation?.functions?.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs uppercase text-gray-400 font-semibold">Functions</p>
                  <ul className="text-sm list-disc list-inside">
                    {doc.documentation.functions.map((f) => (
                      <li key={f.name + f.line_number}>
                        <code>
                          {f.name}({f.args.join(", ")})
                        </code>{" "}
                        — {f.docstring}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
