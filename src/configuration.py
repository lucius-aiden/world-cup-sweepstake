from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Settings:
    raw: dict[str, Any]
    root_dir: Path

    @property
    def database_path(self) -> Path:
        return self.root_dir / self.raw["storage"]["database_path"]

    @property
    def participants_csv(self) -> Path:
        return self.root_dir / self.raw["storage"]["participants_csv"]

    @property
    def leaderboard_output(self) -> Path:
        return self.root_dir / self.raw["storage"]["leaderboard_output"]

    @property
    def site_output(self) -> Path:
        return self.root_dir / self.raw["storage"]["site_output"]

    @property
    def competition_code(self) -> str:
        return str(self.raw["tournament"]["competition_code"])

    @property
    def season(self) -> int:
        return int(self.raw["tournament"]["season"])

    @property
    def football_provider(self) -> str:
        return str(self.raw["football_api"]["provider"])

    @property
    def football_api_base_url(self) -> str:
        return str(self.raw["football_api"]["base_url"]).rstrip("/")

    @property
    def football_api_key(self) -> str:
        return _require_env(self.raw["football_api"]["api_key_env"])

    @property
    def football_timeout_seconds(self) -> int:
        return int(self.raw["football_api"].get("timeout_seconds", 30))

    @property
    def recent_matches_window_days(self) -> int:
        return int(self.raw["job"].get("recent_matches_window_days", 7))

    @property
    def top_n_summary(self) -> int:
        return int(self.raw["job"].get("top_n_summary", 3))

    @property
    def teams_notifier(self) -> str:
        return str(self.raw["teams"]["notifier"])

    def graph_value(self, section: str, key: str) -> str | None:
        env_name = self.raw[section].get(key)
        if not env_name:
            return None
        return os.getenv(env_name)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings(root_dir: Path | None = None) -> Settings:
    root = (root_dir or Path(__file__).resolve().parent.parent).resolve()
    settings_path = root / "config" / "settings.yaml"
    with settings_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    configure_logging(raw["app"].get("log_level", "INFO"))
    return Settings(raw=raw, root_dir=root)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
