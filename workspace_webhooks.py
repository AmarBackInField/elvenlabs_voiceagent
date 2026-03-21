"""
ElevenLabs workspace webhooks (post-call, etc.).
API: GET/POST /v1/workspace/webhooks
"""

from typing import Any, Dict, Optional

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class WorkspaceWebhookService(BaseClient):
    """Manage workspace-level webhooks used by ConvAI (e.g. post-call)."""

    ENDPOINT = "/v1/workspace/webhooks"

    def __init__(self, config: ElevenLabsConfig):
        super().__init__(config, logger_name="elevenlabs.workspace_webhooks")

    def list_webhooks(self, include_usages: bool = False) -> Dict[str, Any]:
        """List all workspace webhooks."""
        with APICallLogger(self.logger, "List workspace webhooks"):
            params = {"include_usages": "true"} if include_usages else None
            return self._make_request("GET", self.ENDPOINT, params=params)

    def create_hmac_webhook(self, name: str, webhook_url: str) -> Dict[str, Any]:
        """
        Create an HMAC-signed workspace webhook.

        Returns webhook_id and webhook_secret (store secret for verifying signatures).
        """
        with APICallLogger(self.logger, "Create workspace webhook", name=name):
            payload = {
                "settings": {
                    "auth_type": "hmac",
                    "name": name,
                    "webhook_url": webhook_url,
                }
            }
            return self._make_request("POST", self.ENDPOINT, data=payload)

    def find_webhook_id_by_url(self, target_url: str) -> Optional[str]:
        """Return enabled webhook_id whose URL matches (ignoring trailing slash)."""
        normalized = (target_url or "").strip().rstrip("/")
        if not normalized:
            return None
        data = self.list_webhooks()
        for w in data.get("webhooks") or []:
            if w.get("is_disabled"):
                continue
            wurl = (w.get("webhook_url") or "").strip().rstrip("/")
            if wurl == normalized:
                return w.get("webhook_id")
        return None
