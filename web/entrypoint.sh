#!/bin/sh
set -eu

REPO_URL="${GIT_REPO_URL:-}"
REPO_BRANCH="${GIT_REPO_BRANCH:-main}"

SRC_DIR="/opt/source"
CACHE_DIR="/opt/cache"
APP_DIR="/app"

WEB_SRC_REL="${WEB_SRC_REL:-web}"

log() {
  echo "[entrypoint] $*"
}

copy_web_dir() {
  SRC_BASE="$1"

  rm -rf "$APP_DIR"
  mkdir -p "$APP_DIR"

  cp -r "$SRC_BASE/$WEB_SRC_REL/." "$APP_DIR/"
}

copy_from_source() {
  copy_web_dir "$SRC_DIR"
}

copy_from_cache() {
  copy_web_dir "$CACHE_DIR"
}

save_cache() {
  rm -rf "$CACHE_DIR"
  mkdir -p "$CACHE_DIR"
  cp -r "$APP_DIR/." "$CACHE_DIR/"
}

have_cache() {
  [ -f "$CACHE_DIR/app.py" ]
}

update_from_git() {
  [ -n "$REPO_URL" ] || return 1

  if [ ! -d "$SRC_DIR/.git" ]; then
    rm -rf "$SRC_DIR"
    git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$SRC_DIR"
  else
    cd "$SRC_DIR"
    git fetch origin "$REPO_BRANCH"
    git reset --hard "origin/$REPO_BRANCH"
  fi

  [ -d "$SRC_DIR/$WEB_SRC_REL" ]
  [ -f "$SRC_DIR/$WEB_SRC_REL/app.py" ]
}

log "Iniciando actualización de código"

UPDATED=0

if update_from_git; then
  log "Código actualizado desde GitHub"
  copy_from_source
  save_cache
  UPDATED=1
else
  log "No se pudo actualizar desde GitHub"
fi

if [ "$UPDATED" -eq 0 ]; then
  if have_cache; then
    log "Usando última versión local en caché"
    copy_from_cache
  else
    log "ERROR: no hay internet y no existe caché local"
    exit 1
  fi
fi

log "Arrancando aplicación"
exec python /app/app.py