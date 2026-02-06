"""Constants for the Claude Code Terminal integration."""

DOMAIN = "claude_code_terminal"
NAME = "Claude Code Terminal"
VERSION = "1.0.0"

# Configuration
CONF_API_KEY = "api_key"
CONF_WORKING_DIR = "working_dir"
CONF_MAX_SESSIONS = "max_sessions"
CONF_SESSION_TIMEOUT = "session_timeout"

# Defaults
DEFAULT_WORKING_DIR = "/config"
DEFAULT_MAX_SESSIONS = 3
DEFAULT_SESSION_TIMEOUT = 1800  # 30 minutes in seconds

# Allowed working directories (security whitelist)
ALLOWED_WORKING_DIRS = [
    "/config",
    "/share",
    "/addon_configs",
    "/homeassistant",
]

# WebSocket commands
WS_TYPE_START = "claude_terminal/start"
WS_TYPE_INPUT = "claude_terminal/input"
WS_TYPE_RESIZE = "claude_terminal/resize"
WS_TYPE_STOP = "claude_terminal/stop"
WS_TYPE_OUTPUT = "claude_terminal/output"

# Panel configuration
PANEL_URL = "claude-code-terminal"
PANEL_ICON = "mdi:console"
PANEL_TITLE = "Claude Code Terminal"
PANEL_COMPONENT = "claude-terminal-panel"

# Resource limits
MAX_OUTPUT_BUFFER_SIZE = 1048576  # 1MB
MAX_PTY_BUFFER_SIZE = 65536  # 64KB
