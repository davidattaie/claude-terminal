# Implementation Plan: Claude Code Terminal for Home Assistant

## Context

This integration will add a web-based Claude Code terminal to Home Assistant, allowing users to interact with Claude Code CLI directly from their Home Assistant dashboard. The user currently has a Home Assistant theme development repository (LCARS theme) and wants to create a custom component that provides terminal access to Claude Code.

The motivation is to enable seamless AI-assisted development within the Home Assistant environment without needing to switch to a separate terminal application.

## Architecture Overview

**Approach: Custom Integration (Python backend) + Custom Panel (JavaScript frontend)**

This hybrid approach provides:
- Secure authentication via Home Assistant's built-in auth system
- Native sidebar panel integration (appears like a first-class HA feature)
- Full WebSocket communication for real-time terminal I/O
- Process lifecycle management for Claude Code CLI
- HACS distribution compatibility

## Key Components

### Backend (Python)

1. Terminal Manager - Spawns and manages Claude Code PTY processes
2. WebSocket Handler - Relays data between frontend terminal and PTY
3. Panel Registration - Adds terminal panel to HA sidebar
4. Config Flow - Optional UI for API key configuration

### Frontend (JavaScript)

1. Custom Panel - LitElement-based panel with xterm.js terminal
2. WebSocket Client - Communicates with HA WebSocket API
3. Terminal UI - Full-featured terminal with resize, theming, etc.

## Implementation Steps

### 0. Research Claude Code Authentication

**CRITICAL FIRST STEP:** Before implementing OAuth, research Claude Code's actual authentication mechanism:
- Review Claude Code CLI source code or documentation
- Determine if it uses:
  - Anthropic API keys (simpler)
  - OAuth 2.0 (more complex)
  - Token-based authentication
  - Session-based authentication
- Check if Claude Code stores auth credentials locally (e.g., in ~/.claude/ directory)
- Determine if we can reuse existing Claude Code authentication or need separate flow
- Test spawning Claude Code in PTY mode to see authentication requirements

**Decision Point:** Based on research, we may need to adjust the OAuth implementation approach:
- Option A: If Claude Code uses API keys, simplify to API key config flow
- Option B: If Claude Code has its own OAuth, leverage existing auth
- Option C: If no built-in auth, implement full OAuth 2.0 flow as planned

### 1. Create Component Structure

Create the following directory and files in `/Users/davidattaie/Dev/homeassistant/`:

```
custom_components/claude_code_terminal/
├── __init__.py                 # Component initialization
├── manifest.json               # Component metadata
├── const.py                    # Constants (domain, version)
├── config_flow.py              # OAuth configuration flow
├── strings.json                # UI strings
├── oauth_handler.py            # OAuth 2.0 authentication
├── terminal_manager.py         # PTY process management
├── websocket_handler.py        # WebSocket API commands
├── panel.py                    # Panel registration
├── translations/
│   └── en.json                 # English translations
└── frontend/
    ├── claude-terminal-panel.js   # Frontend panel code
    └── lcars-terminal-styles.css  # LCARS theme styles
```

### 2. Implement OAuth Authentication

**File: oauth_handler.py**
- Implement Claude Code OAuth 2.0 flow
- Create OAuth config with:
  - Client ID: Use Home Assistant's OAuth client or register new one
  - Authorization endpoint: https://anthropic.com/oauth/authorize
  - Token endpoint: https://anthropic.com/oauth/token
  - Scopes: Required Claude Code API scopes
- Implement methods:
  - get_authorization_url() - Generate OAuth URL for user
  - handle_oauth_callback(code) - Exchange code for tokens
  - refresh_access_token() - Refresh expired tokens
  - store_tokens() - Securely store in config entry
- Use Home Assistant's aiohttp_client for API calls
- Add token expiration handling and auto-refresh

**File: config_flow.py**
- Implement multi-step config flow:
  - Step 1: Display authorization link, open in new tab
  - Step 2: Wait for OAuth callback
  - Step 3: Validate tokens and complete setup
- Use Home Assistant's OAuth config flow helpers
- Store encrypted tokens in config entry

### 3. Implement Backend Core

**File: terminal_manager.py**
- Implement ClaudeTerminalManager class
- Use Python's pty module to spawn Claude Code as pseudo-terminal
- Pass OAuth tokens via environment variables:
  - ANTHROPIC_API_KEY from OAuth token
  - CLAUDE_CODE_AUTH_TOKEN for authenticated sessions
- Create async methods for:
  - spawn_terminal(session_id, working_dir, auth_token) - Start new PTY process
  - write_to_terminal(session_id, data) - Send input to PTY
  - resize_terminal(session_id, rows, cols) - Resize PTY
  - cleanup() - Terminate all processes on shutdown
- Add resource limits: max 3 concurrent sessions, 30-minute idle timeout
- Implement working directory whitelist validation
- Handle token refresh before spawning terminal

**File: websocket_handler.py**
- Register WebSocket API commands:
  - claude_terminal/start - Start new terminal session
  - claude_terminal/input - Send input to terminal
  - claude_terminal/resize - Handle terminal resize
  - claude_terminal/stop - Stop terminal session
- Implement bidirectional data relay using asyncio queues
- Add error handling and connection cleanup

**File: __init__.py**
- Register component with Home Assistant
- Initialize ClaudeTerminalManager
- Register WebSocket commands
- Register custom panel
- Set up config entry platform

**File: panel.py**
- Register panel with Home Assistant frontend
- Set panel properties: icon (mdi:console), title, URL path
- Link to frontend JavaScript bundle

### 4. Implement Frontend Styling

**File: frontend/lcars-terminal-styles.css**
- Define LCARS color palette for terminal:
```css
:root {
  --lcars-orange: #FF9900;
  --lcars-gold: #FFAA00;
  --lcars-blue: #9999FF;
  --lcars-purple: #CC99CC;
  --lcars-black: #000000;
  --lcars-gray: #333333;
}
```
- Style panel container with LCARS borders
- Create title bar with "LCARS COMPUTER INTERFACE" text
- Add status indicator styling
- Terminal container styling (full height, proper padding)

### 5. Implement Frontend

**File: frontend/claude-terminal-panel.js**
- Create LitElement custom element ClaudeTerminalPanel
- Initialize xterm.js terminal with LCARS theme:
  - Background: #000000 (black)
  - Foreground: #FF9900 (LCARS orange/gold)
  - Cursor: #FF9900
  - Selection background: #FF990055 (semi-transparent)
  - ANSI colors mapped to LCARS palette (use colors from lcars.yaml)
  - Font: Monospace, size 14px
  - xterm-addon-fit for automatic resizing
  - xterm-addon-web-links for clickable URLs
- Add LCARS-style panel chrome:
  - Border using LCARS accent colors
  - Title bar with "LCARS COMPUTER INTERFACE" text
  - Status indicator (online/offline)
  - Integration with lcars.js sound effects (terminal beeps)
- Implement WebSocket communication:
  - Connect to HA WebSocket API
  - Send claude_terminal/start on panel load
  - Relay terminal input via claude_terminal/input
  - Render output from WebSocket messages
  - Handle resize events
- Add session lifecycle management

### 6. Configuration Files

**File: manifest.json**
```json
{
  "domain": "claude_code_terminal",
  "name": "Claude Code Terminal",
  "documentation": "https://github.com/[username]/claude-code-terminal",
  "dependencies": [],
  "codeowners": ["@[username]"],
  "requirements": [],
  "version": "1.0.0",
  "config_flow": true
}
```

**File: const.py**
- Define domain constant: DOMAIN = "claude_code_terminal"
- Define allowed working directories
- Define resource limits

**File: config_flow.py**
- Implement optional config flow for API key entry
- Validate API key format
- Store in encrypted config entry

**File: strings.json**
- Define UI strings for config flow

### 7. Security Implementation

**Authentication & Authorization:**
- Restrict panel access to admin users only
- Validate user permissions before spawning terminals
- Use Home Assistant's session management

**Process Isolation:**
- Whitelist allowed working directories (e.g., /config, user home)
- Prevent path traversal attacks
- Run processes with minimal privileges
- Set CPU/memory limits via resource module

**API Key Security:**
- Store Anthropic API key encrypted in config entry
- Pass to Claude Code via environment variable only
- Never expose in logs or frontend

**Audit Logging:**
- Log all terminal starts/stops to HA history
- Track session activity

### 8. Testing & Verification

**Functional Tests:**
1. Start terminal and verify Claude Code spawns correctly
2. Test terminal I/O (input commands, see output)
3. Test terminal resize handling
4. Test multiple concurrent sessions
5. Verify session cleanup on disconnect
6. Test process termination on HA shutdown

**Security Tests:**
1. Verify path traversal prevention
2. Test authentication requirement (non-admin blocked)
3. Validate resource limits enforcement
4. Check session isolation

**Integration Tests:**
1. Test with existing LCARS theme
2. Verify sidebar panel appearance
3. Test on multiple browsers

### 9. Documentation

Create README.md with:
- Installation instructions (manual + HACS)
- Prerequisites (Claude Code CLI must be installed and authenticated)
- Configuration steps
- Security warnings
- Troubleshooting guide
- Screenshots

### 10. HACS Distribution Setup

**File: hacs.json (in project root)**
```json
{
  "name": "Claude Code Terminal",
  "render_readme": true,
  "content_in_root": false,
  "domains": ["panel_custom"],
  "homeassistant": "2023.9.0"
}
```

**File: .github/workflows/validate.yaml**
- Add hassfest validation (validates manifest.json)
- Add HACS validation (validates hacs.json)
- Similar to your existing LCARS theme workflow

**File: info.md**
- Create HACS info display with:
  - Features overview
  - Installation instructions
  - Configuration steps
  - Screenshots

**File: README.md**
- Comprehensive documentation:
  - Features and benefits
  - Installation via HACS and manual
  - OAuth setup instructions
  - Security considerations
  - Troubleshooting
  - LCARS theme integration notes

## Critical Files to Create/Modify

1. custom_components/claude_code_terminal/__init__.py - Component entry point, ties everything together
2. custom_components/claude_code_terminal/oauth_handler.py - OAuth 2.0 authentication flow for Claude Code
3. custom_components/claude_code_terminal/terminal_manager.py - Core PTY process management with token handling
4. custom_components/claude_code_terminal/websocket_handler.py - WebSocket API for terminal I/O
5. custom_components/claude_code_terminal/frontend/claude-terminal-panel.js - Frontend terminal UI with LCARS theme
6. custom_components/claude_code_terminal/config_flow.py - OAuth configuration flow UI
7. custom_components/claude_code_terminal/manifest.json - Component metadata

## Dependencies

**Python (Backend):**
- Home Assistant core libraries (aiohttp, asyncio)
- Python stdlib: pty, fcntl, termios, struct, os
- No external pip packages required

**JavaScript (Frontend):**
- xterm.js v5+ (terminal emulator)
- xterm-addon-fit (resize handling)
- xterm-addon-web-links (clickable URLs)
- LitElement (HA frontend framework)

## Security Considerations

1. Admin-only access - Panel requires Home Assistant admin role
2. Working directory whitelist - Restrict to safe directories only
3. Resource limits - Max 3 sessions, 30-min timeout, CPU/memory limits
4. API key encryption - Store Anthropic key securely
5. Audit trail - Log all terminal access
6. Process isolation - Run with minimal privileges

## Implementation Notes

### OAuth Integration Approach

The built-in OAuth flow will require:
1. OAuth Client Registration: Register the integration as an OAuth client with Anthropic
   - May need to use Home Assistant's OAuth proxy service
   - Or register directly with redirect URI pointing to Home Assistant instance
2. Callback Handling: Implement OAuth callback endpoint in Home Assistant
   - Use Home Assistant's auth callback infrastructure
   - Handle authorization code exchange
3. Token Management:
   - Store access token and refresh token encrypted in config entry
   - Implement automatic token refresh before expiration
   - Pass token to Claude Code via environment variable
4. Alternative: If Anthropic doesn't support custom OAuth clients, consider:
   - Using Claude Code's built-in authentication mechanism
   - Prompting user to authenticate via CLI and storing resulting tokens

### LCARS Theme Integration

- Style xterm.js terminal with LCARS orange/gold colors (#FF9900) on black background
- Map ANSI colors to LCARS palette from lcars.yaml
- Add LCARS-style panel borders and title bar
- Integrate with existing lcars.js sound effects (terminal beeps)
- Use LCARS fonts if available, otherwise monospace

### Process Management

- Use asyncio for non-blocking I/O; implement graceful shutdown
- Token refresh check before each terminal spawn
- Handle token expiration gracefully (show error, prompt re-authentication)

### Error Handling

- Catch and log all exceptions; display user-friendly errors in terminal
- OAuth errors: clear messaging about re-authentication
- Process errors: retry logic with exponential backoff

### Cross-platform

- Test on Linux, macOS, and Windows (if supported by HA installation)
- PTY module availability varies by platform (primarily Unix-like systems)

## Alternative Approaches Considered

1. Home Assistant Add-on - Rejected due to Docker overhead and limited compatibility (requires Supervisor)
2. External Server + iframe - Rejected due to separate authentication and poor integration
3. Lovelace Card - Rejected due to limited screen space (terminal needs full screen)

The chosen approach (custom integration + panel) provides the best balance of security, user experience, and compatibility.

## Success Criteria

- Terminal panel appears in Home Assistant sidebar
- Claude Code CLI launches and is interactive
- Terminal input/output works in real-time
- Terminal resizes correctly with browser window
- Multiple concurrent sessions work
- Sessions clean up properly on disconnect
- Admin-only access is enforced
- Working directory restrictions work
- Process terminates cleanly on HA shutdown
- Documentation is clear and complete
