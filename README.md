# Claude Code Terminal for Home Assistant

A Home Assistant custom integration that provides a web-based terminal interface for Claude Code CLI, styled with the Star Trek LCARS theme.

## Features

- 🖥️ Full interactive Claude Code terminal in Home Assistant
- 🎨 LCARS (Star Trek) themed interface
- 🔒 Secure OAuth 2.0 authentication
- 👥 Admin-only access with audit logging
- 📱 Responsive design for desktop and mobile
- ⚡ Real-time WebSocket communication
- 🛡️ Resource limits and security controls

## Prerequisites

### 1. Claude Code CLI

Claude Code must be installed on your Home Assistant system:

```bash
npm install -g @anthropic-ai/claude-code
```

Verify installation:
```bash
claude --version
```

### 2. Anthropic API Access

You'll need an Anthropic API account and OAuth credentials:
- Sign up at https://console.anthropic.com/
- Create OAuth application for Home Assistant integration
- Note your Client ID and Client Secret

### 3. Home Assistant Requirements

- Home Assistant 2023.9.0 or later
- Admin user access
- External URL configured (required for OAuth callback)

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/davidattaie/claude-code-terminal`
6. Select category "Integration"
7. Click "Add"
8. Search for "Claude Code Terminal"
9. Click "Download"
10. Restart Home Assistant

### Option 2: Manual Installation

1. Download the latest release from GitHub
2. Extract the `claude_code_terminal` folder
3. Copy to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/claude_code_terminal/
   ```
4. Restart Home Assistant

## Configuration

### 1. Add Integration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Claude Code Terminal"
4. Click to start setup

### 2. OAuth Authentication

1. Click "Submit" to start OAuth flow
2. You'll be redirected to Anthropic's authorization page
3. Sign in and authorize the application
4. You'll be redirected back to Home Assistant
5. Configuration complete!

### 3. Access Terminal

- Look for "Claude Code Terminal" in the sidebar
- Click to open the LCARS terminal interface
- Start chatting with Claude!

## Security

### Authentication & Authorization

- **OAuth 2.0**: Secure authentication with Anthropic
- **Admin Only**: Terminal access restricted to Home Assistant administrators
- **Token Encryption**: All OAuth tokens stored encrypted in Home Assistant

### Process Isolation

- **Working Directory Whitelist**: Terminal can only access:
  - `/config` (Home Assistant configuration)
  - `/share` (Shared files)
  - `/addon_configs` (Add-on configurations)
  - `/homeassistant` (HA core files)
- **Path Traversal Protection**: Prevents directory escape attempts
- **Resource Limits**:
  - Maximum 3 concurrent sessions
  - 30-minute idle timeout
  - CPU and memory limits on child processes

### Audit Logging

All terminal activity is logged:
- Terminal start/stop events
- Failed authentication attempts
- Security violations
- Session timeout cleanups

View logs in Home Assistant:
```
Settings → System → Logs
```

Filter for `claude_code_terminal` events.

## Usage

### Starting a Session

1. Open the Claude Code Terminal panel from sidebar
2. Terminal automatically starts and connects
3. Wait for "INITIALIZING TERMINAL" to complete
4. Start typing your prompts!

### Terminal Commands

All standard Claude Code commands work:
- `/help` - Show available commands
- `/commit` - Create git commits
- `/clear` - Clear conversation history
- And more...

### Keyboard Shortcuts

- `Ctrl+C` - Send interrupt signal
- `Ctrl+D` - Send EOF
- `Ctrl+L` - Clear terminal screen
- Standard terminal navigation keys

### Multiple Sessions

- Maximum 3 concurrent sessions allowed
- Each browser tab creates a new session
- Sessions auto-cleanup after 30 minutes idle

## Troubleshooting

### "Claude Code CLI not found"

**Problem**: Integration can't find the `claude` command.

**Solution**:
1. Verify Claude Code is installed: `which claude`
2. If not found, install it: `npm install -g @anthropic-ai/claude-code`
3. Restart Home Assistant
4. Try setup again

### "OAuth authentication failed"

**Problem**: OAuth flow completed but authentication fails.

**Solution**:
1. Verify your Anthropic API account is active
2. Check OAuth Client ID and Secret are correct
3. Ensure Home Assistant external URL is configured
4. Check redirect URI is whitelisted in Anthropic Console
5. Remove and re-add the integration

### "Session not found" errors

**Problem**: Terminal shows session errors or disconnects.

**Solution**:
1. Refresh the browser page
2. Check Home Assistant logs for errors
3. Verify Claude Code CLI is running: `ps aux | grep claude`
4. Restart Home Assistant if issues persist

### Terminal output not showing

**Problem**: Terminal connects but no output appears.

**Solution**:
1. Check WebSocket connection in browser developer tools
2. Verify Home Assistant is accessible via external URL
3. Check for WebSocket proxy issues (if using reverse proxy)
4. Try different browser

### Resource limit errors

**Problem**: "Maximum number of sessions reached" error.

**Solution**:
1. Close unused terminal tabs
2. Wait for idle sessions to timeout (30 minutes)
3. Or manually stop sessions via Home Assistant restart

## Advanced Configuration

### Custom Working Directory

Edit integration options to change default working directory:
1. Go to Settings → Devices & Services
2. Find "Claude Code Terminal"
3. Click "Configure"
4. Select from allowed directories

### Adjust Resource Limits

Modify `const.py` in the integration folder:

```python
DEFAULT_MAX_SESSIONS = 5  # Change from 3
DEFAULT_SESSION_TIMEOUT = 3600  # Change from 1800 (seconds)
```

Restart Home Assistant after changes.

### LCARS Theme Integration

This terminal automatically integrates with the LCARS theme if installed:
- Sound effects (if `input_boolean.lcars_sound` is enabled)
- Matching color palette
- Consistent UI styling

## Development

### Running Tests

```bash
pytest tests/
```

### Debug Mode

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.claude_code_terminal: debug
```

### Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- **Issues**: https://github.com/davidattaie/claude-code-terminal/issues
- **Discussions**: https://github.com/davidattaie/claude-code-terminal/discussions
- **Home Assistant Community**: Tag `@davidattaie`

## Credits

- **LCARS Theme**: Based on [HA-LCARS](https://github.com/th3jesta/ha-lcars) by @th3jesta
- **xterm.js**: Terminal emulator library
- **Claude Code**: Anthropic's CLI tool

## License

MIT License - see LICENSE file for details

## Disclaimer

This is a community integration, not officially supported by Anthropic or Home Assistant.

⚠️ **Security Warning**: This integration provides terminal access to your Home Assistant system. Only grant access to trusted administrators.

---

**Star Trek™** and related marks are owned by CBS Studios Inc. This is a non-commercial fan production.
