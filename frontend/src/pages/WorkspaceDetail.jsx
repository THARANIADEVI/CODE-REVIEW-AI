import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import {
  getWorkspace,
  inviteWorkspaceMember,
  removeWorkspaceMember,
  getWorkspaceProjects,
} from "../services/api";

export default function WorkspaceDetail() {
  const { id } = useParams();
  const { user } = useAuth();

  const [workspace, setWorkspace] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [wsRes, projectsRes] = await Promise.all([
        getWorkspace(id),
        getWorkspaceProjects(id),
      ]);
      setWorkspace(wsRes.data.workspace);
      setProjects(projectsRes.data.projects);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to load workspace");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!workspace) return null;

  const myMembership = workspace.members.find((m) => m.user_id === user?.id);
  const canManage = myMembership && (myMembership.role === "owner" || myMembership.role === "admin");

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteError("");
    if (!email.trim()) return;
    setInviting(true);
    try {
      await inviteWorkspaceMember(id, { email: email.trim() });
      setEmail("");
      load();
    } catch (err) {
      setInviteError(err.response?.data?.error || "Failed to invite member");
    } finally {
      setInviting(false);
    }
  };

  const handleRemove = async (memberUserId, isSelf) => {
    const msg = isSelf ? "Leave this workspace?" : "Remove this member from the workspace?";
    if (!window.confirm(msg)) return;
    try {
      await removeWorkspaceMember(id, memberUserId);
      load();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to remove member");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{workspace.name}</h1>
          <p className="text-xs text-gray-500 mt-1">
            Created {new Date(workspace.created_at).toLocaleDateString()}
          </p>
        </div>
        <Link to="/workspaces" className="text-sm text-brand-600 hover:underline">
          &larr; Back to Workspaces
        </Link>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-4">Members</h2>
        <div className="space-y-2">
          {workspace.members.map((m) => {
            const isSelf = m.user_id === user?.id;
            const canRemove = isSelf ? m.role !== "owner" : canManage && m.role !== "owner";
            return (
              <div
                key={m.id}
                className="flex items-center justify-between py-2 border-t border-gray-200 dark:border-gray-700 first:border-t-0"
              >
                <div>
                  <p className="text-sm font-medium">
                    {m.user?.name} {isSelf && <span className="text-gray-400">(you)</span>}
                  </p>
                  <p className="text-xs text-gray-500">{m.user?.email}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs uppercase tracking-wide text-gray-500">{m.role}</span>
                  {canRemove && (
                    <button
                      onClick={() => handleRemove(m.user_id, isSelf)}
                      className="text-red-600 text-sm hover:underline"
                    >
                      {isSelf ? "Leave" : "Remove"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {canManage && (
          <form onSubmit={handleInvite} className="flex flex-wrap gap-3 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <input
              className="input max-w-xs"
              type="email"
              placeholder="Invite by email..."
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <button className="btn-primary" disabled={inviting}>
              {inviting ? "Inviting..." : "Invite"}
            </button>
            {inviteError && <p className="text-red-600 text-sm w-full">{inviteError}</p>}
          </form>
        )}
      </div>

      <div className="card p-6">
        <h2 className="font-semibold mb-4">Projects</h2>
        {projects.length === 0 ? (
          <p className="text-gray-500 text-sm">No projects in this workspace yet.</p>
        ) : (
          <div className="space-y-2">
            {projects.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between py-2 border-t border-gray-200 dark:border-gray-700 first:border-t-0"
              >
                <div>
                  <p className="text-sm font-medium">{p.project_name}</p>
                  <p className="text-xs text-gray-500">{new Date(p.created_at).toLocaleString()}</p>
                </div>
                {p.reviews && p.reviews[0] ? (
                  <Link to={`/reviews/${p.reviews[0].id}`} className="text-sm text-brand-600 hover:underline">
                    View Review
                  </Link>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
