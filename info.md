# Claude Code Terminal

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Web-based Claude Code terminal for Home Assistant with LCARS theming.

## Features

✨ **Full Interactive Terminal** - Complete Claude Code CLI experience in your browser
🎨 **LCARS Theme** - Star Trek inspired interface matching HA-LCARS theme
🔒 **Secure OAuth** - Industry-standard authentication with Anthropic
👥 **Admin Only** - Restricted access with full audit logging
📱 **Responsive** - Works on desktop, tablet, and mobile
⚡ **Real-time** - WebSocket-based instant communication

## Quick Start

### Prerequisites

1. **Install Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Anthropic OAuth Credentials**:
   - Sign up at https://console.anthropic.com/
   - Create OAuth application
   - Note Client ID and Secret

3. **Home Assistant Setup**:
   - Version 2023.9.0 or later
   - External URL configured
   - Admin user access

### Installation

1. Install via HACS (this repository)
2. Restart Home Assistant
3. Add integration: Settings → Devices & Services → Add Integration
4. Search for "Claude Code Terminal"
5. Complete OAuth authentication flow
6. Access from sidebar!

## Screenshots

![Terminal Interface](https://via.placeholder.com/800x500?text=Claude+Code+Terminal+Screenshot)
*LCARS-themed terminal interface*

![OAuth Setup](https://via.placeholder.com/800x500?text=OAuth+Configuration)
*Simple OAuth authentication flow*

## Security

- **OAuth 2.0 Authentication** - Secure token-based auth
- **Admin-Only Access** - Requires Home Assistant admin privileges
- **Working Directory Whitelist** - Limited to safe directories
- **Resource Limits** - Max 3 sessions, 30-min timeout
- **Audit Logging** - All activity logged
- **Path Traversal Protection** - Prevents directory escapes

## Configuration

### Default Settings

- **Max Sessions**: 3 concurrent
- **Session Timeout**: 30 minutes idle
- **Allowed Directories**: `/config`, `/share`, `/addon_configs`, `/homeassistant`

### Custom Working Directory

Change via integration options:
1. Settings → Devices & Services
2. Claude Code Terminal → Configure
3. Select directory from whitelist

## Troubleshooting

**Claude CLI not found?**
- Install: `npm install -g @anthropic-ai/claude-code`
- Verify: `which claude`
- Restart Home Assistant

**OAuth fails?**
- Check external URL is configured
- Verify OAuth credentials are correct
- Ensure redirect URI is whitelisted
- Remove and re-add integration

**Terminal not connecting?**
- Check WebSocket in browser dev tools
- Verify no reverse proxy issues
- Try different browser
- Check Home Assistant logs

## LCARS Theme Integration

Automatically integrates with [HA-LCARS](https://github.com/th3jesta/ha-lcars):
- Matching color scheme
- LCARS sound effects
- Consistent styling
- Sidebar integration

## Links

- **Documentation**: [Full README](https://github.com/davidattaie/claude-code-terminal)
- **Issues**: [Report bugs](https://github.com/davidattaie/claude-code-terminal/issues)
- **Discussions**: [Community support](https://github.com/davidattaie/claude-code-terminal/discussions)

## Credits

- LCARS Theme: [@th3jesta](https://github.com/th3jesta/ha-lcars)
- Terminal: [xterm.js](https://xtermjs.org/)
- CLI: [Claude Code](https://claude.com/claude-code) by Anthropic

---

⚠️ **Security Notice**: Provides terminal access. Admin-only by default.

**Star Trek™** is owned by CBS Studios Inc. Non-commercial fan production.
