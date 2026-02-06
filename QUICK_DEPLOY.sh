#!/bin/bash
# Quick deploy to fix HACS error

echo "🔧 Fixing repository structure and deploying..."

cd /Users/davidattaie/Dev/homeassistant || exit 1

# Add all files
git add -A

# Commit
git commit -m "Initial release: Claude Code Terminal v1.0.0" || echo "Already committed"

# Push to dev
git push -u origin dev

# Create tag
git tag -a v1.0.0 -m "Release v1.0.0" || echo "Tag exists"
git push origin v1.0.0

echo "✅ Done! Now add to HACS:"
echo "   Repository: https://github.com/davidattaie/claude-terminal"
echo "   Category: Integration"
