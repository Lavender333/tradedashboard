#!/bin/zsh
cd "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  print 'Please complete the Python setup in README.md first.'
  read '?Press Return to close.'
  exit 1
fi
(sleep 2; open 'http://127.0.0.1:8000/index.html') &
exec .venv/bin/python scripts/run_dashboard.py
