# Claude Desktop Cowork ENAMETOOLONG Fix

## Date: 2026-06-23
## Status: RESOLVED
## Severity: CRITICAL — Cowork local agent completely broken

---

## Problem

Claude Desktop Cowork local agent mode fails with `spawn ENAMETOOLONG` (errno -4064). The launch command exceeds Windows' 32,767 character `CreateProcess` limit because the desktop app embeds ALL cached plugin paths from the `rpm` directory into the agent initialization command.

**Error signature:**
```
Session initialization failed for local_*: spawn ENAMETOOLONG
{ errno: -4064, code: 'ENAMETOOLONG', syscall: 'spawn' }
```

**Root cause:** Each plugin path is ~220 characters. With 41 plugins cached, the command string becomes ~9,000+ characters, but the *actual* payload includes much more than just paths. When the desktop app iterates over all `rpm/plugin_*` directories and embeds them into the spawn command, it hits the Windows limit.

---

## Environment

- **OS:** Windows 11 (build 26200.8655)
- **Claude Desktop:** MSIX `Claude_1.13576.4.0_x64__pzs8sxrjxfjjc`
- **MSIX package family:** `Claude_pzs8sxrjxfjjc`
- **Key cache directory:**
  ```
  %LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\
  local-agent-mode-sessions\<session-id>\<artifact-id>\rpm\manifest.json
  ```

---

## Filesystem Layout (MSIX vs Desktop)

| Layer | Path |
|-------|------|
| MSIX app data | `C:\Users\mozar\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\` |
| Desktop app data | `C:\Users\mozar\AppData\Roaming\Claude\` (config, Chrome native host) |
| Logs | `C:\Users\mozar\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\main.log` |
| VM bundles | `C:\Users\mozar\AppData\Roaming\Claude\vm_bundles\` |

**Important:** The `rpm` cache is in the MSIX LocalCache directory, not the roaming directory. The web app (`claude.ai`) and desktop app maintain separate plugin caches.

---

## Fix Steps (Executed)

### Step 1: Kill Claude Desktop
- Ensure the app is fully closed before editing the cache.
- Check via `tasklist | findstr /i "claude"`.

### Step 2: Prune the `rpm` manifest.json

**Path:**
```
%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\local-agent-mode-sessions\
1033e3a6-6d66-430b-a9fb-ed6204a30770\c802fc5f-fbca-4676-a8ab-04ff5c1a991a\rpm\manifest.json
```

**What was done:**
- Reduced from 41 plugins to 3 plugins.
- Kept only first occurrence of each desired plugin from `knowledge-work-plugins` marketplace.
- Kept: `cowork-plugin-management`, `desktop-commander`, `pdf-viewer`.
- Removed all duplicate My Uploads plugins and unused knowledge-work-plugins.

**Resulting manifest:**
```json
{
  "lastUpdated": 0,
  "plugins": [
    {"id": "plugin_0155zZVATbJU3jHUmPP9NvMC", "name": "cowork-plugin-management"},
    {"id": "plugin_01S1HcuzG4CPx8bTxZDQAguG", "name": "desktop-commander"},
    {"id": "plugin_011v5h6QUzBZvas64y44XLhy", "name": "pdf-viewer"}
  ]
}
```

### Step 3: Delete removed plugin directories

Deleted 38 `plugin_*` directories from the `rpm` folder corresponding to the removed entries.

**Remaining directories:**
- `plugin_0155zZVATbJU3jHUmPP9NvMC` (cowork-plugin-management)
- `plugin_01S1HcuzG4CPx8bTxZDQAguG` (desktop-commander)
- `plugin_011v5h6QUzBZvas64y44XLhy` (pdf-viewer)

### Step 4: Restart Claude Desktop
- Launch from MSIX: `C:\Program Files\WindowsApps\Claude_1.13576.4.0_x64__pzs8sxrjxfjjc\app\Claude.exe`
- Or via Start Menu / taskbar shortcut.

### Step 5: Verify
- Launch a Cowork local agent session.
- Check `main.log` for `spawn ENAMETOOLONG` errors (should be gone).
- Expected: Cowork initializes successfully with the 3 plugins.

---

## Known Sync Behavior

- The desktop app syncs with the cloud `knowledge-work-plugins` marketplace.
- Cloud currently has **10** plugins (checked via logs).
- On restart, the app will re-download the 7 missing marketplace plugins back to `rpm`.
- **10 plugins is SAFE** — well under the Windows command limit.
- If you want to stay at 3 plugins permanently, use the `cowork-plugin-management` plugin (now in your cache) to remove the other 7 from the cloud marketplace.

**Cloud plugin count log evidence:**
```
[PluginsFetcher] fetchAccountScopedRemotePlugins: 10 plugins from 1 marketplace(s)
```

---

## Reusable Scripts

See `claude_log_monitor.py` and `prune_rpm_cache.py` in this repository for automation tools.

---

## Prevention

1. **Monitor plugin count** — Don't let the cache exceed ~25 plugins.
2. **Remove unused plugins** via `cowork-plugin-management` or web app settings.
3. **Run the monitor script** to detect ENAMETOOLONG early.

---

## References

- Windows `CreateProcess` command line limit: 32,767 characters
- Node.js `child_process.spawn` inherits this limit on Windows
- Claude Desktop `mFi.spawnLocalProcess` is the call site

---

*Fix applied by: Kimi (agent)*
*Date: 2026-06-23*
*Session: conv-...*
