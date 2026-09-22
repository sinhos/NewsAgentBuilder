#!/bin/zsh
# Finder launcher: use the repository beside this file, regardless of cwd.
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
cd -- "$(dirname -- "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  print 'Python 3.11 or newer is required. Install Python, then open this file again.'
  read -r '?Press Return to close.'
  exit 1
fi

python3 -m newsagent serve --open-browser
result=$?
if (( result != 0 )); then
  read -r '?Press Return to close.'
fi
exit "$result"
