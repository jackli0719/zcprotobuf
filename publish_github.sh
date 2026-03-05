#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <github_repo_url> [branch]"
  echo "Example: $0 https://github.com/your-account/zcprotobuf.git main"
  exit 1
fi

repo_url="$1"
branch="${2:-main}"

if [[ ! -d .git ]]; then
  git init
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "init zcprotobuf project"
fi

git branch -M "$branch"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$repo_url"
else
  git remote add origin "$repo_url"
fi

git push -u origin "$branch"

echo "Pushed to $repo_url on branch $branch"
