import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


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


settings = BaseConfig()
