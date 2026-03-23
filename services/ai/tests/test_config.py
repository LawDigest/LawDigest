import pytest
import os

def test_config_loads_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from lawdigest_ai.config import get_openai_api_key
    assert get_openai_api_key() == "test-key"

def test_config_raises_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("APIKEY_OPENAI", raising=False)
    from lawdigest_ai import config
    import importlib
    importlib.reload(config)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        config.get_openai_api_key()

def test_db_config_prod(monkeypatch):
    monkeypatch.setenv("DB_HOST", "prod-host")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_NAME", "lawdb")
    from lawdigest_ai.db import get_prod_db_config
    cfg = get_prod_db_config()
    assert cfg["host"] == "prod-host"
    assert cfg["port"] == 3306
