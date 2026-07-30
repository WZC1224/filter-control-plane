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

    DATA818_BASE_URL = os.getenv('DATA818_BASE_URL', '').rstrip('/')
    # 登录 JWT（JWT_SECRET_EXPIRE）：任务列表/订单/价目/公告/账单
    DATA818_TOKEN = os.getenv('DATA818_TOKEN', '')
    # agent JWT（JWT_SECRET_NO_EXPIRE）：/api/filter/* 建任务/类型/国家/余额/下载
    DATA818_AGENT_TOKEN = os.getenv('DATA818_AGENT_TOKEN', '')
    DATA818_TIMEOUT = float(os.getenv('DATA818_TIMEOUT', '60'))

    APP_VERSION = os.getenv('APP_VERSION', '0.1.0')

    @property
    def use_mock_adapter(self) -> bool:
        return not (self.DATA818_BASE_URL and self.DATA818_TOKEN)

    @property
    def data818_token_kind(self) -> str:
        """主 Token（DATA818_TOKEN）种类：none | agent | login | unknown。"""
        if self.use_mock_adapter:
            return 'none'
        return _token_kind(self.DATA818_TOKEN)

    @property
    def data818_has_agent_token(self) -> bool:
        return bool(self.DATA818_AGENT_TOKEN.strip())


settings = BaseConfig()
