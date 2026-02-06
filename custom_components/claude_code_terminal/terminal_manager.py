"""Terminal manager for Claude Code PTY processes."""
from __future__ import annotations

import asyncio
import fcntl
import logging
import os
import pty
import resource
import struct
import termios
import time
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import event

from .bundled_runtime import BundledRuntime
from .const import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TIMEOUT,
    MAX_PTY_BUFFER_SIZE,
    ALLOWED_WORKING_DIRS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ClaudeTerminalSession:
    """Represents a single Claude Code terminal session."""

    def __init__(
        self,
        session_id: str,
        working_dir: str,
        output_callback: Callable[[str, bytes], None],
        runtime: BundledRuntime,
    ) -> None:
        """Initialize terminal session."""
        self.session_id = session_id
        self.working_dir = working_dir
        self.output_callback = output_callback
        self.runtime = runtime
        self.master_fd: int | None = None
        self.pid: int | None = None
        self.last_activity = time.time()
        self._reader_task: asyncio.Task | None = None
        self._closed = False

    async def start(self, auth_token: str | None = None) -> None:
        """Start new PTY process with Claude Code."""
        if self.master_fd is not None:
            raise RuntimeError("Session already started")

        # Security: Validate working directory
        if self.working_dir not in ALLOWED_WORKING_DIRS:
            _LOGGER.error(
                "SECURITY: Attempt to use unauthorized working directory: %s",
                self.working_dir
            )
            raise ValueError(f"Working directory not allowed: {self.working_dir}")

        if not os.path.isdir(self.working_dir):
            raise ValueError(f"Working directory does not exist: {self.working_dir}")

        # Security: Prevent path traversal
        real_path = os.path.realpath(self.working_dir)
        if not any(real_path.startswith(allowed) for allowed in ALLOWED_WORKING_DIRS):
            _LOGGER.error(
                "SECURITY: Path traversal attempt detected: %s -> %s",
                self.working_dir,
                real_path
            )
            raise ValueError("Path traversal detected")

        # Spawn PTY process
        try:
            self.pid, self.master_fd = pty.fork()

            if self.pid == 0:
                # Child process - execute Claude Code
                env = self.runtime.get_env()

                # Set authentication token if provided
                if auth_token:
                    env["ANTHROPIC_API_KEY"] = auth_token
                    env["CLAUDE_CODE_AUTH_TOKEN"] = auth_token

                # Security: Set resource limits for child process
                try:
                    # Limit CPU time (10 hours)
                    resource.setrlimit(resource.RLIMIT_CPU, (36000, 36000))
                    # Limit memory (2GB)
                    resource.setrlimit(resource.RLIMIT_AS, (2147483648, 2147483648))
                    # Limit number of processes
                    resource.setrlimit(resource.RLIMIT_NPROC, (100, 100))
                except Exception as err:
                    _LOGGER.warning("Failed to set resource limits: %s", err)

                # Change to working directory
                os.chdir(self.working_dir)

                # Execute Claude Code CLI using bundled runtime
                claude_cmd = self.runtime.get_claude_command()
                os.execvpe(claude_cmd[0], claude_cmd, env)

            # Parent process - set up non-blocking I/O
            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Start output reader task
            self._reader_task = asyncio.create_task(self._read_output())

            _LOGGER.info(
                "Started Claude terminal session %s (PID: %d)",
                self.session_id,
                self.pid,
            )

        except Exception as err:
            _LOGGER.error("Failed to start terminal session: %s", err)
            await self.close()
            raise

    async def _read_output(self) -> None:
        """Read output from PTY and send to callback."""
        loop = asyncio.get_event_loop()

        while not self._closed and self.master_fd is not None:
            try:
                # Use run_in_executor to avoid blocking
                data = await loop.run_in_executor(
                    None, self._read_from_fd, self.master_fd
                )

                if data:
                    self.last_activity = time.time()
                    # Send output to callback
                    self.output_callback(self.session_id, data)
                else:
                    # EOF reached
                    break

            except OSError as err:
                if err.errno != 11:  # EAGAIN
                    _LOGGER.error("PTY read error: %s", err)
                    break
                await asyncio.sleep(0.01)

            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error reading PTY output: %s", err)
                break

        _LOGGER.info("PTY output reader stopped for session %s", self.session_id)

    def _read_from_fd(self, fd: int) -> bytes:
        """Read data from file descriptor (blocking operation)."""
        try:
            return os.read(fd, MAX_PTY_BUFFER_SIZE)
        except OSError as err:
            if err.errno == 11:  # EAGAIN
                return b""
            raise

    async def write(self, data: str | bytes) -> None:
        """Write input to terminal."""
        if self.master_fd is None:
            raise RuntimeError("Session not started")

        if isinstance(data, str):
            data = data.encode("utf-8")

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, os.write, self.master_fd, data)
        self.last_activity = time.time()

    async def resize(self, rows: int, cols: int) -> None:
        """Resize terminal window."""
        if self.master_fd is None:
            raise RuntimeError("Session not started")

        # Set terminal window size
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)

        _LOGGER.debug("Resized terminal %s to %dx%d", self.session_id, rows, cols)

    async def close(self) -> None:
        """Close terminal session and cleanup."""
        if self._closed:
            return

        self._closed = True

        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # Close master FD
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.master_fd = None

        # Kill child process
        if self.pid is not None:
            try:
                os.kill(self.pid, 15)  # SIGTERM
                # Wait briefly for process to exit
                await asyncio.sleep(0.5)
                try:
                    os.kill(self.pid, 9)  # SIGKILL
                except OSError:
                    pass  # Process already dead
            except OSError:
                pass
            self.pid = None

        _LOGGER.info("Closed terminal session %s", self.session_id)


class ClaudeTerminalManager:
    """Manage Claude Code terminal sessions."""

    def __init__(
        self,
        hass: HomeAssistant,
        runtime: BundledRuntime,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        session_timeout: int = DEFAULT_SESSION_TIMEOUT,
    ) -> None:
        """Initialize terminal manager."""
        self.hass = hass
        self.runtime = runtime
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self.sessions: dict[str, ClaudeTerminalSession] = {}
        self._cleanup_task: asyncio.Task | None = None

    def _fire_audit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Fire audit event for logging terminal activity."""
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            data,
        )
        _LOGGER.info("AUDIT: %s - %s", event_type.upper(), data)

    async def start(self) -> None:
        """Start terminal manager."""
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        _LOGGER.info("Claude Terminal Manager started")

    async def spawn_terminal(
        self,
        session_id: str,
        working_dir: str,
        auth_token: str | None,
        output_callback: Callable[[str, bytes], None],
    ) -> None:
        """Spawn new terminal session.

        Args:
            session_id: Unique session identifier
            working_dir: Working directory for terminal
            auth_token: OAuth token for authentication
            output_callback: Callback function for terminal output

        Raises:
            RuntimeError: If max sessions exceeded
            ValueError: If working directory invalid
        """
        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError(
                f"Maximum number of sessions ({self.max_sessions}) reached"
            )

        # Create and start session
        session = ClaudeTerminalSession(
            session_id=session_id,
            working_dir=working_dir,
            output_callback=output_callback,
            runtime=self.runtime,
        )

        try:
            await session.start(auth_token)
            self.sessions[session_id] = session
            _LOGGER.info("Spawned new terminal session: %s", session_id)

            # Audit logging
            self._fire_audit_event("terminal_started", {
                "session_id": session_id,
                "working_dir": working_dir,
                "timestamp": time.time(),
            })

        except Exception as err:
            _LOGGER.error("Failed to spawn terminal session: %s", err)
            # Audit logging for failed attempt
            self._fire_audit_event("terminal_start_failed", {
                "session_id": session_id,
                "working_dir": working_dir,
                "error": str(err),
                "timestamp": time.time(),
            })
            raise

    async def write_to_terminal(self, session_id: str, data: str | bytes) -> None:
        """Send input to terminal session."""
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        await session.write(data)

    async def resize_terminal(self, session_id: str, rows: int, cols: int) -> None:
        """Resize terminal window."""
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        await session.resize(rows, cols)

    async def stop_terminal(self, session_id: str) -> None:
        """Stop and remove terminal session."""
        session = self.sessions.pop(session_id, None)
        if session:
            await session.close()
            _LOGGER.info("Stopped terminal session: %s", session_id)

            # Audit logging
            self._fire_audit_event("terminal_stopped", {
                "session_id": session_id,
                "timestamp": time.time(),
            })

    async def cleanup(self) -> None:
        """Terminate all sessions and stop manager."""
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all sessions
        for session_id in list(self.sessions.keys()):
            await self.stop_terminal(session_id)

        _LOGGER.info("Claude Terminal Manager stopped")

    async def _cleanup_loop(self) -> None:
        """Periodically cleanup idle sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_time = time.time()
                idle_sessions = []

                for session_id, session in self.sessions.items():
                    idle_time = current_time - session.last_activity
                    if idle_time > self.session_timeout:
                        idle_sessions.append(session_id)
                        _LOGGER.info(
                            "Session %s idle for %d seconds, cleaning up",
                            session_id,
                            idle_time,
                        )

                # Remove idle sessions
                for session_id in idle_sessions:
                    await self.stop_terminal(session_id)

            except asyncio.CancelledError:
                break
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Error in cleanup loop: %s", err)
