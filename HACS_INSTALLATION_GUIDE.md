# HACS Installation Guide for Claude Code Terminal

## Issue: "Integration repository structure for dev is not compliant"

This error typically means HACS cannot validate the repository structure. Here's how to fix it:

## Solution 1: Use Local Installation (Recommended for Development)

Since this is a local development version, **don't use HACS yet**. Instead, install manually:

### Manual Installation Steps:

1. **Copy the integration to Home Assistant**:
   ```bash
   cp -r /Users/davidattaie/Dev/homeassistant/custom_components/claude_code_terminal \
         /path/to/homeassistant/config/custom_components/
   ```

2. **Restart Home Assistant**

3. **Add Integration**:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Claude Code Terminal"
   - Follow setup wizard

## Solution 2: Prepare for HACS (For Future Release)

To make this HACS-compatible, you need to:

### 1. Create GitHub Repository

```bash
cd /Users/davidattaie/Dev/homeassistant
git init
git add .
git commit -m "Initial commit: Claude Code Terminal integration"
git branch -M main
git remote add origin https://github.com/davidattaie/claude-code-terminal.git
git push -u origin main
```

### 2. Create a Release

HACS requires at least one release:

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 3. Add to HACS as Custom Repository

1. In Home Assistant, go to HACS
2. Click the three dots (⋮) in top right
3. Select "Custom repositories"
4. Add:
   - **Repository**: `https://github.com/davidattaie/claude-code-terminal`
   - **Category**: Integration
5. Click "Add"
6. Search for "Claude Code Terminal" and install

## Solution 3: Verify Structure (Current Setup)

Your current structure is correct:

```
/Users/davidattaie/Dev/homeassistant/
├── hacs.json                           ✓ Present
├── README.md                           ✓ Present
├── info.md                             ✓ Present
├── .github/
│   └── workflows/
│       └── validate.yaml               ✓ Present
└── custom_components/
    └── claude_code_terminal/
        ├── __init__.py                 ✓ Present
        ├── manifest.json               ✓ Present
        ├── const.py                    ✓ Present
        ├── config_flow.py              ✓ Present
        ├── oauth_handler.py            ✓ Present
        ├── terminal_manager.py         ✓ Present
        ├── websocket_handler.py        ✓ Present
        ├── panel.py                    ✓ Present
        ├── strings.json                ✓ Present
        ├── translations/
        │   └── en.json                 ✓ Present
        └── frontend/
            ├── claude-terminal-panel.js ✓ Present
            └── lcars-terminal-styles.css ✓ Present
```

## Why HACS Shows Error for Local Dev

HACS validates repositories by:
1. Checking if it's a valid GitHub repository (with releases)
2. Validating the manifest.json
3. Running hassfest validation

**For local development, you can't use HACS directly.** Use manual installation instead.

## Quick Start (Development Mode)

```bash
# 1. Copy to Home Assistant
sudo cp -r /Users/davidattaie/Dev/homeassistant/custom_components/claude_code_terminal \
           /config/custom_components/

# 2. Restart Home Assistant
# (Use Home Assistant UI or command line)

# 3. Check logs for errors
tail -f /config/home-assistant.log | grep claude_code_terminal
```

## Troubleshooting

### Error: "Failed to load"

Check Python syntax:
```bash
python3 -m py_compile custom_components/claude_code_terminal/__init__.py
```

### Error: "Invalid manifest"

Validate manifest.json:
```bash
cat custom_components/claude_code_terminal/manifest.json | python3 -m json.tool
```

### Error: "Module not found"

Check all imports are correct:
```bash
grep -r "^from \|^import " custom_components/claude_code_terminal/*.py
```

## Next Steps After Manual Installation

1. Configure OAuth credentials in code
2. Test the integration
3. Fix any bugs
4. Create GitHub repository
5. Create releases
6. Then add to HACS

## Current Status

✅ **Code is complete**
✅ **Structure is HACS-compliant**
⏳ **Needs GitHub repository for HACS**
⏳ **Needs OAuth credentials configured**
⏳ **Ready for manual testing**
