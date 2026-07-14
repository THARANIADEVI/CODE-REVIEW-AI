import { useEffect, useState } from "react";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";
import { getAnalytics } from "../services/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend);

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];
const SEVERITY_COLORS = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#2563eb",
  info: "#6b7280",
};

export default function Analytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAnalytics()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load analytics"));
  }, []);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return <p>Loading...</p>;

  if (data.total_reviews === 0) {
    return <p className="text-gray-500">No reviews yet. Submit code to see analytics here.</p>;
  }

  const trendData = {
    labels: data.score_trend.map((t) => new Date(t.created_at).toLocaleDateString()),
    datasets: [
      {
        label: "Review score",
        data: data.score_trend.map((t) => t.score),
        borderColor: "#2563eb",
        backgroundColor: "#2563eb33",
        tension: 0.3,
      },
    ],
  };

  const severityData = {
    labels: SEVERITY_ORDER.map((s) => s[0].toUpperCase() + s.slice(1)),
    datasets: [
      {
        label: "Findings",
        data: SEVERITY_ORDER.map((s) => data.severity_totals[s] || 0),
        backgroundColor: SEVERITY_ORDER.map((s) => SEVERITY_COLORS[s]),
        borderRadius: 6,
      },
    ],
  };

  const categoryLabels = Object.keys(data.category_totals);
  const categoryData = {
    labels: categoryLabels.map((c) => c.replace("_", " ")),
    datasets: [
      {
        label: "Findings by category",
        data: categoryLabels.map((c) => data.category_totals[c]),
        backgroundColor: "#3b82f6",
        borderRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Repository Analytics</h1>

      <div className="grid sm:grid-cols-3 gap-4">
        <div className="card p-6 text-center">
          <p className="text-3xl font-bold text-brand-600">{data.total_reviews}</p>
          <p className="text-sm text-gray-500 mt-1">Total Reviews</p>
        </div>
        <div className="card p-6 text-center">
          <p className="text-3xl font-bold text-brand-600">{data.avg_score}</p>
          <p className="text-sm text-gray-500 mt-1">Average Score</p>
        </div>
        <div className="card p-6 text-center">
          <p className="text-3xl font-bold text-brand-600">{data.total_findings}</p>
          <p className="text-sm text-gray-500 mt-1">Total Findings</p>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-4">Score Trend</h2>
        <Line data={trendData} options={chartOptions} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Findings by Severity</h2>
          <Bar data={severityData} options={chartOptions} />
        </div>
        <div className="card p-6">
          <h2 className="font-semibold mb-4">Findings by Category</h2>
          <Bar data={categoryData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}
