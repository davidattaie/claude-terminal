# Bundled Runtime Information

## Overview

This integration bundles Node.js and Claude CLI to work on HassOS and other locked-down environments where system-level installations aren't possible.

## How It Works

On first setup, the integration automatically:

1. **Detects your platform** (Linux x64/ARM64/ARMv7, macOS x64/ARM64)
2. **Downloads Node.js v20.11.0** (~50MB) from nodejs.org
3. **Extracts to** `custom_components/claude_code_terminal/runtime/`
4. **Installs Claude CLI** via npm into the runtime directory
5. **Verifies installation** and makes binaries executable

## Storage

Total disk space required: **~150-200MB**
- Node.js: ~50MB
- Claude CLI + dependencies: ~100-150MB

Location: `/config/custom_components/claude_code_terminal/runtime/`

## Supported Platforms

- ✅ Linux x86_64 (amd64) - HassOS default
- ✅ Linux ARM64 (aarch64) - Raspberry Pi 4, etc.
- ✅ Linux ARMv7 - Raspberry Pi 3, etc.
- ✅ macOS x64 (Intel Macs)
- ✅ macOS ARM64 (Apple Silicon)

## Installation Process

### First-Time Setup
When you add the integration, you'll see:
```
INFO: Bundled runtime not found, installing...
INFO: Downloading Node.js v20.11.0...
INFO: Extracting Node.js...
INFO: Installing Claude CLI...
INFO: Bundled runtime installation complete
```

This takes **5-10 minutes** depending on your internet speed and system performance.

### Subsequent Startups
The integration checks if runtime exists:
```
INFO: Bundled runtime already installed
```
Startup is instant after first installation.

## Troubleshooting

### Installation Fails

**Symptom**: Integration setup fails with "Failed to install bundled runtime"

**Solutions**:
1. Check internet connection (needs to download from nodejs.org)
2. Verify disk space (need ~200MB free in /config)
3. Check Home Assistant logs for specific error
4. Try removing and re-adding integration

### Unsupported Platform

**Symptom**: Error: "Unsupported platform: xxx-yyy"

**Solution**: Your system architecture isn't supported. Currently supports:
- linux-x64, linux-arm64, linux-armv7l
- darwin-x64, darwin-arm64

### Permission Errors

**Symptom**: "Permission denied" when executing Node.js or Claude

**Solution**: Integration automatically sets executable permissions (0755). If this fails, check Home Assistant has write access to /config directory.

### Slow Installation

**Symptom**: Installation takes longer than 10 minutes

**Possible causes**:
- Slow internet connection
- Slow disk I/O (SD card on Raspberry Pi)
- System under heavy load

**Solution**: Be patient, it should complete. Check logs for progress.

## Manual Cleanup

To remove the bundled runtime:

```bash
# SSH into Home Assistant
cd /config/custom_components/claude_code_terminal
rm -rf runtime/
```

It will be re-downloaded on next integration setup.

## Updating

When a new version of the integration is released:
1. The bundled runtime is **preserved** (not re-downloaded)
2. Only integration code is updated
3. To force re-download: remove `runtime/` directory before update

## Security

- **Node.js binaries** are downloaded from official nodejs.org (verified URLs)
- **Claude CLI** is installed from official npm registry
- **No modifications** to downloaded binaries
- **Checksums**: Not currently verified (future enhancement)

## Performance

- **Memory usage**: ~100-200MB per Claude session
- **CPU usage**: Varies based on Claude Code operations
- **Disk I/O**: Minimal after initial installation

## Why Bundled?

HassOS doesn't allow:
- Installing system packages (apt, npm)
- Running `npm install -g`
- Modifying system paths
- Adding custom binaries

Bundling ensures the integration works **everywhere** Home Assistant runs, without requiring manual setup or system access.

## Alternative: Home Assistant Add-on

If you prefer, a future version could provide an **Add-on** instead of bundled runtime. Add-ons run in Docker containers and can install dependencies normally.

**Pros of Add-on**:
- Cleaner separation
- Easier updates
- Lower integration size

**Cons of Add-on**:
- Only works on HassOS (not manual installs)
- Requires Supervisor
- More complex setup

Currently, bundled runtime works universally.

## Technical Details

### Runtime Structure
```
runtime/
├── node/
│   ├── bin/
│   │   ├── node          # Node.js binary
│   │   └── npm           # npm binary
│   └── lib/              # Node.js libraries
└── claude/
    └── node_modules/
        ├── @anthropic-ai/
        │   └── claude-code/  # Claude CLI package
        └── .bin/
            └── claude        # Claude executable
```

### Environment Variables
The integration sets:
- `PATH`: Includes `runtime/node/bin/`
- `NODE_PATH`: Points to `runtime/claude/node_modules/`
- `npm_config_prefix`: Points to `runtime/claude/`

### Execution
Claude CLI is executed as:
```bash
/path/to/runtime/node/bin/node /path/to/runtime/claude/node_modules/.bin/claude
```

This ensures the bundled Node.js runs the bundled Claude CLI.
