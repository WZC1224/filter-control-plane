import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

_WEAK_SECRETS = frozenset({
    '',
    'dev-secret',
    'dev-jwt',
    'change-me-filter-control-plane',
    'change-me-jwt-secret',
})


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
    FLASK_ENV = (os.getenv('FLASK_ENV') or 'development').strip().lower()
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5100'))

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

    # 逗号分隔；空 = 开发放行 / 生产同机托管不需跨域
    CORS_ORIGINS = (os.getenv('CORS_ORIGINS') or '').strip()

    # 登录限流：同 IP 窗口内最大尝试次数；0 = 关闭（测试常用）
    LOGIN_RATE_LIMIT_MAX = int(os.getenv('LOGIN_RATE_LIMIT_MAX', '20'))
    LOGIN_RATE_WINDOW_SECONDS = float(os.getenv('LOGIN_RATE_WINDOW_SECONDS', '300'))
    # 仅反向代理已剥伪造头时再开；否则勿信 X-Forwarded-For
    TRUST_PROXY_HEADERS = (os.getenv('TRUST_PROXY_HEADERS') or '').strip().lower() in (
        '1',
        'true',
        'yes',
        'on',
    )

    # 独占下游：mock | data818 | auto（空=auto）
    DOWNSTREAM = (os.getenv('DOWNSTREAM', '') or 'auto').strip().lower()

    DATA818_BASE_URL = os.getenv('DATA818_BASE_URL', '').rstrip('/')
    # 登录 JWT（JWT_SECRET_EXPIRE）：任务列表/订单/价目/公告/账单
    DATA818_TOKEN = os.getenv('DATA818_TOKEN', '')
    # agent JWT（JWT_SECRET_NO_EXPIRE）：/api/filter/* 建任务/类型/国家/余额/下载
    DATA818_AGENT_TOKEN = os.getenv('DATA818_AGENT_TOKEN', '')
    DATA818_TIMEOUT = float(os.getenv('DATA818_TIMEOUT', '60'))
    # getDownloadPathById 返回 OSS object path 时拼接公开下载基址
    DATA818_OSS_PUBLIC_BASE = (
        os.getenv('DATA818_OSS_PUBLIC_BASE') or 'https://168filter.oss-cn-hongkong.aliyuncs.com'
    ).rstrip('/')

    APP_VERSION = os.getenv('APP_VERSION', '0.1.0')

    @property
    def is_production(self) -> bool:
        return self.FLASK_ENV in ('production', 'prod')

    def assert_production_safe(self) -> None:
        """生产启动门禁：弱密钥直接拒绝。"""
        if not self.is_production:
            return
        if self.SECRET_KEY in _WEAK_SECRETS or self.JWT_SECRET in _WEAK_SECRETS:
            raise RuntimeError(
                '生产环境禁止使用默认 SECRET_KEY / JWT_SECRET；请在 .env 设置强随机值'
            )
        if self.ADMIN_PASSWORD in ('admin123', 'admin', 'password', '123456'):
            raise RuntimeError(
                '生产环境禁止弱 ADMIN_PASSWORD；请改成强密码后再启动'
            )

    @property
    def data818_configured(self) -> bool:
        return bool(self.DATA818_BASE_URL and self.DATA818_TOKEN)

    @property
    def adapter_name(self) -> str:
        """独占下游名：mock | data818。"""
        choice = self.DOWNSTREAM
        if choice in ('', 'auto'):
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
        raise RuntimeError(
            f'未知 DOWNSTREAM={choice!r}；允许 mock|data818|auto'
        )

    @property
    def use_mock_adapter(self) -> bool:
        return self.adapter_name == 'mock'

    @property
    def data818_token_kind(self) -> str:
        """主业务 Token 种类：none | agent | login | unknown。"""
        if self.adapter_name == 'mock':
            return 'none'
        return _token_kind(self.DATA818_TOKEN)

    @property
    def data818_has_agent_token(self) -> bool:
        if self.adapter_name != 'data818':
            return False
        return bool(self.DATA818_AGENT_TOKEN.strip())


settings = BaseConfig()
