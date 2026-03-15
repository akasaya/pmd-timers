"""Settings persistence service."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from src.engine.session import AppSettings


def _get_config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    config_dir = base / "pmd-timers"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class SettingsService:
    def __init__(self, config_dir: Path | None = None):
        self._dir = config_dir or _get_config_dir()
        self._path = self._dir / "settings.json"

    def load(self) -> AppSettings:
        if not self._path.exists():
            return AppSettings()
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            return AppSettings.from_dict(data)
        except Exception:
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        settings.timers.validate()
        settings.ui.validate()
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, ensure_ascii=False, indent=2)

    def reset(self) -> AppSettings:
        defaults = AppSettings()
        self.save(defaults)
        return defaults
