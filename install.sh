#!/bin/sh
# Installe la bibliothèque d'agents sans cloner le dépôt, puis la commande `agents-dev`.
#
#   curl -fsSL https://raw.githubusercontent.com/tchamouramses/Agent-Prompt-For-Developper/main/install.sh | sh
#   curl -fsSL .../install.sh | sh -s -- --global          puis installe pour tous les projets
#   curl -fsSL .../install.sh | sh -s -- --stack laravel   puis installe dans le dossier courant
#
# Ensuite, depuis la racine de n'importe quel projet :
#   agents-dev                 stacks et outils détectés (options : python3 install.py --help)
#   agents-dev maj             télécharge la dernière version et met à jour l'installation globale
#
# Variables : AGENTS_DEV_HOME (défaut ~/.local/share/agents-dev), AGENTS_DEV_BIN (défaut ~/.local/bin),
# AGENTS_DEV_REF (branche ou tag, défaut main).
set -eu

DEPOT="tchamouramses/Agent-Prompt-For-Developper"
REF="${AGENTS_DEV_REF:-main}"
DEST="${AGENTS_DEV_HOME:-$HOME/.local/share/agents-dev}"
BIN="${AGENTS_DEV_BIN:-$HOME/.local/bin}"

command -v python3 >/dev/null 2>&1 || { echo "python3 (3.9 ou plus) est requis." >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "curl est requis." >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "https://codeload.github.com/$DEPOT/tar.gz/$REF" | tar -xz -C "$TMP"
rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")" "$BIN"
mv "$TMP"/*-* "$DEST"

cat > "$BIN/agents-dev" <<EOF
#!/bin/sh
# Généré par install.sh de $DEPOT.
if [ "\${1:-}" = "maj" ]; then
  curl -fsSL "https://raw.githubusercontent.com/$DEPOT/$REF/install.sh" | AGENTS_DEV_HOME="$DEST" AGENTS_DEV_BIN="$BIN" AGENTS_DEV_REF="$REF" sh
  [ -f "\$HOME/.bibliotheque-agents.json" ] && exec python3 "$DEST/scripts/install.py" --global
  exit 0
fi
exec python3 "$DEST/scripts/install.py" "\$@"
EOF
chmod +x "$BIN/agents-dev"
echo "Bibliothèque téléchargée dans $DEST, commande installée : $BIN/agents-dev"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "Ajoute $BIN à ton PATH, par exemple : echo 'export PATH=\"$BIN:\$PATH\"' >> ~/.profile" ;;
esac

if [ "$#" -gt 0 ]; then
  exec python3 "$DEST/scripts/install.py" "$@"
fi
