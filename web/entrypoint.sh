#!/bin/sh
set -eu

REPO_URL="${GIT_REPO_URL:-}"
REPO_BRANCH="${GIT_REPO_BRANCH:-main}"

SRC_DIR="/opt/source"
CACHE_DIR="/opt/cache"
APP_DIR="/app"

APP_SRC_REL="${APP_SRC_REL:-web/app.py}"
HTML_SRC_REL="${HTML_SRC_REL:-web/templates/index.html}"

log() {
  echo "[entrypoint] $*"
}

copy_from_source() {
  mkdir -p "$APP_DIR/templates"
  cp "$SRC_DIR/$APP_SRC_REL" "$APP_DIR/app.py"
  cp "$SRC_DIR/$HTML_SRC_REL" "$APP_DIR/templates/index.html"
}

copy_from_cache() {
  mkdir -p "$APP_DIR/templates"
  cp "$CACHE_DIR/app.py" "$APP_DIR/app.py"
  cp "$CACHE_DIR/index.html" "$APP_DIR/templates/index.html"
}

save_cache() {
  mkdir -p "$CACHE_DIR"
  cp "$APP_DIR/app.py" "$CACHE_DIR/app.py"
  cp "$APP_DIR/templates/index.html" "$CACHE_DIR/index.html"
}

have_cache() {
  [ -f "$CACHE_DIR/app.py" ] && [ -f "$CACHE_DIR/index.html" ]
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

  [ -f "$SRC_DIR/$APP_SRC_REL" ]
  [ -f "$SRC_DIR/$HTML_SRC_REL" ]
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