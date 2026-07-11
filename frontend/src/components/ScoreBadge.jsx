export default function ScoreBadge({ score }) {
  const s = Number(score) || 0;
  const color =
    s >= 80 ? "bg-green-100 text-green-700" : s >= 50 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700";
  return <span className={`badge ${color}`}>{s}/100</span>;
}
