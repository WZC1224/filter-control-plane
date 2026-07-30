from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, BinaryIO, Literal

DownloadFormat = Literal['csv', 'txt', 'xlsx', 'invalid']


@dataclass(frozen=True)
class FilePayload:
    """下游下载的统一文件载荷（不含 Flask 依赖）。"""

    content: bytes
    content_type: str
    filename: str


class DownstreamAdapter(ABC):
    """筛选下游适配器契约。"""

    @abstractmethod
    def list_tasks(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        task_type: str | None = None,
        task_no: str | None = None,
        country_code: str | None = None,
        task_status: int | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def create_task(
        self,
        *,
        filter_type: str,
        country_code: str,
        describe: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def query_task(self, task_no: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_download(self, task_no: str, *, fmt: DownloadFormat = 'csv') -> FilePayload:
        ...

    @abstractmethod
    def list_filter_types(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def list_countries(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_balance(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def close_task(self, task_no: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def refund_task(self, task_no: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def retry_task(self, task_no: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def statistics(self, *, task_type: str | None = None) -> dict[str, Any]:
        ...

    @abstractmethod
    def list_orders(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        order_id: str | None = None,
        task_type: str | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def third_balances(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def list_bills(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        bill_id: str | None = None,
        order_id: str | None = None,
        ledger_type: str | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def list_notices(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_notice(self, notice_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def list_products(self) -> list[dict[str, Any]]:
        """扁平价目：[{taskType, name, price, ...}]"""
        ...

    @abstractmethod
    def list_order_task_types(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def list_ledger_types(self) -> list[dict[str, Any]]:
        """账本类型枚举：[{ledgerType, description}]"""
        ...

    @abstractmethod
    def export_remaining(self, task_no: str) -> FilePayload | dict[str, Any]:
        """文件流；或 {objectPath, downloadable:false}（下游仅 OSS path）。"""
        ...
