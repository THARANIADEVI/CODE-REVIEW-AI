"""Fetches source files from a public GitHub repository via the REST API
(no auth required for public repos). Used for the "paste a GitHub repo URL"
submission path described in the project intro."""
import re
import urllib.request
import json
import base64

from utils.file_utils import is_allowed_file, is_ignored_path

GITHUB_API = "https://api.github.com"
MAX_FILES = 25
MAX_FILE_SIZE = 200_000  # bytes


class GitHubFetchError(Exception):
    pass


def parse_repo_url(url: str):
    match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    if not match:
        raise GitHubFetchError("Invalid GitHub repository URL")
    return match.group(1), match.group(2)


def _get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                 "User-Agent": "ai-code-review-assistant"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_repo_files(repo_url: str) -> list:
    owner, repo = parse_repo_url(repo_url)
    try:
        repo_info = _get(f"{GITHUB_API}/repos/{owner}/{repo}")
        default_branch = repo_info.get("default_branch", "main")
        tree = _get(f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1")
    except Exception as exc:
        raise GitHubFetchError(f"Could not reach GitHub repository: {exc}") from exc

    candidates = [
        item for item in tree.get("tree", [])
        if item.get("type") == "blob"
        and is_allowed_file(item["path"])
        and not is_ignored_path(item["path"])
        and item.get("size", 0) <= MAX_FILE_SIZE
    ][:MAX_FILES]

    files = []
    for item in candidates:
        try:
            blob = _get(f"{GITHUB_API}/repos/{owner}/{repo}/git/blobs/{item['sha']}")
            content = base64.b64decode(blob["content"]).decode("utf-8", errors="ignore")
            files.append({"filename": item["path"], "content": content})
        except Exception:
            continue

    if not files:
        raise GitHubFetchError("No supported source files found in repository")
    return files
