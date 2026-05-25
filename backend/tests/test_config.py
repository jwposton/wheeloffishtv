
import pytest
from pydantic import ValidationError

from wheeloffish.core.config import Settings, get_settings


def test_missing_secret_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WOF_SECRET_KEY", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings()


def test_valid_hex_key_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    monkeypatch.setenv("WOF_SECRET_KEY", key)
    get_settings.cache_clear()
    settings = Settings()
    assert settings.WOF_SECRET_KEY == key
    assert settings.DATABASE_URL == "sqlite:////data/wheeloffish.db"
