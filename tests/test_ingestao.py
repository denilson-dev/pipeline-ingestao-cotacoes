import importlib
from datetime import date

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
            return {
                "date": "2026-09-20",
                "rates": {"BRL": 5.2, "EUR": 0.8},
            }

    monkeypatch.setattr(modulo.requests, "get", lambda *args, **kwargs: FakeResponse())

    cotacoes = modulo.obter_cotacoes()

    assert cotacoes[0] == {
        "moeda": "USD",
        "taxa_brl": 5.2,
        "data_referencia": date(2026, 9, 20),
    }
    assert cotacoes[1]["moeda"] == "EUR"
    assert cotacoes[1]["taxa_brl"] == pytest.approx(6.5)
    assert cotacoes[1]["data_referencia"] == date(2026, 9, 20)


def test_data_referencia_pode_vir_do_timestamp(modulo):
    payload = {"time_last_updated": 1789862400}

    data_referencia = modulo._obter_data_referencia(payload)

    assert isinstance(data_referencia, date)


def test_data_referencia_invalida_gera_erro(modulo):
    with pytest.raises(ValueError, match="data de referência"):
        modulo._obter_data_referencia({})


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
