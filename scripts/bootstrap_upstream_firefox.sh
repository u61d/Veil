#!/usr/bin/env bash
set -euo pipefail

repo_url="${VEIL_UPSTREAM_REPO:-https://github.com/mozilla-firefox/firefox}"
checkout_dir="${1:-upstream/firefox}"
ref="${2:-main}"
method="${VEIL_UPSTREAM_METHOD:-archive}"

mkdir -p "$(dirname "$checkout_dir")"

resolve_ref_sha() {
  git ls-remote "$repo_url" "refs/heads/$ref" | awk '{print $1}'
}

write_metadata() {
  python3 - <<'PY' "$checkout_dir" "$method" "$repo_url" "$ref" "$1" "$2" "$3"
import json
import sys
from pathlib import Path

checkout_dir, method, repo_url, ref, commit, archive_name, source_dir = sys.argv[1:]
meta = {
    "method": method,
    "repository": repo_url,
    "ref": f"refs/heads/{ref}",
    "commit": commit,
    "archive": archive_name or None,
    "source_dir": source_dir or Path(checkout_dir).name,
}
Path(Path(checkout_dir).parent / "upstream-source.json").write_text(
    json.dumps(meta, indent=2) + "\n",
    encoding="utf-8",
)
PY
}

bootstrap_archive() {
  local checkout_parent archive_name archive_path commit source_dir source_name

  checkout_parent="$(dirname "$checkout_dir")"
  commit="$(resolve_ref_sha)"
  archive_name="firefox-${commit}.tar.gz"
  archive_path="${checkout_parent}/${archive_name}"
  source_name="firefox-${commit}"
  source_dir="${checkout_parent}/${source_name}"

  if [[ ! -f "$archive_path" ]]; then
    curl -L --fail \
      --output "$archive_path" \
      "https://codeload.github.com/mozilla-firefox/firefox/tar.gz/${commit}"
  fi

  if [[ ! -d "$source_dir" ]]; then
    tar -xzf "$archive_path" -C "$checkout_parent"
  fi

  if [[ -e "$checkout_dir" && ! -L "$checkout_dir" ]]; then
    printf 'Refusing to replace existing non-symlink path: %s\n' "$checkout_dir" >&2
    exit 1
  fi

  ln -sfn "$source_name" "$checkout_dir"
  write_metadata "$commit" "$archive_name" "$source_name"
  printf 'Upstream archive checkout ready at %s (commit %s)\n' "$checkout_dir" "$commit"
}

bootstrap_git() {
  local commit

  if [[ -d "$checkout_dir/.git" ]]; then
    git -C "$checkout_dir" remote set-url origin "$repo_url"
    git -C "$checkout_dir" fetch --depth 1 origin "$ref"
  else
    git clone \
      --depth 1 \
      --branch "$ref" \
      --single-branch \
      "$repo_url" \
      "$checkout_dir"
  fi

  if git -C "$checkout_dir" show-ref --verify --quiet "refs/remotes/origin/$ref"; then
    git -C "$checkout_dir" checkout -B veil-base "origin/$ref"
  else
    git -C "$checkout_dir" checkout --detach FETCH_HEAD
  fi

  commit="$(git -C "$checkout_dir" rev-parse HEAD)"
  write_metadata "$commit" "" ""
  printf 'Upstream git checkout ready at %s (commit %s)\n' "$checkout_dir" "$commit"
}

case "$method" in
  archive)
    bootstrap_archive
    ;;
  git)
    bootstrap_git
    ;;
  *)
    printf 'Unsupported VEIL_UPSTREAM_METHOD: %s\n' "$method" >&2
    exit 1
    ;;
esac
