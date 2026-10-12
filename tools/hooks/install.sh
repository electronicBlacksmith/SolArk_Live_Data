#!/bin/sh
# Install the leak-check pre-commit hook into a repo.
# Usage: tools/hooks/install.sh <repo_dir> [captures_dir]
# captures_dir defaults to this checkout's captures/ (raw, gitignored).
set -e
TOOLS=$(cd "$(dirname "$0")/.." && pwd)
REPO=$(cd "${1:?repo dir required}" && pwd)
CAPTURES=$(cd "${2:-$TOOLS/../captures}" 2>/dev/null && pwd || echo "${2:-$TOOLS/../captures}")
git -C "$REPO" config solark.tools "$TOOLS"
git -C "$REPO" config solark.captures "$CAPTURES"
cp "$TOOLS/hooks/pre-commit" "$REPO/.git/hooks/pre-commit"
chmod +x "$REPO/.git/hooks/pre-commit"
echo "installed leak-check hook in $REPO (tools=$TOOLS captures=$CAPTURES)"
