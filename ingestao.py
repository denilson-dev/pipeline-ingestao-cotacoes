import logging
import os
import sys
import time
from datetime import datetime, timezone

import psycopg2
import requests

API_URL = os.getenv("EXCHANGE_API_URL", "https://api.exchangerate-api.com/v4/latest/USD")
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "5"))
API_MAX_ATTEMPTS = int(os.getenv("API_MAX_ATTEMPTS", "3"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def obter_configuracao_banco():
    required = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST"]
    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            "Variáveis de ambiente obrigatórias ausentes: " + ", ".join(missing)
        )

    return {
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "host": os.environ["POSTGRES_HOST"],
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "connect_timeout": 5,
        "application_name": "pipeline-ingestao-cotacoes",
    }


def _validar_taxa(valor, nome):
    if not isinstance(valor, (int, float)) or valor <= 0:
        raise ValueError(f"Taxa inválida para {nome}: {valor!r}")
    return float(valor)


def obter_cotacoes():
    ultimo_erro = None

    for tentativa in range(1, API_MAX_ATTEMPTS + 1):
        try:
            resposta = requests.get(API_URL, timeout=API_TIMEOUT_SECONDS)
            resposta.raise_for_status()
            payload = resposta.json()

            rates = payload.get("rates", {})
            brl_por_usd = _validar_taxa(rates.get("BRL"), "BRL")
            eur_por_usd = _validar_taxa(rates.get("EUR"), "EUR")
            brl_por_eur = brl_por_usd / eur_por_usd

            return [
                {"moeda": "USD", "compra": brl_por_usd, "venda": brl_por_usd},
                {"moeda": "EUR", "compra": brl_por_eur, "venda": brl_por_eur},
            ]
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            ultimo_erro = exc
            logger.warning(
                "Falha ao obter cotações (tentativa %s/%s): %s",
                tentativa,
                API_MAX_ATTEMPTS,
                exc,
            )
            if tentativa < API_MAX_ATTEMPTS:
                time.sleep(min(tentativa * 2, 5))

    raise RuntimeError(
        "Não foi possível obter cotações válidas da API. "
        "Nenhum dado será gravado no banco."
    ) from ultimo_erro


def persistir_cotacoes(cotacoes):
    db_config = obter_configuracao_banco()
    agora = datetime.now(timezone.utc)
    inseridos = 0
    ignorados = 0

    with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            for item in cotacoes:
                cursor.execute(
                    """
                    INSERT INTO cotacoes_diarias
                        (moeda, valor_compra, valor_venda, data_cotacao)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        item["moeda"],
                        item["compra"],
                        item["venda"],
                        agora,
                    ),
                )

                if cursor.rowcount == 1:
                    inseridos += 1
                    logger.info(
                        "Cotação %s inserida: R$ %.4f",
                        item["moeda"],
                        item["compra"],
                    )
                else:
                    ignorados += 1
                    logger.info(
                        "Cotação %s já existente para a data UTC atual; inserção ignorada.",
                        item["moeda"],
                    )

    return inseridos, ignorados


def rodar_pipeline():
    logger.info("Iniciando pipeline de ingestão.")
    cotacoes = obter_cotacoes()
    inseridos, ignorados = persistir_cotacoes(cotacoes)
    logger.info(
        "Pipeline concluído com sucesso. Inseridos=%s | Ignorados=%s",
        inseridos,
        ignorados,
    )


if __name__ == "__main__":
    try:
        rodar_pipeline()
    except Exception:
        logger.exception("Pipeline finalizado com erro.")
        sys.exit(1)
