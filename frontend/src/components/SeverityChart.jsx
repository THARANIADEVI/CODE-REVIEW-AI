import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const ORDER = ["critical", "high", "medium", "low", "info"];
const COLORS = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#2563eb",
  info: "#6b7280",
};

export default function SeverityChart({ findings }) {
  const counts = ORDER.map((s) => findings.filter((f) => f.severity === s).length);

  const data = {
    labels: ORDER.map((s) => s[0].toUpperCase() + s.slice(1)),
    datasets: [
      {
        label: "Findings by severity",
        data: counts,
        backgroundColor: ORDER.map((s) => COLORS[s]),
        borderRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
  };

  return <Bar data={data} options={options} />;
}
