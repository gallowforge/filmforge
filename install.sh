#!/usr/bin/env bash
# install.sh: install the nine filmforge skills and their tools for Claude Code.
#
#   ./install.sh                     # into ~/.claude/skills
#   ./install.sh --dest DIR          # into another skills folder
#   ./install.sh --dry-run           # show what would happen
#   ./install.sh --uninstall         # remove only the forge-* folders this installer made
#
# Each skill lands self-contained: SKILL.md and references/, the tools as scripts/, the price table in config/ and
# the templates in templates/, so every command in a skill runs from the skill's own folder. A folder is replaced
# only if it carries this installer's marker (.forge-engine); nothing outside the forge-* folders is touched.
# The copying is done by install.py (also usable on its own, e.g. on Windows); this script adds the checks.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

PY=${PYTHON:-python3}
command -v "$PY" >/dev/null 2>&1 || { echo "install.sh: $PY not found; the tools need Python 3.9 or newer" >&2; exit 1; }

dest="$HOME/.claude/skills"
mode=install
args=("$@")
while [ $# -gt 0 ]; do
  case "$1" in
    --dest) dest=${2:?--dest needs a folder}; shift ;;
    --dest=*) dest=${1#--dest=} ;;
    --dry-run) mode=dry ;;
    --uninstall) mode=uninstall ;;
    -h|--help) "$PY" "$HERE/install.py" --help; exit 0 ;;
  esac
  shift
done

"$PY" "$HERE/install.py" "${args[@]+"${args[@]}"}"
[ "$mode" = install ] || exit 0

# Prove the install: every skill has its SKILL.md and tools, and the tools run from the installed folder.
n=0
case "$dest" in /*) ;; *) dest="$PWD/$dest" ;; esac
for skill in "$HERE"/skills/forge-*/; do
  name=$(basename "$skill")
  if [ -d "$dest/$name" ] && [ ! -f "$dest/$name/.forge-engine" ]; then
    echo "install.sh: $dest/$name was left alone: it was not made by this installer. Move it aside, then run again." >&2
    exit 1
  fi
  for f in SKILL.md scripts/production.py config/prices.yaml templates/production.yaml; do
    if [ ! -f "$dest/$name/$f" ]; then
      echo "install.sh: $dest/$name is incomplete (no $f)" >&2
      exit 1
    fi
  done
  n=$((n + 1))
done

if ! missing=$("$PY" - <<'EOF'
import importlib.util
need = {"numpy": "numpy", "PIL": "Pillow", "yaml": "PyYAML"}
gone = [pkg for mod, pkg in need.items() if importlib.util.find_spec(mod) is None]
print(" ".join(gone))
raise SystemExit(1 if gone else 0)
EOF
); then
  echo
  echo "Installed $n skills into $dest, but the tools need: $missing"
  echo "  $PY -m pip install -r $HERE/requirements.txt"
  exit 0
fi

"$PY" "$dest/forge-director/scripts/production.py" --help >/dev/null
"$PY" "$dest/forge-director/scripts/budget.py" --prices >/dev/null
echo
echo "Installed $n skills into $dest; the tools run from there."
echo "Next, in Claude Code: \"use forge-director to start a production\""
