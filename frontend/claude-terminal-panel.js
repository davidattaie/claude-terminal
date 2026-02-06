/**
 * Claude Code Terminal Panel
 * LitElement-based custom panel with xterm.js terminal
 */

import { LitElement, html, css } from "https://cdn.skypack.dev/lit@2.0.2";
import { Terminal } from "https://cdn.skypack.dev/xterm@5.0.0";
import { FitAddon } from "https://cdn.skypack.dev/xterm-addon-fit@0.6.0";
import { WebLinksAddon } from "https://cdn.skypack.dev/xterm-addon-web-links@0.7.0";

class ClaudeTerminalPanel extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      _sessionId: { type: String },
      _connected: { type: Boolean },
      _loading: { type: Boolean },
      _error: { type: String },
    };
  }

  constructor() {
    super();
    this._sessionId = null;
    this._connected = false;
    this._loading = false;
    this._error = null;
    this._terminal = null;
    this._fitAddon = null;
    this._subscriptionId = null;
  }

  static get styles() {
    return css`
      :host {
        display: block;
        height: 100vh;
        width: 100%;
        background-color: #000000;
      }

      /* Import LCARS styles */
      @import url('./lcars-terminal-styles.css');
    `;
  }

  render() {
    return html`
      <link rel="stylesheet" href="/local/community/claude_code_terminal/lcars-terminal-styles.css">

      <div class="claude-terminal-panel">
        <!-- LCARS Header -->
        <div class="lcars-header">
          <div class="lcars-header-cap"></div>
          <div class="lcars-header-title">LCARS Computer Interface</div>
          <div class="lcars-status-indicator">
            <span>${this._connected ? 'ONLINE' : 'OFFLINE'}</span>
            <div class="lcars-status-dot ${this._connected ? 'online' : ''}"></div>
          </div>
        </div>

        <!-- Terminal Container -->
        <div class="terminal-container">
          <div class="terminal-border">
            ${this._renderContent()}
          </div>
        </div>

        <!-- LCARS Footer -->
        <div class="lcars-footer">
          <div class="lcars-footer-cap"></div>
          <div class="lcars-footer-text">
            CLAUDE CODE TERMINAL v1.0 | SESSION: ${this._sessionId || 'NONE'}
          </div>
        </div>
      </div>
    `;
  }

  _renderContent() {
    if (this._error) {
      return html`
        <div class="terminal-error">
          <div class="terminal-error-title">TERMINAL ERROR</div>
          <div>${this._error}</div>
        </div>
      `;
    }

    if (this._loading) {
      return html`
        <div class="terminal-loading">
          INITIALIZING TERMINAL
        </div>
      `;
    }

    return html`
      <div class="terminal-wrapper" id="terminal"></div>
    `;
  }

  firstUpdated() {
    this._initTerminal();
    this._startSession();

    // Handle window resize
    window.addEventListener('resize', () => this._handleResize());

    // Play LCARS sound effect if available
    this._playLcarsSound();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this._cleanup();
  }

  _initTerminal() {
    const terminalElement = this.shadowRoot.getElementById('terminal');
    if (!terminalElement) {
      return;
    }

    // Create terminal with LCARS theme
    this._terminal = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      fontSize: 14,
      theme: {
        background: '#000000',
        foreground: '#FF9900',
        cursor: '#FF9900',
        cursorAccent: '#000000',
        selection: 'rgba(255, 153, 0, 0.3)',
        black: '#000000',
        red: '#CC6666',
        green: '#FF9966',
        yellow: '#FFAA00',
        blue: '#9999FF',
        magenta: '#CC99CC',
        cyan: '#CC99FF',
        white: '#FFCC99',
        brightBlack: '#333333',
        brightRed: '#CC6666',
        brightGreen: '#FF9966',
        brightYellow: '#FFD700',
        brightBlue: '#9999FF',
        brightMagenta: '#CC99FF',
        brightCyan: '#CCCCFF',
        brightWhite: '#FFCC99',
      },
      allowProposedApi: true,
    });

    // Add fit addon for responsive sizing
    this._fitAddon = new FitAddon();
    this._terminal.loadAddon(this._fitAddon);

    // Add web links addon
    const webLinksAddon = new WebLinksAddon();
    this._terminal.loadAddon(webLinksAddon);

    // Open terminal in DOM
    this._terminal.open(terminalElement);

    // Fit terminal to container
    setTimeout(() => {
      this._fitAddon.fit();
    }, 100);

    // Handle terminal input
    this._terminal.onData((data) => {
      this._sendInput(data);
    });

    // Welcome message
    this._terminal.writeln('\x1b[1;33m╔═══════════════════════════════════════════════════════╗\x1b[0m');
    this._terminal.writeln('\x1b[1;33m║\x1b[0m     \x1b[1;36mCLAUDE CODE TERMINAL - LCARS INTERFACE\x1b[0m         \x1b[1;33m║\x1b[0m');
    this._terminal.writeln('\x1b[1;33m╚═══════════════════════════════════════════════════════╝\x1b[0m');
    this._terminal.writeln('');
    this._terminal.writeln('\x1b[1;32mInitializing connection...\x1b[0m');
    this._terminal.writeln('');
  }

  async _startSession() {
    this._loading = true;
    this.requestUpdate();

    try {
      // Subscribe to WebSocket messages
      this._subscriptionId = await this.hass.connection.subscribeMessage(
        (message) => this._handleWebSocketMessage(message),
        {
          type: 'claude_terminal/start',
        }
      );

      // WebSocket subscription handles the response
    } catch (err) {
      console.error('Failed to start terminal session:', err);
      this._error = `Failed to start session: ${err.message}`;
      this._loading = false;
      this.requestUpdate();
    }
  }

  _handleWebSocketMessage(message) {
    if (message.type === 'claude_terminal/output') {
      // Terminal output from backend
      if (this._terminal && message.data) {
        this._terminal.write(message.data);
      }
    } else if (message.session_id) {
      // Session started successfully
      this._sessionId = message.session_id;
      this._connected = true;
      this._loading = false;
      this.requestUpdate();

      // Send resize event after connection
      setTimeout(() => {
        this._handleResize();
      }, 100);
    }
  }

  async _sendInput(data) {
    if (!this._sessionId || !this._connected) {
      return;
    }

    try {
      await this.hass.callWS({
        type: 'claude_terminal/input',
        session_id: this._sessionId,
        data: data,
      });
    } catch (err) {
      console.error('Failed to send input:', err);
    }
  }

  async _handleResize() {
    if (!this._terminal || !this._fitAddon || !this._sessionId) {
      return;
    }

    // Fit terminal to container
    this._fitAddon.fit();

    // Send resize event to backend
    const { rows, cols } = this._terminal;

    try {
      await this.hass.callWS({
        type: 'claude_terminal/resize',
        session_id: this._sessionId,
        rows: rows,
        cols: cols,
      });
    } catch (err) {
      console.error('Failed to resize terminal:', err);
    }
  }

  async _cleanup() {
    // Stop terminal session
    if (this._sessionId) {
      try {
        await this.hass.callWS({
          type: 'claude_terminal/stop',
          session_id: this._sessionId,
        });
      } catch (err) {
        console.error('Failed to stop terminal:', err);
      }
    }

    // Unsubscribe from WebSocket
    if (this._subscriptionId) {
      await this.hass.connection.unsubscribeMessage(this._subscriptionId);
    }

    // Dispose terminal
    if (this._terminal) {
      this._terminal.dispose();
      this._terminal = null;
    }

    this._sessionId = null;
    this._connected = false;
  }

  _playLcarsSound() {
    // Check if LCARS sound effects are enabled
    const soundEntity = this.hass.states['input_boolean.lcars_sound'];
    if (!soundEntity || soundEntity.state !== 'on') {
      return;
    }

    // Play LCARS beep sound if lcars.js is available
    if (window.playLcarsSound) {
      window.playLcarsSound('beep');
    }
  }
}

customElements.define('claude-terminal-panel', ClaudeTerminalPanel);

// Register panel
window.customPanels = window.customPanels || [];
window.customPanels.push({
  name: 'claude-terminal-panel',
  element: 'claude-terminal-panel',
});
