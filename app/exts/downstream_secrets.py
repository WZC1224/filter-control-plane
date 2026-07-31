"""下游凭证覆盖：文件落盘 + 热应用到 settings（不改 .env）。"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import BASE_DIR, _jwt_payload_unverified, _token_kind, settings

SECRET_KEYS = (
    'DATA818_TOKEN',
    'DATA818_AGENT_TOKEN',
)

SECRETS_PATH = BASE_DIR / 'downstream_secrets.json'

_lock = threading.Lock()
_env_baseline: dict[str, str] = {k: getattr(settings, k) or '' for k in SECRET_KEYS}


def secrets_path() -> Path:
    return SECRETS_PATH


def set_env_baseline(values: dict[str, str]) -> None:
    """测试用：替换环境底。"""
    global _env_baseline
    _env_baseline = {k: values.get(k, '') for k in SECRET_KEYS}


def _read_file(path: Path | None = None) -> dict[str, str]:
    p = path or SECRETS_PATH
    if not p.is_file():
        return {}
    try:
        raw = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for k in SECRET_KEYS:
        v = raw.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out


def _write_file(data: dict[str, str], path: Path | None = None) -> None:
    p = path or SECRETS_PATH
    payload = {k: data[k] for k in SECRET_KEYS if k in data and data[k]}
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def recompute(path: Path | None = None) -> dict[str, str]:
    """生效值 = 环境底 ⊕ 文件覆盖。返回文件覆盖字典。"""
    with _lock:
        file_vals = _read_file(path)
        for k in SECRET_KEYS:
            setattr(settings, k, file_vals.get(k, _env_baseline.get(k, '')))
        return dict(file_vals)


def mask_secret(value: str) -> str:
    raw = (value or '').strip()
    if raw.lower().startswith('bearer '):
        raw = raw[7:].strip()
    if not raw:
        return ''
    if len(raw) <= 12:
        return raw[:2] + '…' + raw[-2:]
    return f'{raw[:6]}…{raw[-6:]}'


def _exp_iso(token: str) -> str | None:
    payload = _jwt_payload_unverified(token)
    exp = payload.get('exp')
    if exp is None or exp == '':
        return None
    try:
        ts = int(exp)
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except (TypeError, ValueError, OSError):
        return None


def describe_token(value: str, *, override: bool) -> dict[str, Any]:
    configured = bool((value or '').strip())
    return {
        'configured': configured,
        'masked': mask_secret(value) if configured else '',
        'kind': _token_kind(value) if configured else 'none',
        'exp': _exp_iso(value) if configured else None,
        'source': 'file' if override else 'env',
    }


def status(path: Path | None = None) -> dict[str, Any]:
    overrides = _read_file(path)
    return {
        'data818Token': describe_token(
            settings.DATA818_TOKEN, override='DATA818_TOKEN' in overrides
        ),
        'data818AgentToken': describe_token(
            settings.DATA818_AGENT_TOKEN, override='DATA818_AGENT_TOKEN' in overrides
        ),
        'filePath': str((path or SECRETS_PATH).name),
        'adapter': settings.adapter_name,
    }


def update(
    *,
    data818_token: str | None = None,
    data818_agent_token: str | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """
    更新覆盖文件并热生效。
    - None：不改该键
    - ''：删除该键覆盖（回退环境底）
    - 非空：写入覆盖（自动剥 Bearer 前缀）
    """
    with _lock:
        current = _read_file(path)
        mapping = {
            'DATA818_TOKEN': data818_token,
            'DATA818_AGENT_TOKEN': data818_agent_token,
        }
        touched = False
        for key, value in mapping.items():
            if value is None:
                continue
            touched = True
            stripped = value.strip()
            if not stripped:
                current.pop(key, None)
            else:
                if stripped.lower().startswith('bearer '):
                    stripped = stripped[7:].strip()
                current[key] = stripped
        if not touched:
            return status(path)
        _write_file(current, path)

    recompute(path)
    from app.adapters import get_adapter

    get_adapter.cache_clear()
    return status(path)
