from __future__ import annotations

import logging
from pathlib import Path

import requests

from .configuration import Settings

LOGGER = logging.getLogger(__name__)


class SharePointClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token: str | None = None

    def upload_leaderboard(self, file_path: Path) -> None:
        site_id = self.settings.graph_value("sharepoint", "site_id_env")
        drive_id = self.settings.graph_value("sharepoint", "drive_id_env")
        item_id = self.settings.graph_value("sharepoint", "file_item_id_env")
        remote_path = self.settings.graph_value("sharepoint", "file_path_env")
        if not site_id or not drive_id or (not item_id and not remote_path):
            LOGGER.warning("SharePoint target not configured; skipping upload.")
            return

        target = (
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/content"
            if item_id
            else f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{remote_path}:/content"
        )
        response = requests.put(
            target,
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            data=file_path.read_bytes(),
            timeout=60,
        )
        response.raise_for_status()
        LOGGER.info("Uploaded leaderboard to SharePoint.")

    def _token(self) -> str:
        if self._access_token:
            return self._access_token
        tenant_id = self.settings.graph_value("sharepoint", "tenant_id_env")
        client_id = self.settings.graph_value("sharepoint", "client_id_env")
        client_secret = self.settings.graph_value("sharepoint", "client_secret_env")
        if not tenant_id or not client_id or not client_secret:
            raise RuntimeError("Missing Microsoft Graph app-only credentials.")
        response = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": self.settings.raw["sharepoint"]["scope"],
            },
            timeout=30,
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token

