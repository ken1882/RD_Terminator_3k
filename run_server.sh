#!/bin/bash

touch LOCK

while true; do
    echo "Starting server"
    python main.py
    echo "Server stopped. If you wish to exit, use CTRL+C to break the loop in 30 seconds."
    sleep 30 || break
done

rm LOCK