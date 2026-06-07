-- ============================================================================
-- MK5 - Uso de suelo clave IMPLAN exacta + proteccion de ubicacion manual
-- Correr UNA VEZ en Supabase: Dashboard -> SQL Editor -> pega y RUN.
-- Es aditivo (IF NOT EXISTS): no altera datos existentes.
-- ============================================================================

ALTER TABLE listings ADD COLUMN IF NOT EXISTS uso_suelo_clave  text;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS ubicacion_manual boolean DEFAULT false;

COMMENT ON COLUMN listings.uso_suelo_clave  IS 'Codigo IMPLAN exacto del punto: H1, H2, H3, M1, CU1.1, ES, etc.';
COMMENT ON COLUMN listings.ubicacion_manual IS 'Ubicacion fijada manualmente en el mapa: el scraper no mueve lat/lng ni uso de suelo (pero si actualiza precio/descripcion)';

CREATE INDEX IF NOT EXISTS idx_listings_uso_suelo_clave ON listings (uso_suelo_clave);

-- Despues de correr esto:  py scripts/poblar_uso_suelo.py   (pobla uso_suelo_clave)
