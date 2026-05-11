# 🏠 Torreón Real Estate Scraper

Base de datos de listings inmobiliarios de Torreón — scraping automático de Inmuebles24 con enriquecimiento por IA (Claude) y almacenamiento en Supabase.

---

## 📁 Archivos del proyecto

```
C:\proyectos\real-estate\
├── .env              ← Credenciales (NO subir a git)
├── scraper.py        ← Scraper principal
├── scheduler.py      ← Corridas automáticas
├── test_conexion.py  ← Verifica que todo esté OK
└── dashboard.html    ← Frontend — ábrelo en el navegador
```

---

## 🚀 Cómo correr

### 1. Verificar que todo funciona
```powershell
cd C:\proyectos\real-estate
py test_conexion.py
```
Deberías ver: `✓ Supabase OK`, `✓ Claude API OK`, `✓ Playwright OK`

### 2. Correr el scraper una vez
```powershell
cd C:\proyectos\real-estate
py scraper.py
```
- Tarda ~20–60 min dependiendo de cuántos listings haya
- Scrapea 10 tipos de inmuebles (casas, deptos, terrenos, locales, bodegas — venta y renta)
- Guarda automáticamente en Supabase
- Si ya existe un listing, actualiza el precio y guarda historial si cambió

### 3. Ver el dashboard
Abre `dashboard.html` directamente en tu navegador (doble clic o arrastrar a Chrome/Edge).

La primera vez pedirá tus credenciales de Supabase:
- **URL**: la que empieza con `https://xxxx.supabase.co`
- **Anon Key**: la que empieza con `eyJhbGci...`

Ambas están en tu archivo `.env`.

### 4. Programar corridas automáticas
```powershell
cd C:\proyectos\real-estate
py scheduler.py
```
Corre el scraper cada 12 horas mientras la ventana esté abierta.

---

## 🗃️ Qué datos se guardan

| Campo | Descripción | Fuente |
|-------|-------------|--------|
| `precio_mxn` | Precio de lista en pesos MXN | Scraper |
| `precio_x_m2` | Precio ÷ m² (calculado automático) | Calculado |
| `colonia` | Nombre de la colonia | Scraper |
| `tipo_operacion` | venta / renta / preventa | IA |
| `tipo_inmueble` | casa / departamento / terreno / etc. | IA |
| `recamaras` | Número de recámaras | Scraper + IA |
| `banos` | Número de baños | Scraper + IA |
| `m2_terreno` | Metros cuadrados de lote | Scraper |
| `m2_construccion` | Metros cuadrados construidos | Scraper |
| `nivel_premium` | economico / medio / residencial / premium | IA |
| `estado_inmueble` | nuevo / usado / remodelado / etc. | IA |
| `amenidades` | Lista de amenidades detectadas | IA |
| `score_calidad_anuncio` | 0–100, qué tan completo es el anuncio | IA |
| `fecha_primer_scrape` | Cuándo se capturó por primera vez | Scraper |
| `fecha_ultimo_scrape` | Última vez que se vio activo | Scraper |

---

## 🔧 Configurar el scraper

Edita `scraper.py` y cambia estas constantes al inicio:

```python
MAX_PAGINAS = 10    # Subir para más cobertura (cada página ~28 listings)
```

Para agregar más zonas de Torreón además del municipio general, agrega URLs al arreglo `PORTALES`:

```python
{"nombre": "i24_campestre_venta", "url_base": "https://www.inmuebles24.com/casas-en-venta-en-campestre-la-rosita.html", "tipo_operacion_default": "venta"},
```

---

## ❗ Solución de problemas

**"Error: módulo no encontrado"**
```powershell
pip install playwright anthropic python-dotenv supabase --break-system-packages
playwright install chromium
```

**"0 listings encontrados"**
- Inmuebles24 puede bloquear temporalmente. Espera 10 min y vuelve a correr.
- Verifica que tengas internet.

**"Error Supabase 401"**
- Revisa que SUPABASE_KEY en `.env` sea la `anon key`, no la `service_role key`.

**El dashboard no carga**
- Verifica que el URL de Supabase NO tenga `/` al final.
- Abre la consola del navegador (F12) para ver el error exacto.

---

## 💰 Costo estimado por corrida

| Servicio | Costo |
|----------|-------|
| Claude Haiku (IA por listing) | ~$0.001 por listing |
| Corrida completa (~500 listings) | ~$0.50 USD |
| Supabase (hasta 50,000 filas) | Gratis |
| Total mensual (2 corridas/día) | ~$30 USD |

---

## 📊 Ver los datos en Supabase directamente

1. Ve a [supabase.com](https://supabase.com) → tu proyecto
2. Sección **Table Editor** → tabla `listings`
3. Para SQL: sección **SQL Editor**

Consultas útiles:
```sql
-- Precio promedio por colonia (venta)
SELECT colonia, COUNT(*) as total, AVG(precio_mxn) as precio_avg, AVG(precio_x_m2) as pm2_avg
FROM listings
WHERE tipo_operacion = 'venta' AND activo = true
GROUP BY colonia
ORDER BY total DESC;

-- Listings más baratos por m²
SELECT colonia, tipo_inmueble, precio_mxn, precio_x_m2, m2_construccion
FROM listings
WHERE precio_x_m2 IS NOT NULL AND tipo_operacion = 'venta'
ORDER BY precio_x_m2 ASC
LIMIT 20;

-- Cuántos listings por tipo
SELECT tipo_inmueble, tipo_operacion, COUNT(*) as total
FROM listings WHERE activo = true
GROUP BY tipo_inmueble, tipo_operacion
ORDER BY total DESC;
```
