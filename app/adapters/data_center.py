from __future__ import annotations

from typing import Any

from app.adapters.filter_http import FilterHttpAdapter
from app.utils.response import _Exception
from config import settings


class DataCenterAdapter(FilterHttpAdapter):
    """对接 data-center-backend：/api/filter* 用 X-Api-Key，业务面用登录 JWT。"""

    adapter_label = 'data_center'

    def __init__(self) -> None:
        if not (
            settings.DATA_CENTER_BASE_URL
            and settings.DATA_CENTER_API_KEY
            and settings.DATA_CENTER_TOKEN
        ):
            raise RuntimeError(
                'DATA_CENTER_BASE_URL / DATA_CENTER_API_KEY / DATA_CENTER_TOKEN required'
            )
        super().__init__(
            base_url=settings.DATA_CENTER_BASE_URL,
            timeout=settings.DATA_CENTER_TIMEOUT,
        )
        self._api_key = settings.DATA_CENTER_API_KEY.strip()
        self._login_auth = self._bearer(settings.DATA_CENTER_TOKEN)

    def _headers_for(self, path: str) -> dict[str, str]:
        if path.startswith('/api/filter'):
            return {'X-Api-Key': self._api_key}
        return {'Authorization': self._login_auth}

    def list_notices(self) -> list[dict[str, Any]]:
        # data-center-backend 无 /sys_msg/*
        return []

    def get_notice(self, notice_id: str) -> dict[str, Any]:
        raise _Exception(404, 'data-center 不支持公告接口')
