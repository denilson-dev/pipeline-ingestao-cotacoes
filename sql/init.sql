CREATE TABLE IF NOT EXISTS cotacoes_diarias (
    id BIGSERIAL PRIMARY KEY,
    moeda VARCHAR(10) NOT NULL,
    valor_compra NUMERIC(18, 6) NOT NULL CHECK (valor_compra > 0),
    valor_venda NUMERIC(18, 6) NOT NULL CHECK (valor_venda > 0),
    data_cotacao TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cotacoes_diarias_moeda_data
    ON cotacoes_diarias (moeda, data_cotacao DESC);
