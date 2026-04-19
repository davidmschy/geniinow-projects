#!/bin/bash
# Launch Kimi CLE with Genii Studio context
cd ~/geniinow-projects
kimi --context .claude-context "$@"
