from __future__ import annotations

from app.adapters.filter_http import FilterHttpAdapter, flatten_product_tree
from config import settings

__all__ = ['Data818Adapter', 'flatten_product_tree']


class Data818Adapter(FilterHttpAdapter):
    """通过 HTTP 对接 data818 开放筛选 / 业务任务接口。"""

    adapter_label = 'data818'

    def __init__(self) -> None:
        if not settings.DATA818_BASE_URL or not settings.DATA818_TOKEN:
            raise RuntimeError('DATA818_BASE_URL / DATA818_TOKEN required')
        super().__init__(base_url=settings.DATA818_BASE_URL, timeout=settings.DATA818_TIMEOUT)
        self._login_auth = self._bearer(settings.DATA818_TOKEN)
        agent = (settings.DATA818_AGENT_TOKEN or '').strip()
        self._agent_auth = self._bearer(agent) if agent else self._login_auth

    def _headers_for(self, path: str) -> dict[str, str]:
        """818 两套密钥：/api/filter/* 用 agent；其余用登录 JWT。"""
        auth = self._agent_auth if path.startswith('/api/filter') else self._login_auth
        return {'Authorization': auth}
