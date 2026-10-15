#!/bin/sh
# Installe la bibliothèque d'agents, puis la commande `agents-dev`, ou directement dans un projet.
#
#   curl -fsSL https://raw.githubusercontent.com/tchamouramses/Agent-Prompt-For-Developper/main/install.sh | sh
#   curl -fsSL .../install.sh | sh -s -- --projet          installe dans le dossier courant, sans rien hors du projet
#   curl -fsSL .../install.sh | sh -s -- --projet ~/app    installe dans ce dossier
#   curl -fsSL .../install.sh | sh -s -- --global          installe la commande, puis pour tous les projets
#
# Depuis un clone, le script prend le clone comme source sans rien télécharger :
#   sh Agent-Prompt-For-Developper/install.sh --projet ~/app
# Avec npm, sans ce script : npx @tchamouramses/agents-dev (voir le README).
#
# Ensuite, depuis la racine de n'importe quel projet :
#   agents-dev                 stacks et outils détectés (options : agents-dev --help)
#   agents-dev maj             récupère la dernière version et met à jour l'installation globale
#
# Les options qui suivent --projet (ou toutes, sans --projet) sont passées à scripts/install.mjs.
# Variables : AGENTS_DEV_HOME (défaut ~/.local/share/agents-dev), AGENTS_DEV_BIN (défaut ~/.local/bin),
# AGENTS_DEV_REF (branche ou tag, défaut main).
set -eu

DEPOT="tchamouramses/Agent-Prompt-For-Developper"
REF="${AGENTS_DEV_REF:-main}"
DEST="${AGENTS_DEV_HOME:-$HOME/.local/share/agents-dev}"
BIN="${AGENTS_DEV_BIN:-$HOME/.local/bin}"

command -v node >/dev/null 2>&1 || { echo "Node.js 18 ou plus est requis (https://nodejs.org)." >&2; exit 1; }
node -e 'process.exit(parseInt(process.versions.node, 10) < 18 ? 1 : 0)' || { echo "Node.js 18 ou plus est requis (version trouvée : $(node --version))." >&2; exit 1; }

PROJET=""
if [ "${1:-}" = "--projet" ]; then
  shift
  PROJET="."
  case "${1:-}" in
    ""|-*) ;;
    *) PROJET="$1"; shift ;;
  esac
fi

# Source : le clone d'où le script est lancé, sinon un clone Git, sinon l'archive de GitHub.
# Lancé par `curl … | sh`, $0 vaut « sh » : seul un chemin vers install.sh désigne un clone.
ICI=""
case "$0" in
  *install.sh) ICI="$(cd "$(dirname "$0")" && pwd)" ;;
esac
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
if [ -n "$ICI" ] && [ -f "$ICI/scripts/install.mjs" ]; then
  SOURCE="$ICI"
elif command -v git >/dev/null 2>&1 && git clone -q --depth 1 --branch "$REF" "https://github.com/$DEPOT.git" "$TMP/source" 2>/dev/null; then
  SOURCE="$TMP/source"
else
  command -v curl >/dev/null 2>&1 || { echo "git ou curl est requis." >&2; exit 1; }
  mkdir "$TMP/source"
  curl -fsSL "https://codeload.github.com/$DEPOT/tar.gz/$REF" | tar -xz -C "$TMP/source" --strip-components 1 || {
    echo "Téléchargement impossible depuis GitHub. Vérifie la connexion ou AGENTS_DEV_REF ($REF)." >&2
    exit 1
  }
  SOURCE="$TMP/source"
fi

if [ -n "$PROJET" ]; then
  # Rien n'est gardé hors du projet : la source temporaire est effacée à la sortie.
  node "$SOURCE/scripts/install.mjs" "$PROJET" "$@"
  exit $?
fi

if [ "$SOURCE" != "$ICI" ]; then
  rm -rf "$DEST"
  mkdir -p "$(dirname "$DEST")"
  mv "$SOURCE" "$DEST"
else
  DEST="$ICI"  # lancé depuis un clone : la commande utilise ce clone, mis à jour par git pull
fi
mkdir -p "$BIN"

cat > "$BIN/agents-dev" <<EOF
#!/bin/sh
# Généré par install.sh de $DEPOT.
if [ "\${1:-}" = "maj" ]; then
  if [ -d "$DEST/.git" ]; then
    git -C "$DEST" pull -q --ff-only
  else
    curl -fsSL "https://raw.githubusercontent.com/$DEPOT/$REF/install.sh" | AGENTS_DEV_HOME="$DEST" AGENTS_DEV_BIN="$BIN" AGENTS_DEV_REF="$REF" sh
  fi
  [ -f "\$HOME/.bibliotheque-agents.json" ] && exec node "$DEST/scripts/install.mjs" --global
  exit 0
fi
exec node "$DEST/scripts/install.mjs" "\$@"
EOF
chmod +x "$BIN/agents-dev"
echo "Bibliothèque dans $DEST, commande installée : $BIN/agents-dev"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "Ajoute $BIN à ton PATH, par exemple : echo 'export PATH=\"$BIN:\$PATH\"' >> ~/.profile" ;;
esac

if [ "$#" -gt 0 ]; then
  exec node "$DEST/scripts/install.mjs" "$@"
fi
