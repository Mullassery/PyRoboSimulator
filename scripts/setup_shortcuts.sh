#!/bin/bash
# Setup keyboard shortcuts for PyRoboSimulator

add_shortcuts() {
  if [ -f ~/.zshrc ]; then
    RC_FILE=~/.zshrc
  elif [ -f ~/.bashrc ]; then
    RC_FILE=~/.bashrc
  else
    echo "❌ No shell config found"; return 1
  fi
  
  if grep -q "dash-pyrobosimulator" "$RC_FILE"; then
    echo "⚠️  Shortcuts already installed"; return 0
  fi
  
  cat >> "$RC_FILE" << 'ALIASES'

# PyRoboSimulator dashboard shortcuts
alias dash-pyrobosimulator='pyrobosimulator dashboard --static'
alias dash-pyrobosimulator-live='pyrobosimulator dashboard'
alias dash-pyrobosimulator-export='pyrobosimulator dashboard --export /tmp/pyrobosimulator_metrics.json && echo ✓ Exported'
ALIASES
  
  echo "✅ Shortcuts added to $RC_FILE"
  echo "   Run: source $RC_FILE"
}

remove_shortcuts() {
  sed -i '' '/# PyRoboSimulator dashboard shortcuts/,/alias dash-pyrobosimulator-export=/d' ~/.zshrc 2>/dev/null
  sed -i '' '/# PyRoboSimulator dashboard shortcuts/,/alias dash-pyrobosimulator-export=/d' ~/.bashrc 2>/dev/null
  echo "✅ Shortcuts removed"
}

case "${1:-}" in --remove) remove_shortcuts ;; *) add_shortcuts ;; esac
