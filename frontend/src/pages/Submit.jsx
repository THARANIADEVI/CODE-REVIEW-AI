import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { useTheme } from "../context/ThemeContext.jsx";
import { uploadFiles, uploadSnippet, uploadGithubRepo } from "../services/api";

const MONACO_LANGUAGE_BY_EXT = {
  py: "python",
  js: "javascript",
  jsx: "javascript",
  ts: "typescript",
  tsx: "typescript",
};

function monacoLanguageFor(filename) {
  const ext = filename.trim().split(".").pop()?.toLowerCase();
  return MONACO_LANGUAGE_BY_EXT[ext] || "plaintext";
}

const TABS = [
  { key: "files", label: "Upload Files" },
  { key: "snippet", label: "Paste Snippet" },
  { key: "github", label: "GitHub Repo URL" },
];

export default function Submit() {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [tab, setTab] = useState("files");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [projectName, setProjectName] = useState("");
  const [files, setFiles] = useState([]);
  const [snippetFilename, setSnippetFilename] = useState("snippet.py");
  const [snippetCode, setSnippetCode] = useState("");
  const [repoUrl, setRepoUrl] = useState("");

  const goToReview = (review) => navigate(`/reviews/${review.id}`);

  const submitFiles = async (e) => {
    e.preventDefault();
    if (!files.length) return setError("Choose at least one file");
    setBusy(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("project_name", projectName || "Untitled Upload");
      files.forEach((f) => formData.append("files", f));
      const res = await uploadFiles(formData);
      goToReview(res.data.review);
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const submitSnippet = async (e) => {
    e.preventDefault();
    if (!snippetCode.trim()) return setError("Paste some code first");
    setBusy(true);
    setError("");
    try {
      const res = await uploadSnippet({
        project_name: projectName || "Untitled Snippet",
        filename: snippetFilename,
        code: snippetCode,
      });
      goToReview(res.data.review);
    } catch (err) {
      setError(err.response?.data?.error || "Review failed");
    } finally {
      setBusy(false);
    }
  };

  const submitGithub = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return setError("Enter a public GitHub repo URL");
    setBusy(true);
    setError("");
    try {
      const res = await uploadGithubRepo({ repo_url: repoUrl });
      goToReview(res.data.review);
    } catch (err) {
      setError(err.response?.data?.error || "GitHub fetch failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">New Code Review</h1>
      <div className="flex gap-2 mb-6">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => {
              setTab(t.key);
              setError("");
            }}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              tab === t.key ? "bg-brand-600 text-white" : "btn-secondary"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

      <div className="card p-6">
        <input
          className="input mb-4"
          placeholder="Project name (optional)"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
        />

        {tab === "files" && (
          <form onSubmit={submitFiles} className="space-y-4">
            <input
              type="file"
              multiple
              accept=".py,.js,.jsx,.ts,.tsx"
              onChange={(e) => setFiles(Array.from(e.target.files))}
              className="block w-full text-sm"
            />
            <p className="text-xs text-gray-500">
              Supports .py, .js, .jsx, .ts, .tsx. Binaries/images/dependency folders are ignored.
            </p>
            <button className="btn-primary" disabled={busy}>
              {busy ? "Analyzing..." : "Upload & Analyze"}
            </button>
          </form>
        )}

        {tab === "snippet" && (
          <form onSubmit={submitSnippet} className="space-y-4">
            <input
              className="input"
              placeholder="Filename (e.g. main.py)"
              value={snippetFilename}
              onChange={(e) => setSnippetFilename(e.target.value)}
            />
            <div className="rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
              <Editor
                height="320px"
                language={monacoLanguageFor(snippetFilename)}
                theme={theme === "dark" ? "vs-dark" : "light"}
                value={snippetCode}
                onChange={(value) => setSnippetCode(value || "")}
                options={{ minimap: { enabled: false }, fontSize: 13, automaticLayout: true }}
              />
            </div>
            <button className="btn-primary" disabled={busy}>
              {busy ? "Analyzing..." : "Analyze Snippet"}
            </button>
          </form>
        )}

        {tab === "github" && (
          <form onSubmit={submitGithub} className="space-y-4">
            <input
              className="input"
              placeholder="https://github.com/owner/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
            />
            <p className="text-xs text-gray-500">Public repositories only, up to 25 source files.</p>
            <button className="btn-primary" disabled={busy}>
              {busy ? "Fetching & Analyzing..." : "Analyze Repository"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
