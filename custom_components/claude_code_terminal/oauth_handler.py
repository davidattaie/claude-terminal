"""OAuth 2.0 handler for Claude Code / Anthropic API."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timedelta

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# OAuth endpoints
AUTHORIZATION_URL = "https://anthropic.com/oauth/authorize"
TOKEN_URL = "https://anthropic.com/oauth/token"
SCOPES = ["api.full_access"]  # Adjust based on actual Claude Code API scopes


class OAuthHandler:
    """Handle OAuth 2.0 authentication for Claude Code."""

    def __init__(self, hass: HomeAssistant, client_id: str, client_secret: str) -> None:
        """Initialize OAuth handler."""
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self._session: ClientSession = async_get_clientsession(hass)
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: datetime | None = None

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL for user.

        Args:
            redirect_uri: The callback URL after authorization
            state: CSRF protection state parameter

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{AUTHORIZATION_URL}?{query_string}"

    async def handle_oauth_callback(
        self, code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: The same redirect URI used in authorization

        Returns:
            Dictionary containing access_token, refresh_token, and expires_in

        Raises:
            Exception: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with self._session.post(TOKEN_URL, data=data) as response:
            if response.status != 200:
                error_text = await response.text()
                _LOGGER.error("OAuth token exchange failed: %s", error_text)
                raise Exception(f"Token exchange failed: {response.status}")

            token_data = await response.json()

            # Store tokens
            self._access_token = token_data.get("access_token")
            self._refresh_token = token_data.get("refresh_token")

            # Calculate expiration time
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            _LOGGER.info("Successfully obtained OAuth tokens")
            return token_data

    async def refresh_access_token(self) -> dict[str, Any]:
        """Refresh expired access token using refresh token.

        Returns:
            Dictionary containing new access_token and expires_in

        Raises:
            Exception: If token refresh fails
        """
        if not self._refresh_token:
            raise Exception("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with self._session.post(TOKEN_URL, data=data) as response:
            if response.status != 200:
                error_text = await response.text()
                _LOGGER.error("OAuth token refresh failed: %s", error_text)
                raise Exception(f"Token refresh failed: {response.status}")

            token_data = await response.json()

            # Update tokens
            self._access_token = token_data.get("access_token")
            if "refresh_token" in token_data:
                self._refresh_token = token_data["refresh_token"]

            # Update expiration time
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            _LOGGER.info("Successfully refreshed OAuth token")
            return token_data

    async def get_valid_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token

        Raises:
            Exception: If no token available or refresh fails
        """
        if not self._access_token:
            raise Exception("No access token available")

        # Check if token is expired or will expire soon (within 5 minutes)
        if self._token_expires_at:
            time_until_expiry = self._token_expires_at - datetime.now()
            if time_until_expiry < timedelta(minutes=5):
                _LOGGER.info("Access token expired or expiring soon, refreshing")
                await self.refresh_access_token()

        return self._access_token

    def store_tokens(self, config_entry_data: dict[str, Any]) -> dict[str, Any]:
        """Store tokens in config entry data.

        Args:
            config_entry_data: Dictionary to update with token data

        Returns:
            Updated config entry data
        """
        config_entry_data.update({
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
        })
        return config_entry_data

    def load_tokens(self, config_entry_data: dict[str, Any]) -> None:
        """Load tokens from config entry data.

        Args:
            config_entry_data: Dictionary containing stored token data
        """
        self._access_token = config_entry_data.get("access_token")
        self._refresh_token = config_entry_data.get("refresh_token")

        expires_at_str = config_entry_data.get("token_expires_at")
        if expires_at_str:
            self._token_expires_at = datetime.fromisoformat(expires_at_str)
