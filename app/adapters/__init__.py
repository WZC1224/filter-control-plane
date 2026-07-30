from functools import lru_cache

from app.adapters.base import DownstreamAdapter
from app.adapters.mock import MockAdapter
from config import settings


@lru_cache(maxsize=1)
def get_adapter() -> DownstreamAdapter:
    name = settings.adapter_name
    if name == 'mock':
        return MockAdapter()
    if name == 'data_center':
        from app.adapters.data_center import DataCenterAdapter

        return DataCenterAdapter()
    from app.adapters.data818 import Data818Adapter

    return Data818Adapter()
