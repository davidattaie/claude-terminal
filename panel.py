"""Panel registration for Claude Code Terminal."""
from __future__ import annotations

import logging

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PANEL_URL, PANEL_ICON, PANEL_TITLE, PANEL_COMPONENT

_LOGGER = logging.getLogger(__name__)


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register Claude Code Terminal panel."""
    # Register the frontend module
    await frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL,
        config={
            "_panel_custom": {
                "name": PANEL_COMPONENT,
                "embed_iframe": False,
                "trust_external": False,
            }
        },
        require_admin=True,  # Only admins can access terminal
    )

    _LOGGER.info(
        "Registered Claude Code Terminal panel at /%s",
        PANEL_URL,
    )


async def async_unregister_panel(hass: HomeAssistant) -> None:
    """Unregister Claude Code Terminal panel."""
    await frontend.async_remove_panel(hass, PANEL_URL)
    _LOGGER.info("Unregistered Claude Code Terminal panel")
