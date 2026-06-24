import json
import os
import shutil
import sys
from pathlib import Path


def prune_rpm_cache(keep_names=None, rpm_dir=None):
    """
    Prune Claude Desktop's rpm plugin cache to a specified set of plugins.

    Args:
        keep_names: Set of plugin names to keep (e.g., {"cowork-plugin-management", "desktop-commander", "pdf-viewer"})
        rpm_dir: Path to the rpm directory. If None, auto-detects from MSIX cache.
    """
    if keep_names is None:
        keep_names = {"cowork-plugin-management", "desktop-commander", "pdf-viewer"}

    if rpm_dir is None:
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        rpm_dir = Path(local_appdata) / "Packages" / "Claude_pzs8sxrjxfjjc" / "LocalCache" / "Roaming" / "Claude" / "local-agent-mode-sessions"
        # Auto-detect session and artifact directories
        sessions = list(rpm_dir.glob("*/"))
        if not sessions:
            print("No local-agent-mode-sessions found.")
            return False
        session_dir = sessions[0]
        artifacts = list(session_dir.glob("*/"))
        if not artifacts:
            print(f"No artifacts in session {session_dir.name}")
            return False
        rpm_dir = artifacts[0] / "rpm"
    else:
        rpm_dir = Path(rpm_dir)

    manifest_path = rpm_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"manifest.json not found at {manifest_path}")
        return False

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    original_count = len(manifest["plugins"])
    print(f"Original plugins: {original_count}")

    keep_plugins = []
    remove_ids = []
    seen_names = set()

    for plugin in manifest["plugins"]:
        name = plugin["name"]
        if name in keep_names and name not in seen_names:
            keep_plugins.append(plugin)
            seen_names.add(name)
            print(f"  KEEP: {name} (id: {plugin['id']})")
        else:
            remove_ids.append(plugin["id"])
            print(f"  REMOVE: {name} (id: {plugin['id']})")

    manifest["plugins"] = keep_plugins
    manifest["lastUpdated"] = 0

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest updated: {original_count} -> {len(keep_plugins)} plugins")

    removed_count = 0
    for plugin_id in remove_ids:
        plugin_dir = rpm_dir / plugin_id
        if plugin_dir.exists() and plugin_dir.is_dir():
            shutil.rmtree(plugin_dir)
            removed_count += 1
            print(f"  Deleted: {plugin_dir}")

    print(f"\nDeleted {removed_count} plugin directories")
    remaining_dirs = [d.name for d in rpm_dir.iterdir() if d.is_dir() and d.name.startswith("plugin_")]
    print(f"Remaining plugin directories: {remaining_dirs}")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        keep_names = set(sys.argv[1].split(","))
    else:
        keep_names = None

    if len(sys.argv) > 2:
        rpm_dir = sys.argv[2]
    else:
        rpm_dir = None

    success = prune_rpm_cache(keep_names=keep_names, rpm_dir=rpm_dir)
    sys.exit(0 if success else 1)
