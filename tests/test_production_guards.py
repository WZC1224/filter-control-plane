"""生产启动门禁。"""
import pytest

from config import settings


def test_production_rejects_weak_secrets(monkeypatch):
    monkeypatch.setattr(settings, 'FLASK_ENV', 'production')
    monkeypatch.setattr(settings, 'SECRET_KEY', 'change-me-filter-control-plane')
    monkeypatch.setattr(settings, 'JWT_SECRET', 'strong-enough-jwt-secret-value')
    monkeypatch.setattr(settings, 'ADMIN_PASSWORD', 'S0meStrongPass!')
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        settings.assert_production_safe()


def test_production_rejects_weak_admin_password(monkeypatch):
    monkeypatch.setattr(settings, 'FLASK_ENV', 'production')
    monkeypatch.setattr(settings, 'SECRET_KEY', 'strong-enough-secret-key-value')
    monkeypatch.setattr(settings, 'JWT_SECRET', 'strong-enough-jwt-secret-value')
    monkeypatch.setattr(settings, 'ADMIN_PASSWORD', 'admin123')
    with pytest.raises(RuntimeError, match='ADMIN_PASSWORD'):
        settings.assert_production_safe()


def test_development_allows_defaults(monkeypatch):
    monkeypatch.setattr(settings, 'FLASK_ENV', 'development')
    monkeypatch.setattr(settings, 'SECRET_KEY', 'dev-secret')
    monkeypatch.setattr(settings, 'JWT_SECRET', 'dev-jwt')
    monkeypatch.setattr(settings, 'ADMIN_PASSWORD', 'admin123')
    settings.assert_production_safe()
