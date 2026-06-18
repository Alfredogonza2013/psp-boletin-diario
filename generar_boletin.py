import os
import json
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

api_key = os.environ["ANTHROPIC_API_KEY"]

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

ahora = datetime.now(ZoneInfo("America/Bogota"))
fecha_str = f"{DIAS[ahora.weekday()]}, {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"

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
- El texto "Generado a las..." debe decir exactamente: Generado a las MARCADOR_HORA COT
- En el pie de página, el correo de contacto debe decir exactamente: alfredo.gonzales@coremar.com (nunca otro correo)

El boletín debe incluir:
1) INDICADORES CLAVE actualizados: TRM/dólar Colombia, Petróleo Brent y WTI, Gas Natural, Maíz/Soya/Trigo en Chicago, Coque metalúrgico, principales bolsas.
2) CONTEXTO INTERNACIONAL por categoría de carga portuaria: Granel limpio/cereales, Fertilizantes, Químicos y líquidos, Metálicos, Carga general (2-3 líneas cada uno). Para COQUE METALÚRGICO, profundiza más (6-8 líneas): incluye precio internacional actual y tendencia, principales países exportadores (Australia, China, Indonesia), principales países importadores/demandantes (India, Brasil), factores que están moviendo el mercado esta semana, y cómo afecta esto a las importaciones de coque por PSP Barranquilla.
3) NOTICIAS con links reales: 4 de Infraestructura (Valora Analitik), 4 Petroleras (Valora Analitik), 4 Macroeconómicas (Valora Analitik), 4 Económicas internacionales (Valora Analitik), 4 Empresariales (Valora Analitik), 4 Mercados financieros (Valora Analitik), y una sección nueva de 4 NOTICIAS DE COQUE METALÚRGICO Y CARBÓN COQUIZABLE (busca en fuentes especializadas como Argus Media, S&P Global Platts, Mining.com, o Valora Analitik si cubre el tema) sobre precios, oferta/demanda, contratos, o movimientos relevantes del mercado de coque a nivel internacional.
4) IMPLICACIONES ESTRATÉGICAS para PSP Barranquilla.

Diseño profesional navy #0a2540 y teal #13b0c4. INSTRUCCIONES DE DISEÑO OBLIGATORIAS: (1) Inmediatamente después del header principal incluye una BARRA TICKER animada (CSS keyframes, animación infinita de derecha a izquierda) con fondo #0a2540 y texto en #13b0c4, mostrando los indicadores del día separados por espaciadores: TRM · Brent · WTI · Gas Natural · Maíz Chicago · Soya Chicago · Trigo Chicago · Coque metalúrgico. Cada indicador muestra su valor y flecha de tendencia ↑ o ↓. (2) Los indicadores clave también aparecen en tarjetas visuales con ícono, valor grande, variación porcentual y flecha de color (verde subida, rojo bajada). (3) Tipografía Segoe UI, tarjetas con sombra suave, bordes redondeados, fondo gris muy claro #f4f6f8. IMPORTANTE: tu respuesta completa debe ser ÚNICAMENTE el código HTML, comenzando exactamente con <!DOCTYPE html> como primer carácter. Nunca escribas frases de introducción o confirmación antes o después del código. Sin markdown, sin bloques de código, sin comillas envolventes.

def generar_con_streaming(url, headers, payload, timeout=600):
    full_text = ""
    current_block_type = None
    stop_reason = None

    with requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout) as resp:
        if resp.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP {resp.status_code}: {resp.text}")
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data:"):
                continue
            data_str = raw_line[len("data:"):].strip()
            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            if etype == "content_block_start":
                current_block_type = event.get("content_block", {}).get("type")
            elif etype == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta" and current_block_type == "text":
                    full_text += delta.get("text", "")
            elif etype == "content_block_stop":
                current_block_type = None
            elif etype == "message_delta":
                stop_reason = event.get("delta", {}).get("stop_reason", stop_reason)
            elif etype == "error":
                raise RuntimeError(f"Error de la API durante streaming: {event}")

    return full_text, stop_reason


payload = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 24000,
    "stream": True,
    "messages": [{"role": "user", "content": prompt}],
    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
}
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

MAX_REINTENTOS = 3
html_completo = None
stop_reason = None
ultimo_error = None

for intento in range(1, MAX_REINTENTOS + 1):
    try:
        html_completo, stop_reason = generar_con_streaming(
            "https://api.anthropic.com/v1/messages", headers, payload, timeout=600
        )
        break
    except requests.exceptions.RequestException as e:
        ultimo_error = e
        print(f"Intento {intento} fallo por error de conexion: {e}")
        if intento < MAX_REINTENTOS:
            time.sleep(15)

if html_completo is None:
    print(f"ERROR: no se pudo conectar con la API despues de {MAX_REINTENTOS} intentos. Ultimo error: {ultimo_error}")
    raise SystemExit(1)

if stop_reason != "end_turn":
    print("ADVERTENCIA: la respuesta se cortó antes de terminar. stop_reason:", stop_reason)
    raise SystemExit(1)

idx = html_completo.find("<!DOCTYPE html>")
if idx == -1:
    idx = html_completo.lower().find("<!doctype html>")
if idx == -1:
    print("ERROR: no se encontró <!DOCTYPE html> en la respuesta")
    raise SystemExit(1)

html_final = html_completo[idx:]

hora_real = datetime.now(ZoneInfo("America/Bogota")).strftime("%H:%M")
html_final = html_final.replace("MARCADOR_HORA", hora_real)

BOTON_PDF = """
<style>
  @media print { #btn-descargar-pdf { display: none !important; } }
  #btn-descargar-pdf {
    position: fixed; bottom: 24px; right: 24px;
    background: #13b0c4; color: #fff; border: none;
    padding: 14px 22px; border-radius: 8px; font-weight: bold;
    font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px;
    cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.25); z-index: 9999;
  }
  #btn-descargar-pdf:hover { background: #0a8a9a; }
</style>
<button id="btn-descargar-pdf" onclick="window.print()">📥 Descargar PDF</button>
"""

if "</body>" in html_final:
    html_final = html_final.replace("</body>", BOTON_PDF + "</body>")
else:
    html_final = html_final + BOTON_PDF

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_final)

with open(EDICION_FILE, "w") as f:
    f.write(str(nueva_edicion))

print(f"Boletín generado. Edición {nueva_edicion}, fecha {fecha_str}, hora {hora_real}. stop_reason: {stop_reason}")
