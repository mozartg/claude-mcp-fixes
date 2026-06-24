# Agent Context: Claude Desktop ENAMETOOLONG Fix

## What Happened
- Date: 2026-06-23
- Claude Desktop Cowork local agent mode was broken with `spawn ENAMETOOLONG` (errno -4064)
- The rpm plugin cache had 41 plugins, exceeding Windows' CreateProcess command line limit of 32,767 chars
- The fix: prune the rpm cache manifest.json from 41 plugins to 3 plugins, delete corresponding directories
- Cloud marketplace has 10 plugins; on restart the app will re-download to 10 plugins, which is SAFE

## Where to Find the Fix
- GitHub repo: https://github.com/mozartg/claude-mcp-fixes
- Local workspace: C:\Users\mozar\Documents\kimi\workspace\CLAUDE_ENAMETOOLONG_FIX.md
- Monitoring script: C:\Users\mozar\Documents\kimi\workspace\claude_log_monitor.py
- Pruning script: C:\Users\mozar\Documents\kimi\workspace\prune_rpm_cache.py

## Key Paths
- rpm cache: `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\local-agent-mode-sessions\<session>\<artifact>\rpm\`
- manifest.json: in the rpm directory above
- main.log: `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\main.log`

## Monitoring
- Cron job: `67fd0c80-3d0c-485f-87df-f8d6006d88e0`
- Runs at 7:13 AM and 7:13 PM daily (America/New_York)
- Checks for ENAMETOOLONG errors and plugin count > 25

## If This Happens Again
1. Kill Claude Desktop
2. Run `python C:\Users\mozar\Documents\kimi\workspace\prune_rpm_cache.py`
3. Restart Claude Desktop
4. Check main.log for errors

## Web App Plugin Management vs Desktop Cache
- The web app (`claude.ai`) plugin settings are SEPARATE from the Cowork desktop cache
- The `rpm` directory is the local agent plugin cache used by Cowork
- Clearing web app plugins does NOT clear the desktop `rpm` cache
- Desktop cache syncs from `knowledge-work-plugins` marketplace (10 plugins currently)

## Approved Action for Future Agents
- You are authorized to run the pruning script if ENAMETOOLONG is detected
- You are authorized to check and modify the rpm cache manifest.json
- You do not need to ask permission before pruning the cache if the error is present
