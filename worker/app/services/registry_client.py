import logging
import uuid
from typing import List, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class RegistryClient:
    """Клиент для запросов в Registry (source of truth)."""

    def __init__(self):
        self._client = httpx.Client(
            base_url=settings.registry_service_url,
            timeout=30.0,
        )

    def get_user_permission_groups(self, user_id: uuid.UUID) -> List[dict]:
        resp = self._client.get(f"/users/{user_id}/permission-groups")
        resp.raise_for_status()
        return resp.json()

    def check_conflicts(
        self, user_current_groups: list[str], new_group_id: uuid.UUID
    ) -> Tuple[bool, str | None]:
        resp = self._client.post(
            "/permission-groups/check-conflicts",
            json={
                "user_current_groups": user_current_groups,
                "new_group_id": str(new_group_id),
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("has_conflict", False), data.get("reason")

    def grant_permission_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        resp = self._client.post(f"/users/{user_id}/permission-groups/{group_id}/grant")
        resp.raise_for_status()
        return True

    def revoke_permission_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        resp = self._client.post(
            f"/users/{user_id}/permission-groups/{group_id}/revoke"
        )
        resp.raise_for_status()
        return True

    def close(self):
        self._client.close()

