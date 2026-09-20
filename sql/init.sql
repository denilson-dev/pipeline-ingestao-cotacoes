CREATE TABLE IF NOT EXISTS cotacoes_diarias (
    id BIGSERIAL PRIMARY KEY,
    moeda VARCHAR(3) NOT NULL,
    taxa_brl NUMERIC(18, 6) NOT NULL CHECK (taxa_brl > 0),
    data_referencia DATE NOT NULL,
    data_ingestao TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_cotacoes_diarias_moeda_data
        UNIQUE (moeda, data_referencia)
);

CREATE INDEX IF NOT EXISTS idx_cotacoes_diarias_moeda_data
    ON cotacoes_diarias (moeda, data_referencia DESC);
