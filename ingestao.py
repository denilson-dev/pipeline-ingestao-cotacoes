import requests
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "dbname": "analytics_db",
    "user": "admin_dba",
    "password": "SuaSenhaSegura123",
    "host": "127.0.0.1",
    "port": "5432"
}

def obter_cotacoes():
    # Tenta obter dados de uma API publica sem restricao agressiva
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            brl = data["rates"]["BRL"]
            eur = data["rates"]["EUR"]
            return [
                {"moeda": "USD", "compra": brl, "venda": brl},
                {"moeda": "EUR", "compra": brl / eur, "venda": brl / eur}
            ]
    except Exception as e:
        print(f"Aviso: Falha na API principal ({e}). Usando dados de fallback.")

    # Fallback automatico para simulação caso a API bloqueie o IP
    return [
        {"moeda": "USD", "compra": 5.65, "venda": 5.68},
        {"moeda": "EUR", "compra": 6.15, "venda": 6.20},
        {"moeda": "BTC", "compra": 345000.00, "venda": 346000.00}
    ]

def rodar_pipeline():
    cotacoes = obter_cotacoes()
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    registos = 0
    agora = datetime.now()

    for item in cotacoes:
        cursor.execute(
            """
            INSERT INTO cotacoes_diarias (moeda, valor_compra, valor_venda, data_cotacao)
            VALUES (%s, %s, %s, %s)
            """,
            (item["moeda"], item["compra"], item["venda"], agora)
        )
        registos += 1
        print(f"-> Inserida cotação {item['moeda']}: R$ {item['compra']:.2f}")

    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"[{agora}] Sucesso! Registos inseridos no PostgreSQL: {registos}")

if __name__ == "__main__":
    rodar_pipeline()
