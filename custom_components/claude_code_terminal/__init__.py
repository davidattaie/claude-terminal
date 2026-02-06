"""The Claude Code Terminal integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .bundled_runtime import BundledRuntime
from .const import DOMAIN, DEFAULT_MAX_SESSIONS, DEFAULT_SESSION_TIMEOUT
from .oauth_handler import OAuthHandler
from .panel import async_register_panel, async_unregister_panel
from .terminal_manager import ClaudeTerminalManager
from .websocket_handler import async_register_websocket_handlers

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Claude Code Terminal component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Claude Code Terminal from a config entry."""
    _LOGGER.info("Setting up Claude Code Terminal integration")

    # Get integration path
    integration_path = Path(__file__).parent

    # Initialize bundled runtime
    runtime = BundledRuntime(hass, integration_path)

    # Install Node.js and Claude CLI if not already installed
    if not runtime.is_installed():
        _LOGGER.info("Bundled runtime not found, installing...")
        try:
            await runtime.install()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Failed to install bundled runtime: %s", err)
            raise ConfigEntryNotReady from err
    else:
        _LOGGER.info("Bundled runtime already installed")

    # Initialize OAuth handler and load tokens
    oauth_handler = OAuthHandler(
        hass,
        client_id="home-assistant-claude-terminal",  # Replace with actual
        client_secret="",  # Replace with actual
    )
    oauth_handler.load_tokens(entry.data)

    # Verify we have a valid token
    try:
        await oauth_handler.get_valid_access_token()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Failed to get valid access token: %s", err)
        raise ConfigEntryNotReady from err

    # Initialize terminal manager with bundled runtime
    manager = ClaudeTerminalManager(
        hass,
        runtime=runtime,
        max_sessions=DEFAULT_MAX_SESSIONS,
        session_timeout=DEFAULT_SESSION_TIMEOUT,
    )
    await manager.start()

    # Store manager, runtime, and oauth handler in hass.data
    hass.data[DOMAIN] = {
        "manager": manager,
        "runtime": runtime,
        "oauth_handler": oauth_handler,
        "entry": entry,
    }

    # Register WebSocket API handlers
    async_register_websocket_handlers(hass)

    # Register panel
    await async_register_panel(hass)

    # Set up update listener for options
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Claude Code Terminal integration setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Claude Code Terminal integration")

    # Get manager
    manager: ClaudeTerminalManager = hass.data[DOMAIN]["manager"]

    # Cleanup all terminal sessions
    await manager.cleanup()

    # Unregister panel
    await async_unregister_panel(hass)

    # Remove from hass.data
    hass.data.pop(DOMAIN)

    _LOGGER.info("Claude Code Terminal integration unloaded")
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
