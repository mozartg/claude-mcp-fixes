import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def check_enametoolong(log_path=None, max_lines=1000):
    """
    Check Claude Desktop main.log for ENAMETOOLONG errors.

    Args:
        log_path: Path to main.log. If None, auto-detects from MSIX cache.
        max_lines: Number of lines to read from the end of the log.

    Returns:
        dict with found (bool), count (int), last_occurrence (str), details (list)
    """
    if log_path is None:
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        log_path = Path(local_appdata) / "Packages" / "Claude_pzs8sxrjxfjjc" / "LocalCache" / "Roaming" / "Claude" / "logs" / "main.log"
    else:
        log_path = Path(log_path)

    if not log_path.exists():
        return {"found": False, "count": 0, "last_occurrence": None, "details": [], "error": "Log file not found"}

    # Read last N lines
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    tail_lines = lines[-max_lines:] if len(lines) > max_lines else lines

    pattern = re.compile(r"spawn ENAMETOOLONG", re.IGNORECASE)
    matches = []

    for line in tail_lines:
        if pattern.search(line):
            timestamp_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
            timestamp = timestamp_match.group(1) if timestamp_match else "unknown"
            matches.append({"timestamp": timestamp, "line": line.strip()})

    return {
        "found": len(matches) > 0,
        "count": len(matches),
        "last_occurrence": matches[-1]["timestamp"] if matches else None,
        "details": matches,
        "log_checked": datetime.now(timezone.utc).isoformat(),
        "log_path": str(log_path)
    }


def check_plugin_count(rpm_dir=None):
    """
    Check the current plugin count in the rpm cache.

    Returns:
        dict with plugin_count, plugin_names, and rpm_dir
    """
    if rpm_dir is None:
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        rpm_dir = Path(local_appdata) / "Packages" / "Claude_pzs8sxrjxfjjc" / "LocalCache" / "Roaming" / "Claude" / "local-agent-mode-sessions"
        sessions = list(rpm_dir.glob("*/"))
        if not sessions:
            return {"error": "No local-agent-mode-sessions found"}
        artifacts = list(sessions[0].glob("*/"))
        if not artifacts:
            return {"error": "No artifacts in session"}
        rpm_dir = artifacts[0] / "rpm"
    else:
        rpm_dir = Path(rpm_dir)

    manifest_path = rpm_dir / "manifest.json"
    if not manifest_path.exists():
        return {"error": "manifest.json not found", "rpm_dir": str(rpm_dir)}

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    plugin_count = len(manifest.get("plugins", []))
    plugin_names = [p["name"] for p in manifest.get("plugins", [])]
    total_chars = sum(len(str(p)) for p in manifest.get("plugins", []))

    return {
        "plugin_count": plugin_count,
        "plugin_names": plugin_names,
        "total_plugin_chars": total_chars,
        "rpm_dir": str(rpm_dir),
        "manifest_path": str(manifest_path),
        "safe": plugin_count <= 25  # Conservative threshold
    }


def main(check_type="both", log_path=None, rpm_dir=None):
    """
    Run monitoring checks.

    check_type: 'enametoolong', 'plugin_count', or 'both'
    """
    results = {}

    if check_type in ("enametoolong", "both"):
        results["enametoolong"] = check_enametoolong(log_path=log_path)

    if check_type in ("plugin_count", "both"):
        results["plugin_count"] = check_plugin_count(rpm_dir=rpm_dir)

    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    check_type = sys.argv[1] if len(sys.argv) > 1 else "both"
    log_path = sys.argv[2] if len(sys.argv) > 2 else None
    rpm_dir = sys.argv[3] if len(sys.argv) > 3 else None

    main(check_type=check_type, log_path=log_path, rpm_dir=rpm_dir)
