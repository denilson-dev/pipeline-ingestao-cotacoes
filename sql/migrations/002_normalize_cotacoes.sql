BEGIN;

DO $$
BEGIN
    IF to_regclass('public.cotacoes_diarias') IS NOT NULL
       AND EXISTS (
           SELECT 1
           FROM information_schema.columns
           WHERE table_schema = 'public'
             AND table_name = 'cotacoes_diarias'
             AND column_name = 'valor_compra'
       )
    THEN
        IF to_regclass('public.cotacoes_diarias_legacy') IS NULL THEN
            ALTER TABLE cotacoes_diarias RENAME TO cotacoes_diarias_legacy;
        ELSE
            RAISE EXCEPTION
                'A tabela cotacoes_diarias_legacy já existe. Revise a migração antes de continuar.';
        END IF;
    END IF;
END
$$;

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

DO $$
BEGIN
    IF to_regclass('public.cotacoes_diarias_legacy') IS NOT NULL THEN
        EXECUTE $sql$
            INSERT INTO cotacoes_diarias
                (moeda, taxa_brl, data_referencia, data_ingestao)
            SELECT
                moeda,
                valor_compra AS taxa_brl,
                (data_cotacao AT TIME ZONE 'UTC')::date AS data_referencia,
                data_cotacao AS data_ingestao
            FROM (
                SELECT DISTINCT ON (
                    moeda,
                    (data_cotacao AT TIME ZONE 'UTC')::date
                )
                    id,
                    moeda,
                    valor_compra,
                    data_cotacao
                FROM cotacoes_diarias_legacy
                WHERE valor_compra > 0
                ORDER BY
                    moeda,
                    (data_cotacao AT TIME ZONE 'UTC')::date,
                    data_cotacao DESC,
                    id DESC
            ) AS legado
            ON CONFLICT (moeda, data_referencia) DO NOTHING
        $sql$;
    END IF;
END
$$;

COMMIT;

-- A tabela cotacoes_diarias_legacy é mantida propositalmente como cópia do
-- modelo anterior. Depois de validar a nova estrutura e os dados migrados,
-- ela pode ser removida manualmente em uma etapa separada, se desejado.
