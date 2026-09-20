import importlib

import pytest
import requests


@pytest.fixture
def modulo(monkeypatch):
    monkeypatch.setenv("API_MAX_ATTEMPTS", "1")
    import ingestao

    return importlib.reload(ingestao)


def test_obter_cotacoes_calcula_usd_e_eur(monkeypatch, modulo):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"rates": {"BRL": 5.2, "EUR": 0.8}}

    monkeypatch.setattr(modulo.requests, "get", lambda *args, **kwargs: FakeResponse())

    cotacoes = modulo.obter_cotacoes()

    assert cotacoes[0] == {"moeda": "USD", "compra": 5.2, "venda": 5.2}
    assert cotacoes[1]["moeda"] == "EUR"
    assert cotacoes[1]["compra"] == pytest.approx(6.5)
    assert cotacoes[1]["venda"] == pytest.approx(6.5)


def test_obter_cotacoes_nao_inventa_fallback(monkeypatch, modulo):
    def falhar(*args, **kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(modulo.requests, "get", falhar)

    with pytest.raises(RuntimeError, match="Nenhum dado será gravado"):
        modulo.obter_cotacoes()


def test_configuracao_banco_exige_segredos(monkeypatch, modulo):
    for nome in [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
    ]:
        monkeypatch.delenv(nome, raising=False)

    with pytest.raises(RuntimeError, match="POSTGRES_DB"):
        modulo.obter_configuracao_banco()


def test_configuracao_banco_vem_do_ambiente(monkeypatch, modulo):
    monkeypatch.setenv("POSTGRES_DB", "analytics_db")
    monkeypatch.setenv("POSTGRES_USER", "admin_dba")
    monkeypatch.setenv("POSTGRES_PASSWORD", "segredo")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "55432")

    config = modulo.obter_configuracao_banco()

    assert config["dbname"] == "analytics_db"
    assert config["user"] == "admin_dba"
    assert config["password"] == "segredo"
    assert config["host"] == "localhost"
    assert config["port"] == "55432"
