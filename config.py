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
    DATA818_TOKEN = os.getenv('DATA818_TOKEN', '')
    DATA818_TIMEOUT = float(os.getenv('DATA818_TIMEOUT', '60'))

    APP_VERSION = os.getenv('APP_VERSION', '0.1.0')

    @property
    def use_mock_adapter(self) -> bool:
        return not (self.DATA818_BASE_URL and self.DATA818_TOKEN)

    @property
    def data818_token_kind(self) -> str:
        """none | agent | login — agent 常 exp 为 null，只能打 /api/filter/*。"""
        if self.use_mock_adapter:
            return 'none'
        payload = _jwt_payload_unverified(self.DATA818_TOKEN)
        if not payload:
            return 'unknown'
        exp = payload.get('exp')
        if exp is None or exp == '':
            return 'agent'
        return 'login'


settings = BaseConfig()
