import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listWorkspaces, createWorkspace } from "../services/api";

export default function Workspaces() {
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await listWorkspaces();
      setWorkspaces(res.data.workspaces);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateError("");
    if (!name.trim()) return;
    setCreating(true);
    try {
      await createWorkspace({ name: name.trim() });
      setName("");
      setShowCreate(false);
      load();
    } catch (err) {
      setCreateError(err.response?.data?.error || "Failed to create workspace");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Team Workspaces</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + Create Workspace
        </button>
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : workspaces.length === 0 ? (
        <p className="text-gray-500">No workspaces yet. Create one to start collaborating.</p>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((w) => (
            <div
              key={w.id}
              className="card p-4 cursor-pointer hover:shadow-md transition"
              onClick={() => navigate(`/workspaces/${w.id}`)}
            >
              <p className="font-semibold text-brand-600">{w.name}</p>
              <p className="text-xs text-gray-500 mt-1">
                {w.member_count} member{w.member_count === 1 ? "" : "s"}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Created {new Date(w.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-sm bg-white dark:bg-gray-800">
            <h2 className="font-semibold text-lg mb-4">Create Workspace</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                className="input w-full"
                placeholder="Workspace name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
              {createError && <p className="text-red-600 text-sm">{createError}</p>}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setShowCreate(false);
                    setCreateError("");
                    setName("");
                  }}
                >
                  Cancel
                </button>
                <button className="btn-primary" disabled={creating}>
                  {creating ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
