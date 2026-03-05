#!/usr/bin/env bash
set -euo pipefail

repo_input="${1:-}"
branch="${2:-main}"
visibility="${VISIBILITY:-public}" # public|private
default_repo="$(basename "$PWD")"
workspace_root="$(cd "$(dirname "$0")/.." && pwd)"

sync_from_zero_docs_if_exists() {
  local src_dir="${workspace_root}/from_zero"
  local dst_dir="${workspace_root}/zcprotobuf/docs/from_zero"

  if [[ ! -d "$src_dir" ]]; then
    return 0
  fi

  mkdir -p "$dst_dir"
  cp "${src_dir}/ZCPROTOBUF_FROM_ZERO.md" "${dst_dir}/ZCPROTOBUF_FROM_ZERO.md"
  cp "${src_dir}/README.md" "${dst_dir}/README.md"
}

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI not found. Install GitHub CLI first."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: gh is not logged in. Run: gh auth login"
  exit 1
fi

if [[ ! -d .git ]]; then
  git init
fi

sync_from_zero_docs_if_exists

git add .
if ! git diff --cached --quiet; then
  git commit -m "chore: auto publish update"
fi

git branch -M "$branch"

owner="$(gh api user -q .login)"

if [[ -z "$repo_input" ]]; then
  full_repo="${owner}/${default_repo}"
elif [[ "$repo_input" == http*://github.com/* ]]; then
  full_repo="$(echo "$repo_input" | sed -E 's#https?://github.com/##; s#\.git$##')"
elif [[ "$repo_input" == */* ]]; then
  full_repo="$repo_input"
else
  full_repo="${owner}/${repo_input}"
fi

repo_url="https://github.com/${full_repo}.git"

if ! gh repo view "$full_repo" >/dev/null 2>&1; then
  gh repo create "$full_repo" "--${visibility}" --source=. --remote=origin
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$repo_url"
else
  git remote add origin "$repo_url"
fi

git push -u origin "$branch"
echo "Pushed: $full_repo ($branch)"
