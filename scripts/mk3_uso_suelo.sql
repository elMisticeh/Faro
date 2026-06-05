-- ============================================================================
-- MK3 - Uso de suelo (zonificacion IMPLAN) persistido por listing
-- Correr UNA VEZ en Supabase: Dashboard -> SQL Editor -> pega y RUN.
-- Es aditivo (IF NOT EXISTS): no altera datos existentes.
-- ============================================================================

ALTER TABLE listings ADD COLUMN IF NOT EXISTS uso_suelo      text;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS uso_suelo_cat  text;

COMMENT ON COLUMN listings.uso_suelo     IS 'SIMBOLOGIA IMPLAN del punto del listing (point-in-polygon)';
COMMENT ON COLUMN listings.uso_suelo_cat IS 'Categoria de uso: Habitacional / Mixto / Corredor urbano / Industrial / Servicios / Equipamiento / Agricola / Conservacion';

CREATE INDEX IF NOT EXISTS idx_listings_uso_suelo_cat ON listings (uso_suelo_cat);

-- Despues de correr esto, ejecuta:  py scripts/poblar_uso_suelo.py
