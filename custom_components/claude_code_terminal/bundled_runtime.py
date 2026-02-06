"""Bundled Node.js runtime and Claude CLI manager."""
from __future__ import annotations

import asyncio
import logging
import os
import platform
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Node.js versions and download URLs
NODE_VERSION = "20.11.0"
NODE_URLS = {
    "linux-x64": f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-x64.tar.xz",
    "linux-arm64": f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-arm64.tar.xz",
    "linux-armv7l": f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-armv7l.tar.xz",
    "darwin-x64": f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-darwin-x64.tar.gz",
    "darwin-arm64": f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-darwin-arm64.tar.gz",
}


class BundledRuntime:
    """Manage bundled Node.js runtime and Claude CLI."""

    def __init__(self, hass: HomeAssistant, integration_path: Path) -> None:
        """Initialize bundled runtime manager."""
        self.hass = hass
        self.integration_path = integration_path
        self.runtime_path = integration_path / "runtime"
        self.node_path = self.runtime_path / "node"
        self.claude_path = self.runtime_path / "claude"
        self._session: aiohttp.ClientSession = async_get_clientsession(hass)

    @property
    def node_binary(self) -> Path:
        """Get path to Node.js binary."""
        return self.node_path / "bin" / "node"

    @property
    def npm_binary(self) -> Path:
        """Get path to npm binary."""
        return self.node_path / "bin" / "npm"

    @property
    def claude_binary(self) -> Path:
        """Get path to Claude CLI."""
        return self.claude_path / "node_modules" / ".bin" / "claude"

    def is_installed(self) -> bool:
        """Check if runtime is already installed."""
        return (
            self.node_binary.exists()
            and self.node_binary.is_file()
            and self.claude_binary.exists()
            and os.access(self.node_binary, os.X_OK)
        )

    async def install(self) -> None:
        """Download and install Node.js and Claude CLI."""
        _LOGGER.info("Installing bundled Node.js and Claude CLI...")

        try:
            # Create runtime directory
            self.runtime_path.mkdir(parents=True, exist_ok=True)

            # Install Node.js
            if not self.node_binary.exists():
                await self._install_nodejs()

            # Install Claude CLI
            if not self.claude_binary.exists():
                await self._install_claude_cli()

            # Verify installation
            if not self.is_installed():
                raise RuntimeError("Installation verification failed")

            _LOGGER.info("Bundled runtime installation complete")

        except Exception as err:
            _LOGGER.error("Failed to install bundled runtime: %s", err)
            # Cleanup on failure
            if self.runtime_path.exists():
                shutil.rmtree(self.runtime_path, ignore_errors=True)
            raise

    async def _install_nodejs(self) -> None:
        """Download and extract Node.js."""
        _LOGGER.info("Downloading Node.js v%s...", NODE_VERSION)

        # Detect platform
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Map machine types
        if machine in ("x86_64", "amd64"):
            machine = "x64"
        elif machine in ("aarch64", "arm64"):
            machine = "arm64"
        elif machine.startswith("arm"):
            machine = "armv7l"

        platform_key = f"{system}-{machine}"
        node_url = NODE_URLS.get(platform_key)

        if not node_url:
            raise RuntimeError(
                f"Unsupported platform: {platform_key}. "
                f"Supported: {list(NODE_URLS.keys())}"
            )

        # Download Node.js
        download_path = self.runtime_path / f"node.tar.xz"
        await self._download_file(node_url, download_path)

        # Extract Node.js
        _LOGGER.info("Extracting Node.js...")
        extract_path = self.runtime_path / "node_temp"
        extract_path.mkdir(exist_ok=True)

        # Run extraction in executor (blocking operation)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._extract_tarball, download_path, extract_path
        )

        # Move to final location
        extracted_dir = list(extract_path.glob("node-v*"))[0]
        if self.node_path.exists():
            shutil.rmtree(self.node_path)
        shutil.move(str(extracted_dir), str(self.node_path))

        # Cleanup
        shutil.rmtree(extract_path, ignore_errors=True)
        download_path.unlink(missing_ok=True)

        # Make binaries executable
        os.chmod(self.node_binary, 0o755)
        os.chmod(self.npm_binary, 0o755)

        _LOGGER.info("Node.js installed successfully")

    async def _install_claude_cli(self) -> None:
        """Install Claude CLI using npm."""
        _LOGGER.info("Installing Claude CLI...")

        # Create claude installation directory
        self.claude_path.mkdir(parents=True, exist_ok=True)

        # Prepare npm install command
        env = os.environ.copy()
        env["PATH"] = f"{self.node_path / 'bin'}:{env.get('PATH', '')}"
        env["npm_config_prefix"] = str(self.claude_path)

        # Install Claude CLI
        cmd = [
            str(self.npm_binary),
            "install",
            "--prefix",
            str(self.claude_path),
            "@anthropic-ai/claude-code",
            "--production",
            "--no-save",
            "--no-audit",
            "--no-fund",
        ]

        _LOGGER.info("Running: %s", " ".join(cmd))

        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.claude_path),
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            _LOGGER.error("npm install failed: %s", stderr.decode())
            raise RuntimeError(f"Failed to install Claude CLI: {stderr.decode()}")

        # Make claude binary executable
        if self.claude_binary.exists():
            os.chmod(self.claude_binary, 0o755)

        _LOGGER.info("Claude CLI installed successfully")

    async def _download_file(self, url: str, dest: Path) -> None:
        """Download file from URL."""
        _LOGGER.info("Downloading from %s...", url)

        async with self._session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"Download failed: HTTP {response.status}")

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(dest, "wb") as f:
                async for chunk in response.content.iter_chunked(1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        _LOGGER.debug("Downloaded: %.1f%%", percent)

        _LOGGER.info("Download complete: %s", dest.name)

    def _extract_tarball(self, tarball_path: Path, extract_to: Path) -> None:
        """Extract tar.xz or tar.gz file (blocking)."""
        _LOGGER.info("Extracting %s...", tarball_path.name)

        with tarfile.open(tarball_path, "r:*") as tar:
            tar.extractall(extract_to)

    async def cleanup(self) -> None:
        """Remove bundled runtime."""
        _LOGGER.info("Cleaning up bundled runtime...")
        if self.runtime_path.exists():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, shutil.rmtree, self.runtime_path, True
            )
        _LOGGER.info("Bundled runtime removed")

    def get_claude_command(self) -> list[str]:
        """Get command to execute Claude CLI."""
        if not self.is_installed():
            raise RuntimeError("Bundled runtime not installed")

        # Return command as list
        return [str(self.node_binary), str(self.claude_binary)]

    def get_env(self) -> dict[str, str]:
        """Get environment variables for Claude CLI."""
        env = os.environ.copy()
        env["PATH"] = f"{self.node_path / 'bin'}:{env.get('PATH', '')}"
        env["NODE_PATH"] = str(self.claude_path / "node_modules")
        return env
