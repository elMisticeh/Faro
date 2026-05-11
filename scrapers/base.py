"""
base.py — Clase base para todos los scrapers v2
================================================
Mejoras vs v1:
- Filtro geográfico: descarta listings fuera de Torreón/La Laguna
- Extracción de colonia por IA cuando scraper devuelve genérico
- Extracción de m² por IA desde descripción cuando faltan en HTML
- Validación estricta antes de guardar
"""
import re
import json
from datetime import datetime
from anthropic import Anthropic
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
claude   = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─── Bounding box de Torreón / La Laguna ─────────────────────────────────────
# Cubre Torreón, Gómez Palacio, Lerdo y alrededores
TORREON_BBOX = {
    "lat_min": 25.40,
    "lat_max": 25.75,
    "lng_min": -103.65,
    "lng_max": -103.15,
}

# Palabras que indican colonia genérica (no útil)
COLONIAS_GENERICAS = {
    "torreón", "torreon", "coahuila", "torreón coahuila",
    "torreón, coahuila", "torreon coahuila", "la laguna",
    "gómez palacio", "gomez palacio", "lerdo", "",
}

# ─── Validación geográfica ────────────────────────────────────────────────────

def es_de_torreon(lat: float | None, lng: float | None) -> bool:
    """True si las coordenadas están dentro del área de Torreón/La Laguna."""
    if lat is None or lng is None:
        return True  # Sin coords no podemos descartar — dejar pasar
    try:
        lat, lng = float(lat), float(lng)
        return (TORREON_BBOX["lat_min"] <= lat <= TORREON_BBOX["lat_max"] and
                TORREON_BBOX["lng_min"] <= lng <= TORREON_BBOX["lng_max"])
    except:
        return True

def colonia_es_generica(colonia: str) -> bool:
    return (colonia or "").strip().lower() in COLONIAS_GENERICAS

# ─── Parseo básico ────────────────────────────────────────────────────────────

def limpiar_precio(texto: str) -> float | None:
    if not texto:
        return None
    texto = re.sub(r"[A-Za-z$\s,]", "", texto.replace("MN","").replace("MXN",""))
    try:
        v = float(texto)
        return v if 10_000 <= v <= 500_000_000 else None
    except:
        return None

def limpiar_m2(texto: str) -> float | None:
    if not texto:
        return None
    m = re.search(r"([\d,]+\.?\d*)", texto.replace(",",""))
    try:
        v = float(m.group(1)) if m else None
        return v if v and 1 <= v <= 100_000 else None
    except:
        return None

def calcular_precio_x_m2(precio, m2):
    """Stub — Supabase calcula precio_x_m2 automáticamente como columna generada."""
    return None

def parsear_features(textos: list) -> dict:
    r = {}
    for t in textos:
        t = t.strip()
        if re.search(r"m²\s*lote|m2\s*lote", t, re.I):
            m = re.search(r"([\d,]+\.?\d*)", t)
            if m: r["m2_terreno"] = float(m.group(1).replace(",",""))
        elif re.search(r"m²\s*const|m2\s*const", t, re.I):
            m = re.search(r"([\d,]+\.?\d*)", t)
            if m: r["m2_construccion"] = float(m.group(1).replace(",",""))
        elif re.search(r"m²|m2", t, re.I):
            m = re.search(r"([\d,]+\.?\d*)", t)
            if m:
                v = float(m.group(1).replace(",",""))
                if "m2_terreno" not in r: r["m2_terreno"] = v
                elif "m2_construccion" not in r: r["m2_construccion"] = v
        elif re.match(r"(\d+)\s*rec", t, re.I):
            r["recamaras"] = int(re.match(r"(\d+)", t).group(1))
        elif re.match(r"([\d.]+)\s*ba", t, re.I):
            r["banos"] = float(re.match(r"([\d.]+)", t).group(1))
        elif re.match(r"(\d+)\s*estac", t, re.I):
            r["estacionamientos"] = int(re.match(r"(\d+)", t).group(1))
    return r

# ─── Extracción con IA ────────────────────────────────────────────────────────

def _sanitizar_para_prompt(texto: str, max_chars: int = 800) -> str:
    """Elimina secuencias que podrían ser prompt injection antes de enviar a Claude."""
    if not texto:
        return ""
    # Quitar bloques que parecen instrucciones (patrones comunes de injection)
    import re as _re
    sanitizado = _re.sub(r'(?i)(ignora|ignore|forget|olvida|instrucciones|instructions)\s*(las\s*)?(anteriores?|previous|above|previas?)', '[REDACTED]', texto)
    # Limitar a max_chars
    return sanitizado[:max_chars]

def enriquecer_con_ia(descripcion: str, precio: float, colonia: str, tipo_op: str) -> dict:
    """
    Extrae todos los datos posibles de la descripción.
    Si la colonia es genérica, intenta extraer la real del texto.
    Si faltan m², los busca en la descripción.
    """
    colonia_es_mala = colonia_es_generica(colonia)

    colonia_es_mala = colonia_es_generica(colonia)
    prompt = (
        "Analiza este listing inmobiliario de Torreón, Coahuila, México.\n"
        "Responde SOLO con JSON válido, sin texto adicional.\n\n"
        f'Colonia actual: "{colonia}"\n'
        f"Precio: ${precio:,.0f} MXN\n"
        f"Operación: {tipo_op}\n"
        f"Descripción: {_sanitizar_para_prompt(descripcion)}\n\n"
        "Devuelve exactamente este JSON con valores reales (no objetos con instruccion):\n"
        "{\n"
        '  "tipo_inmueble": "casa|departamento|terreno|local_comercial|bodega|oficina|otro",\n'
        '  "estado_inmueble": "nuevo|en_construccion|remodelado|usado|no_especificado",\n'
        '  "nivel_premium": "economico|medio|residencial|premium|no_determinado",\n'
        '  "amenidades": [],\n'
        '  "uso_suelo_inferido": "habitacional|comercial|industrial|mixto|no_determinado",\n'
        '  "score_calidad_anuncio": 50,\n'
        '  "colonia_extraida": null,\n'
        '  "m2_terreno": null,\n'
        '  "m2_construccion": null,\n'
        '  "recamaras": null,\n'
        '  "banos": null\n'
        "}\n\n"
        "REGLAS:\n"
        "- colonia_extraida: si la colonia es generica (Torreon, Coahuila) extrae el fraccionamiento real de la descripcion, sino null\n"
        "- m2_terreno, m2_construccion, recamaras, banos: numeros si se mencionan, sino null\n"
        "- score_calidad_anuncio: 0-100 segun que tan completo es el anuncio"
    )

    try:
        r = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role":"user","content":prompt}]
        )
        resultado = json.loads(re.sub(r"```json|```","", r.content[0].text).strip())

        # Si IA encontró colonia mejor, usarla
        colonia_ia = resultado.get("colonia_extraida")
        if colonia_es_mala and colonia_ia and isinstance(colonia_ia, str):
            resultado["colonia"] = colonia_ia.strip()
        else:
            resultado["colonia"] = colonia if not colonia_es_mala else None

        return resultado
    except Exception as e:
        return {}

# ─── Guardado en Supabase ─────────────────────────────────────────────────────

CAMPOS_EXCLUIR = {
    "precio_x_m2",
    "precio_x_m2_terreno",
    "precio_x_m2_construccion",
    "estacionamientos",
    "colonia_extraida",
}

def guardar_listing(datos: dict) -> str:
    """
    Valida y guarda listing. Devuelve: 'nuevo', 'actualizado', 'sin_link',
    'fuera_de_torreon', 'precio_invalido'
    """
    link = datos.get("link_publicacion")
    if not link:
        return "sin_link"

    # Normalizar link
    link = link.split("?")[0].rstrip("/")
    datos["link_publicacion"] = link

    # Validar precio
    precio = datos.get("precio_mxn")
    if not precio or float(precio) < 10_000:
        return "precio_invalido"

    # Validar geografía
    if not es_de_torreon(datos.get("lat"), datos.get("lng")):
        return "fuera_de_torreon"

    # Limpiar campos no válidos
    datos = {k: v for k, v in datos.items()
             if k not in CAMPOS_EXCLUIR and v is not None and v != [] and v != ""}

    existente = supabase.table("listings")\
        .select("id, precio_mxn")\
        .eq("link_publicacion", link)\
        .execute()

    now = datetime.utcnow().isoformat()

    if existente.data:
        reg = existente.data[0]
        p_nuevo = datos.get("precio_mxn")
        p_viejo = reg.get("precio_mxn")

        if p_nuevo and p_viejo and float(p_nuevo) != float(p_viejo):
            supabase.table("historial_precios").insert({
                "listing_id": reg["id"],
                "precio_mxn": p_viejo,
            }).execute()

        supabase.table("listings").update({
            "precio_mxn":          datos.get("precio_mxn"),
            "fecha_ultimo_scrape": now,
            "activo":              True,
        }).eq("id", reg["id"]).execute()
        return "actualizado"

    else:
        datos["fecha_primer_scrape"] = now
        datos["fecha_ultimo_scrape"] = now
        datos["activo"] = True
        supabase.table("listings").insert(datos).execute()
        return "nuevo"
