const COLORS = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
  info: "bg-gray-100 text-gray-700",
};

export default function SeverityBadge({ severity }) {
  const cls = COLORS[severity] || COLORS.info;
  return <span className={`badge ${cls}`}>{severity}</span>;
}
