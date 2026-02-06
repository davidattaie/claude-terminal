"""Config flow for Claude Code Terminal integration with OAuth."""
from __future__ import annotations

import logging
import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, CONF_WORKING_DIR, DEFAULT_WORKING_DIR, ALLOWED_WORKING_DIRS
from .oauth_handler import OAuthHandler

_LOGGER = logging.getLogger(__name__)

# OAuth client credentials
# Note: In production, these should be registered with Anthropic
OAUTH_CLIENT_ID = "home-assistant-claude-terminal"  # Replace with actual client ID
OAUTH_CLIENT_SECRET = ""  # Replace with actual client secret


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Claude Code Terminal with OAuth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._oauth_handler: OAuthHandler | None = None
        self._oauth_state: str | None = None
        self._authorization_code: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - Start OAuth flow.

        Step 1: Display authorization link, open in new tab
        """
        # Only allow single instance
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            # User clicked to start OAuth flow
            return await self.async_step_oauth_authorize()

        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "info": "Click Submit to start the OAuth authorization process. "
                        "You will be redirected to Anthropic to authorize access."
            },
        )

    async def async_step_oauth_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Generate OAuth URL and wait for callback."""
        # Initialize OAuth handler
        self._oauth_handler = OAuthHandler(
            self.hass,
            OAUTH_CLIENT_ID,
            OAUTH_CLIENT_SECRET,
        )

        # Generate state for CSRF protection
        self._oauth_state = secrets.token_urlsafe(32)

        # Get redirect URI (Home Assistant callback URL)
        redirect_uri = f"{self.hass.config.external_url}/auth/external/callback"

        # Generate authorization URL
        auth_url = self._oauth_handler.get_authorization_url(
            redirect_uri=redirect_uri,
            state=self._oauth_state,
        )

        return self.async_external_step(
            step_id="oauth_callback",
            url=auth_url,
        )

    async def async_step_oauth_callback(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3: Handle OAuth callback and validate tokens."""
        if user_input is None:
            return self.async_abort(reason="oauth_error")

        # Verify state for CSRF protection
        if user_input.get("state") != self._oauth_state:
            _LOGGER.error("OAuth state mismatch - possible CSRF attack")
            return self.async_abort(reason="oauth_error")

        # Get authorization code
        code = user_input.get("code")
        if not code:
            _LOGGER.error("No authorization code received")
            return self.async_abort(reason="oauth_error")

        errors = {}

        try:
            # Exchange code for tokens
            redirect_uri = f"{self.hass.config.external_url}/auth/external/callback"
            token_data = await self._oauth_handler.handle_oauth_callback(
                code=code,
                redirect_uri=redirect_uri,
            )

            # Validate we got the necessary tokens
            if not token_data.get("access_token"):
                raise OAuthTokenError("No access token received")

            # Store tokens in config entry
            config_data = {
                CONF_WORKING_DIR: DEFAULT_WORKING_DIR,
            }
            config_data = self._oauth_handler.store_tokens(config_data)

            return self.async_create_entry(
                title="Claude Code Terminal",
                data=config_data,
            )

        except OAuthTokenError as err:
            _LOGGER.error("OAuth token error: %s", err)
            errors["base"] = "auth_failed"
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception during OAuth callback: %s", err)
            errors["base"] = "unknown"

        # If we got here, something went wrong
        return self.async_abort(reason="oauth_error")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Claude Code Terminal."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Validate working directory
            working_dir = user_input.get(CONF_WORKING_DIR, DEFAULT_WORKING_DIR)
            if working_dir not in ALLOWED_WORKING_DIRS:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._get_options_schema(),
                    errors={"base": "invalid_working_dir"},
                )

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self) -> vol.Schema:
        """Return options schema."""
        return vol.Schema(
            {
                vol.Optional(
                    CONF_WORKING_DIR,
                    default=self.config_entry.options.get(
                        CONF_WORKING_DIR, DEFAULT_WORKING_DIR
                    ),
                ): vol.In(ALLOWED_WORKING_DIRS),
            }
        )


class OAuthTokenError(HomeAssistantError):
    """Error to indicate OAuth token issues."""
