import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listReviews, deleteReview } from "../services/api";
import ScoreBadge from "../components/ScoreBadge.jsx";

export default function Dashboard() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [uploadType, setUploadType] = useState("");
  const [sort, setSort] = useState("newest");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const params = { sort };
      if (search) params.search = search;
      if (uploadType) params.upload_type = uploadType;
      const res = await listReviews(params);
      setReviews(res.data.reviews);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sort]);

  const handleSearch = (e) => {
    e.preventDefault();
    load();
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this review permanently?")) return;
    try {
      await deleteReview(id);
      setReviews((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      alert(err.response?.data?.error || "Delete failed");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Review Dashboard</h1>
        <Link to="/submit" className="btn-primary">
          + New Review
        </Link>
      </div>

      <form onSubmit={handleSearch} className="flex flex-wrap gap-3 mb-6">
        <input
          className="input max-w-xs"
          placeholder="Search by project name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input max-w-[10rem]" value={uploadType} onChange={(e) => setUploadType(e.target.value)}>
          <option value="">All types</option>
          <option value="file">File upload</option>
          <option value="snippet">Snippet</option>
          <option value="github">GitHub repo</option>
        </select>
        <select className="input max-w-[10rem]" value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="score">Highest score</option>
        </select>
        <button className="btn-secondary">Filter</button>
      </form>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      {loading ? (
        <p>Loading...</p>
      ) : reviews.length === 0 ? (
        <p className="text-gray-500">No reviews yet. Submit code to get started.</p>
      ) : (
        <div className="grid gap-4">
          {reviews.map((r) => (
            <div key={r.id} className="card p-4 flex items-center justify-between">
              <div>
                <Link to={`/reviews/${r.id}`} className="font-semibold text-brand-600 hover:underline">
                  {r.project_name}
                </Link>
                <p className="text-xs text-gray-500 mt-1">{new Date(r.created_at).toLocaleString()}</p>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2 max-w-xl">{r.summary}</p>
              </div>
              <div className="flex items-center gap-3">
                <ScoreBadge score={r.review_score} />
                <button onClick={() => handleDelete(r.id)} className="text-red-600 text-sm hover:underline">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
