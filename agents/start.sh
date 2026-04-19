#!/bin/bash
# Start all Genii Studio agents via PM2

cd "$(dirname "$0")"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "PM2 not found. Install: npm install -g pm2"
    exit 1
fi

# Start all agents
pm2 start pm2.config.js

echo "Agents started. Monitor with: pm2 monit"
echo "Logs: tail -f ~/geniinow-projects/logs/*.log"
