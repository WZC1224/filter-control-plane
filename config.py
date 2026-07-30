import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def _jwt_payload_unverified(token: str) -> dict:
    """只读 JWT payload，不验签（仅用于运维提示）。"""
    import base64
    import json

    raw = token.strip()
    if raw.lower().startswith('bearer '):
        raw = raw[7:].strip()
    parts = raw.split('.')
    if len(parts) < 2:
        return {}
    pad = parts[1] + '=' * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(pad.encode('ascii')))
    except Exception:
        return {}


def _token_kind(token: str) -> str:
    payload = _jwt_payload_unverified(token)
    if not payload:
        return 'unknown'
    exp = payload.get('exp')
    if exp is None or exp == '':
        return 'agent'
    return 'login'


class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', f"sqlite:///{BASE_DIR / 'fcp.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-jwt')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '1440'))

    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # 独占下游：mock | data818 | data_center | auto（空=auto）
    DOWNSTREAM = (os.getenv('DOWNSTREAM', '') or 'auto').strip().lower()

    DATA818_BASE_URL = os.getenv('DATA818_BASE_URL', '').rstrip('/')
    # 登录 JWT（JWT_SECRET_EXPIRE）：任务列表/订单/价目/公告/账单
    DATA818_TOKEN = os.getenv('DATA818_TOKEN', '')
    # agent JWT（JWT_SECRET_NO_EXPIRE）：/api/filter/* 建任务/类型/国家/余额/下载
    DATA818_AGENT_TOKEN = os.getenv('DATA818_AGENT_TOKEN', '')
    DATA818_TIMEOUT = float(os.getenv('DATA818_TIMEOUT', '60'))

    DATA_CENTER_BASE_URL = os.getenv('DATA_CENTER_BASE_URL', '').rstrip('/')
    DATA_CENTER_API_KEY = os.getenv('DATA_CENTER_API_KEY', '')
    DATA_CENTER_TOKEN = os.getenv('DATA_CENTER_TOKEN', '')
    DATA_CENTER_TIMEOUT = float(os.getenv('DATA_CENTER_TIMEOUT', '60'))

    APP_VERSION = os.getenv('APP_VERSION', '0.1.0')

    @property
    def data818_configured(self) -> bool:
        return bool(self.DATA818_BASE_URL and self.DATA818_TOKEN)

    @property
    def data_center_configured(self) -> bool:
        return bool(
            self.DATA_CENTER_BASE_URL
            and self.DATA_CENTER_API_KEY.strip()
            and self.DATA_CENTER_TOKEN.strip()
        )

    @property
    def adapter_name(self) -> str:
        """独占下游名：mock | data818 | data_center。"""
        choice = self.DOWNSTREAM
        if choice in ('', 'auto'):
            if self.data_center_configured:
                return 'data_center'
            if self.data818_configured:
                return 'data818'
            return 'mock'
        if choice == 'mock':
            return 'mock'
        if choice == 'data818':
            if not self.data818_configured:
                raise RuntimeError(
                    'DOWNSTREAM=data818 但缺少 DATA818_BASE_URL / DATA818_TOKEN'
                )
            return 'data818'
        if choice in ('data_center', 'datacenter', 'data-center'):
            if not self.data_center_configured:
                raise RuntimeError(
                    'DOWNSTREAM=data_center 但缺少 DATA_CENTER_BASE_URL / '
                    'DATA_CENTER_API_KEY / DATA_CENTER_TOKEN'
                )
            return 'data_center'
        raise RuntimeError(
            f'未知 DOWNSTREAM={choice!r}；允许 mock|data818|data_center|auto'
        )

    @property
    def use_mock_adapter(self) -> bool:
        return self.adapter_name == 'mock'

    @property
    def data818_token_kind(self) -> str:
        """主业务 Token 种类：none | agent | login | unknown。"""
        name = self.adapter_name
        if name == 'mock':
            return 'none'
        if name == 'data_center':
            return _token_kind(self.DATA_CENTER_TOKEN)
        return _token_kind(self.DATA818_TOKEN)

    @property
    def data818_has_agent_token(self) -> bool:
        """data818 agent JWT；data_center 无 agent 概念，恒 False。"""
        if self.adapter_name != 'data818':
            return False
        return bool(self.DATA818_AGENT_TOKEN.strip())

    @property
    def data_center_has_api_key(self) -> bool:
        return self.adapter_name == 'data_center' and bool(self.DATA_CENTER_API_KEY.strip())


settings = BaseConfig()
