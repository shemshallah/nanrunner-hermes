#!/usr/bin/env bash
# Restore pinned pre-installed Hermes from this repository's versioned release.
# No API keys are accepted or read by this script.
set -euo pipefail

PIN="2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19"
TAG="hermes-runtime-v0.23.0-ubuntu2404-x64-2bd378ed1b8d"
ARCHIVE="hermes-ubuntu2404-x64-2bd378ed1b8d.tar.zst"
REPOSITORY="shemshallah/nanrunner-hermes"
MARKER="$HOME/.hermes/.nanrunner-hermes-runtime-pin"
INSTALLER="https://raw.githubusercontent.com/NousResearch/hermes-agent/$PIN/scripts/install.sh"
RELEASE="https://github.com/$REPOSITORY/releases/download/$TAG"
MODE="$1"

require_target() {
  local os_id os_version
  if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
    echo "ERROR: prebuilt Hermes requires Linux x86-64" >&2; exit 2
  fi
  os_id="$(. /etc/os-release; printf '%s' "$ID")"
  os_version="$(. /etc/os-release; printf '%s' "$VERSION_ID")"
  if [[ "$os_id" != ubuntu || "$os_version" != 24.04 ]]; then
    echo "ERROR: prebuilt Hermes requires Ubuntu 24.04" >&2; exit 2
  fi
}

has_pinned_runtime() {
  [[ -f "$MARKER" && "$(cat "$MARKER")" == "$PIN" ]] &&
  [[ -x "$HOME/.local/bin/hermes" ]] &&
  "$HOME/.local/bin/hermes" --help >/dev/null 2>&1
}

publish_path() {
  if [[ -n "$(printenv GITHUB_PATH 2>/dev/null || true)" ]]; then
    echo "$HOME/.local/bin" >> "$GITHUB_PATH"
  fi
  export PATH="$HOME/.local/bin:$PATH"
}

install_from_pin() {
  local tmp
  tmp="$(mktemp -d)"
  echo "Installing Hermes at pinned upstream commit $PIN (no cloud secrets)"
  curl -fsSL --retry 3 --connect-timeout 15 "$INSTALLER" -o "$tmp/install.sh"
  bash "$tmp/install.sh" --commit "$PIN" --channel main --non-interactive --skip-browser --skip-computer-use
  rm -rf "$tmp"
  mkdir -p "$HOME/.hermes"
  printf '%s\n' "$PIN" > "$MARKER"
  publish_path
  if ! has_pinned_runtime; then
    echo "ERROR: pinned Hermes installation failed executable validation" >&2; exit 1
  fi
  echo "PASS: pinned Hermes installed"
}

restore_from_release() {
  local tmp="$1"
  curl -fLsS --retry 3 --connect-timeout 15 --max-time 600 "$RELEASE/$ARCHIVE" -o "$tmp/$ARCHIVE"
  (cd "$tmp" && sha256sum -c "$ARCHIVE.sha256")
  tar --zstd -xf "$tmp/$ARCHIVE" -C "$HOME"
  publish_path
  if ! has_pinned_runtime; then
    echo "ERROR: prebuilt runtime failed pin/executable validation" >&2; exit 1
  fi
  echo "PASS: Hermes pre-installed runtime restored from repository release"
}

make_bundle() {
  if ! has_pinned_runtime; then
    echo "ERROR: no pinned Hermes to package" >&2; exit 1
  fi
  command -v zstd >/dev/null || { echo "ERROR: missing zstd" >&2; exit 1; }
  mkdir -p dist
  (
    cd "$HOME"
    tar --zstd -cf "$GITHUB_WORKSPACE/dist/$ARCHIVE" \
      --exclude='.hermes/cache' \
      --exclude='.hermes/logs' \
      --exclude='.hermes/telemetry' \
      --exclude='.hermes/sessions' \
      --exclude='.hermes/memories' \
      --exclude='.hermes/credentials' \
      --exclude='.hermes/credentials.*' \
      --exclude='.hermes/secrets' \
      --exclude='.hermes/.env' \
      --exclude='.hermes/config.json' \
      --exclude='.hermes/config.yaml' \
      .hermes .local/bin/hermes
  )
  (
    cd dist
    sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
    sha256sum -c "$ARCHIVE.sha256"
  )
  if (( $(stat -c %s "dist/$ARCHIVE") >= 1900000000 )); then
    echo "ERROR: runtime bundle exceeds safe Release asset size" >&2; exit 1
  fi
  ls -lh "dist/$ARCHIVE" "dist/$ARCHIVE.sha256"
  echo "PASS: SHA-256 verified pre-installed Hermes runtime bundle"
}

require_target
case "$MODE" in
  install)
    install_from_pin
    ;;
  restore)
    publish_path
    if has_pinned_runtime; then
      echo "PASS: Hermes already installed via repository Actions cache"
      exit 0
    fi
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT
    if curl -fLsS --retry 2 --connect-timeout 10 --max-time 40 \
      "$RELEASE/$ARCHIVE.sha256" -o "$tmp/$ARCHIVE.sha256"; then
      restore_from_release "$tmp"
    else
      echo "Pinned release not yet published: performing one-time bootstrap."
      install_from_pin
    fi
    ;;
  bundle)
    make_bundle
    ;;
  *)
    echo "Usage: $0 install|restore|bundle" >&2
    exit 2
    ;;
esac
