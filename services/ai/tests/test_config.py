import pytest


def test_config_loads_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    import importlib
    import lawdigest_ai.config as config
    importlib.reload(config)
    assert config.get_openai_api_key() == "test-key"


def test_config_raises_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("APIKEY_OPENAI", raising=False)
    import importlib
    import lawdigest_ai.config as config
    importlib.reload(config)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        config.get_openai_api_key()


def test_config_loads_gemini_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    import importlib
    import lawdigest_ai.config as config
    importlib.reload(config)
    assert config.get_gemini_api_key() == "gemini-key"


def test_config_exposes_gemini_models(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-model")
    monkeypatch.setenv("GEMINI_BATCH_MODEL", "gemini-batch-model")
    monkeypatch.setenv("GEMINI_INSTANT_MODEL", "gemini-instant-model")
    import importlib
    import lawdigest_ai.config as config
    importlib.reload(config)
    assert config.GEMINI_MODEL == "gemini-model"
    assert config.GEMINI_BATCH_MODEL == "gemini-batch-model"
    assert config.GEMINI_INSTANT_MODEL == "gemini-instant-model"


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


def test_db_config_test(monkeypatch):
    monkeypatch.setenv("TEST_DB_HOST", "test-host")
    monkeypatch.setenv("TEST_DB_PORT", "3307")
    monkeypatch.setenv("TEST_DB_USER", "test-user")
    monkeypatch.setenv("TEST_DB_PASSWORD", "test-pass")
    monkeypatch.setenv("TEST_DB_NAME", "test-lawdb")
    from lawdigest_ai.db import get_test_db_config
    cfg = get_test_db_config()
    assert cfg["host"] == "test-host"
    assert cfg["port"] == 3307


def test_db_config_missing_raises(monkeypatch):
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    import importlib
    import lawdigest_ai.db as db_module
    importlib.reload(db_module)
    with pytest.raises(ValueError, match="DB 환경변수 누락"):
        db_module.get_prod_db_config()
