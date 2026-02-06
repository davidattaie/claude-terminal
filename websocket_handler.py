"""WebSocket API handler for Claude Code Terminal."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import (
    WS_TYPE_START,
    WS_TYPE_INPUT,
    WS_TYPE_RESIZE,
    WS_TYPE_STOP,
    WS_TYPE_OUTPUT,
    CONF_WORKING_DIR,
    DEFAULT_WORKING_DIR,
    DOMAIN,
)
from .terminal_manager import ClaudeTerminalManager

_LOGGER = logging.getLogger(__name__)


@callback
def async_register_websocket_handlers(hass: HomeAssistant) -> None:
    """Register WebSocket API handlers."""
    websocket_api.async_register_command(hass, handle_terminal_start)
    websocket_api.async_register_command(hass, handle_terminal_input)
    websocket_api.async_register_command(hass, handle_terminal_resize)
    websocket_api.async_register_command(hass, handle_terminal_stop)


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_START,
        vol.Optional("working_dir"): str,
    }
)
@websocket_api.async_response
async def handle_terminal_start(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle terminal start command.

    Starts a new Claude Code terminal session and returns the session ID.
    """
    # Get terminal manager
    manager: ClaudeTerminalManager = hass.data[DOMAIN]["manager"]

    # Get config entry for auth token
    config_entries = hass.config_entries.async_entries(DOMAIN)
    if not config_entries:
        connection.send_error(msg["id"], "not_configured", "Integration not configured")
        return

    config_entry = config_entries[0]

    # Get working directory
    working_dir = msg.get("working_dir")
    if not working_dir:
        working_dir = config_entry.options.get(
            CONF_WORKING_DIR,
            config_entry.data.get(CONF_WORKING_DIR, DEFAULT_WORKING_DIR),
        )

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Get auth token from config
    auth_token = config_entry.data.get("access_token")

    # Define output callback to send data to WebSocket
    def output_callback(sid: str, data: bytes) -> None:
        """Send terminal output to WebSocket."""
        try:
            connection.send_message(
                websocket_api.event_message(
                    msg["id"],
                    {
                        "type": WS_TYPE_OUTPUT,
                        "session_id": sid,
                        "data": data.decode("utf-8", errors="replace"),
                    },
                )
            )
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error sending terminal output: %s", err)

    try:
        # Spawn terminal
        await manager.spawn_terminal(
            session_id=session_id,
            working_dir=working_dir,
            auth_token=auth_token,
            output_callback=output_callback,
        )

        # Send success response with session ID
        connection.send_result(
            msg["id"],
            {
                "session_id": session_id,
                "working_dir": working_dir,
            },
        )

    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("Failed to start terminal: %s", err)
        connection.send_error(msg["id"], "start_failed", str(err))


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_INPUT,
        vol.Required("session_id"): str,
        vol.Required("data"): str,
    }
)
@websocket_api.async_response
async def handle_terminal_input(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle terminal input command.

    Sends user input to the specified terminal session.
    """
    manager: ClaudeTerminalManager = hass.data[DOMAIN]["manager"]
    session_id = msg["session_id"]
    data = msg["data"]

    try:
        await manager.write_to_terminal(session_id, data)
        connection.send_result(msg["id"], {"success": True})

    except ValueError as err:
        connection.send_error(msg["id"], "session_not_found", str(err))
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("Failed to send input: %s", err)
        connection.send_error(msg["id"], "input_failed", str(err))


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_RESIZE,
        vol.Required("session_id"): str,
        vol.Required("rows"): int,
        vol.Required("cols"): int,
    }
)
@websocket_api.async_response
async def handle_terminal_resize(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle terminal resize command.

    Resizes the terminal window for the specified session.
    """
    manager: ClaudeTerminalManager = hass.data[DOMAIN]["manager"]
    session_id = msg["session_id"]
    rows = msg["rows"]
    cols = msg["cols"]

    try:
        await manager.resize_terminal(session_id, rows, cols)
        connection.send_result(msg["id"], {"success": True})

    except ValueError as err:
        connection.send_error(msg["id"], "session_not_found", str(err))
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("Failed to resize terminal: %s", err)
        connection.send_error(msg["id"], "resize_failed", str(err))


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_STOP,
        vol.Required("session_id"): str,
    }
)
@websocket_api.async_response
async def handle_terminal_stop(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle terminal stop command.

    Stops and removes the specified terminal session.
    """
    manager: ClaudeTerminalManager = hass.data[DOMAIN]["manager"]
    session_id = msg["session_id"]

    try:
        await manager.stop_terminal(session_id)
        connection.send_result(msg["id"], {"success": True})

    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("Failed to stop terminal: %s", err)
        connection.send_error(msg["id"], "stop_failed", str(err))
