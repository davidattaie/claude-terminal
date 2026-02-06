#!/bin/bash
# Deploy Claude Code Terminal to GitHub

set -e

echo "🚀 Deploying Claude Code Terminal to GitHub..."

cd /Users/davidattaie/Dev/homeassistant

# Stage all changes
echo "📦 Staging files..."
git add .

# Commit
echo "💾 Creating commit..."
git commit -m "Release v1.0.0: Claude Code Terminal for Home Assistant

Complete implementation with:
- OAuth 2.0 authentication
- Full interactive terminal with xterm.js
- LCARS theme integration
- Admin-only access with security features
- WebSocket real-time communication
- PTY process management
- Audit logging
- HACS distribution ready

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to dev branch
echo "⬆️  Pushing to GitHub (dev branch)..."
git push -u origin dev

# Create and push release tag
echo "🏷️  Creating release tag v1.0.0..."
git tag -a v1.0.0 -m "Release v1.0.0

First stable release of Claude Code Terminal

Features:
- OAuth 2.0 authentication with Anthropic
- Full interactive Claude Code terminal in Home Assistant
- LCARS (Star Trek) themed interface
- Real-time WebSocket communication
- Secure PTY process management
- Admin-only access with audit logging
- Resource limits and security controls
- HACS compatible

Requirements:
- Home Assistant 2023.9.0+
- Claude Code CLI installed
- Anthropic API OAuth credentials"

echo "⬆️  Pushing tag..."
git push origin v1.0.0

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://github.com/davidattaie/claude-terminal/releases"
echo "2. Verify the v1.0.0 release appears"
echo "3. In HACS, add custom repository: https://github.com/davidattaie/claude-terminal"
echo "4. Category: Integration"
echo "5. Search and install 'Claude Code Terminal'"
echo ""
echo "🎉 Done! The integration is now HACS-compatible!"
