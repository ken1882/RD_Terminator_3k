#!/bin/bash

while true; do
  # Check if it's 5:00 AM
  if [[ $(date +"%H:%M") == "05:00" ]]; then
    echo "$(date +"%Y-%m-%d") Restarting server"
    # Send CTRL+Z to the server's tmux window
    # Use CTRL+C and remove the kill if it response to
    tmux send-keys -t 0:2 C-z
    kill -9 $(pgrep python)
    sleep 1
    tmux send-keys -t 0:2 "python main.py" Enter
  fi
  sleep 60
done
