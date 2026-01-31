"""Safe file backup and restore utilities."""

import os
import shutil
from datetime import datetime
from typing import Optional


def create_backup(filepath: str, suffix: Optional[str] = None) -> str:
    """Create a backup of a file before modification.

    Args:
        filepath: Path to the file to backup
        suffix: Optional suffix for backup file (default: timestamp)

    Returns:
        Path to the backup file
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot backup: {filepath} does not exist")

    if suffix is None:
        suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = f"{filepath}.{suffix}.bak"

    # Avoid overwriting existing backups
    counter = 1
    while os.path.exists(backup_path):
        backup_path = f"{filepath}.{suffix}_{counter}.bak"
        counter += 1

    shutil.copy2(filepath, backup_path)
    return backup_path


def restore_backup(backup_path: str, original_path: Optional[str] = None) -> str:
    """Restore a file from backup.

    Args:
        backup_path: Path to the backup file
        original_path: Path to restore to (default: derived from backup path)

    Returns:
        Path to the restored file
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    if original_path is None:
        # Remove .bak and timestamp suffix to get original path
        original_path = backup_path
        if original_path.endswith(".bak"):
            original_path = original_path[:-4]
        # Remove timestamp suffix if present
        parts = original_path.rsplit(".", 1)
        if len(parts) == 2 and parts[1].startswith("20"):  # Year prefix
            original_path = parts[0]

    shutil.copy2(backup_path, original_path)
    return original_path


def list_backups(filepath: str) -> list[str]:
    """List all backups for a file.

    Args:
        filepath: Path to the original file

    Returns:
        List of backup file paths, sorted by modification time (newest first)
    """
    directory = os.path.dirname(filepath) or "."
    basename = os.path.basename(filepath)

    backups = []
    for f in os.listdir(directory):
        if f.startswith(basename) and f.endswith(".bak"):
            backups.append(os.path.join(directory, f))

    return sorted(backups, key=os.path.getmtime, reverse=True)
