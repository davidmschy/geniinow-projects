#!/bin/bash
# Launch Claude Code with Genii Studio context
cd ~/geniinow-projects
claude --context .claude-context "$@"
