import logging
import os
import sys
import time
from datetime import date, datetime, timezone

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


def _obter_data_referencia(payload):
    data_api = payload.get("date")
    if data_api:
        try:
            return date.fromisoformat(data_api)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Data inválida retornada pela API: {data_api!r}") from exc

    timestamp_api = payload.get("time_last_updated")
    if isinstance(timestamp_api, (int, float)) and timestamp_api > 0:
        return datetime.fromtimestamp(timestamp_api, tz=timezone.utc).date()

    raise ValueError("A API não retornou uma data de referência válida.")


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
            data_referencia = _obter_data_referencia(payload)

            return [
                {
                    "moeda": "USD",
                    "taxa_brl": brl_por_usd,
                    "data_referencia": data_referencia,
                },
                {
                    "moeda": "EUR",
                    "taxa_brl": brl_por_eur,
                    "data_referencia": data_referencia,
                },
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
    data_ingestao = datetime.now(timezone.utc)
    inseridos = 0
    atualizados = 0

    with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            for item in cotacoes:
                cursor.execute(
                    """
                    INSERT INTO cotacoes_diarias
                        (moeda, taxa_brl, data_referencia, data_ingestao)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (moeda, data_referencia)
                    DO UPDATE SET
                        taxa_brl = EXCLUDED.taxa_brl,
                        data_ingestao = EXCLUDED.data_ingestao
                    RETURNING (xmax = 0) AS inserido
                    """,
                    (
                        item["moeda"],
                        item["taxa_brl"],
                        item["data_referencia"],
                        data_ingestao,
                    ),
                )

                inserido = cursor.fetchone()[0]
                if inserido:
                    inseridos += 1
                    acao = "inserida"
                else:
                    atualizados += 1
                    acao = "atualizada"

                logger.info(
                    "Cotação %s %s: R$ %.4f | referência=%s",
                    item["moeda"],
                    acao,
                    item["taxa_brl"],
                    item["data_referencia"],
                )

    return inseridos, atualizados


def rodar_pipeline():
    logger.info("Iniciando pipeline de ingestão.")
    cotacoes = obter_cotacoes()
    inseridos, atualizados = persistir_cotacoes(cotacoes)
    logger.info(
        "Pipeline concluído com sucesso. Inseridos=%s | Atualizados=%s",
        inseridos,
        atualizados,
    )


if __name__ == "__main__":
    try:
        rodar_pipeline()
    except Exception:
        logger.exception("Pipeline finalizado com erro.")
        sys.exit(1)
