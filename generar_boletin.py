import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

api_key = os.environ["ANTHROPIC_API_KEY"]

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

ahora = datetime.now(ZoneInfo("America/Bogota"))
fecha_str = f"{DIAS[ahora.weekday()]}, {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"
hora_str = ahora.strftime("%H:%M") + " COT"

EDICION_FILE = "edicion.txt"
try:
    with open(EDICION_FILE, "r") as f:
        edicion_actual = int(f.read().strip())
except (FileNotFoundError, ValueError):
    edicion_actual = 3

nueva_edicion = edicion_actual + 1

prompt = f"""Eres el sistema de Inteligencia de Mercados de Palermo Sociedad Portuaria (PSP), Grupo Coremar, Barranquilla, Colombia. Genera un boletín económico diario completo en HTML.

INSTRUCCIONES DE ENCABEZADO (sigue esto exactamente, sin variaciones ni texto adicional):
- Debajo de "PALERMO SOCIEDAD PORTUARIA" escribe exactamente: GRUPO COREMAR · BARRANQUILLA, COLOMBIA · INTELIGENCIA DE MERCADOS
- Debajo de "BOLETÍN ECONÓMICO DIARIO" escribe exactamente: Operaciones Portuarias (nada más)
- En la esquina superior derecha, en el lugar de la edición, escribe exactamente: Edición {nueva_edicion}
- La fecha del boletín debe ser exactamente: {fecha_str}
- El texto "Generado a las..." debe decir exactamente: Generado a las {hora_str}
- En el pie de página, el correo de contacto debe decir exactamente: alfredo.gonzales@coremar.com (nunca otro correo)
El boletín debe incluir:
1) INDICADORES CLAVE actualizados: TRM/dólar Colombia, Petróleo Brent y WTI, Gas Natural, Maíz/Soya/Trigo en Chicago, Coque metalúrgico, principales bolsas.
2) CONTEXTO INTERNACIONAL por categoría de carga portuaria: Granel limpio/cereales, Fertilizantes, Químicos y líquidos, Metálicos, Carga general (2-3 líneas cada uno). Para COQUE METALÚRGICO, profundiza más (6-8 líneas): incluye precio internacional actual y tendencia, principales países exportadores (Australia, China, Indonesia), principales países importadores/demandantes (India, Brasil), factores que están moviendo el mercado esta semana, y cómo afecta esto a las importaciones de coque por PSP Barranquilla.
3) NOTICIAS con links reales: 4 de Infraestructura (Valora Analitik), 4 Petroleras (Valora Analitik), 4 Macroeconómicas (Valora Analitik), 4 Económicas internacionales (Valora Analitik), 4 Empresariales (Valora Analitik), 4 Mercados financieros (Valora Analitik), y una sección nueva de 4 NOTICIAS DE COQUE METALÚRGICO Y CARBÓN COQUIZABLE (busca en fuentes especializadas como Argus Media, S&P Global Platts, Mining.com, o Valora Analitik si cubre el tema) sobre precios, oferta/demanda, contratos, o movimientos relevantes del mercado de coque a nivel internacional.
4) IMPLICACIONES ESTRATÉGICAS para PSP Barranquilla.

Diseño profesional navy #0a2540 y teal #13b0c4. IMPORTANTE: tu respuesta completa debe ser ÚNICAMENTE el código HTML, comenzando exactamente con <!DOCTYPE html> como primer carácter. Nunca escribas frases de introducción o confirmación antes o después del código (por ejemplo, nunca escribas "Aquí está el boletín" ni nada similar). Sin markdown, sin bloques de código, sin comillas envolventes."""

response = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 24000,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    },
    timeout=600,
)

data = response.json()

if response.status_code != 200:
    print("ERROR:", json.dumps(data, indent=2))
    raise SystemExit(1)

if data.get("stop_reason") != "end_turn":
    print("ADVERTENCIA: la respuesta se cortó antes de terminar. stop_reason:", data.get("stop_reason"))
    raise SystemExit(1)

html_parts = [block["text"] for block in data["content"] if block.get("type") == "text"]
html_completo = "".join(html_parts)

idx = html_completo.find("<!DOCTYPE html>")
if idx == -1:
    idx = html_completo.lower().find("<!doctype html>")
if idx == -1:
    print("ERROR: no se encontró <!DOCTYPE html> en la respuesta")
    raise SystemExit(1)

html_final = html_completo[idx:]

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_final)

with open(EDICION_FILE, "w") as f:
    f.write(str(nueva_edicion))

print(f"Boletín generado. Edición {nueva_edicion}, fecha {fecha_str}, hora {hora_str}. stop_reason: {data.get('stop_reason')}")
