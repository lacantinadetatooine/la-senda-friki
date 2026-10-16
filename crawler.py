import json
import re
import requests
from bs4 import BeautifulSoup

JS_FILE = "convenciones.js"


def extraer_eventos():
  with open(JS_FILE, "r", encoding="utf-8") as f:
    contenido = f.read()

  coincidencia = re.search(
      r"const\s+CONVENCIONES\s*=\s*(\[[\s\S]*?\])\s*;", contenido
  )
  if not coincidencia:
    print("No se encontró el bloque CONVENCIONES.")
    return None, contenido

  try:
    eventos = json.loads(coincidencia.group(1))
  except Exception:
    import ast

    eventos = ast.literal_eval(coincidencia.group(1))

  return eventos, contenido


def auditar_y_actualizar():
  eventos, _ = extraer_eventos()
  if not eventos:
    return

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  modificado = False
  print(f"Revisando {len(eventos)} convenciones...\n")

  for ev in eventos:
    url = ev.get("enlaceExterno", "")
    if not url or url == "#" or not url.startswith("http"):
      continue

    try:
      resp = requests.get(
          url, headers=headers, timeout=10, allow_redirects=True
      )
      if resp.status_code >= 400:
        print(f"  [AVISO] {ev['nombre']} da error {resp.status_code}")
        continue

      soup = BeautifulSoup(resp.text, "html.parser")
      og_image = soup.find("meta", property="og:image")
      if og_image and og_image.get("content"):
        img_url = og_image["content"].strip()
        if img_url.startswith("http") and not ev.get("cartel"):
          print(f"  [ACTUALIZADO] Nuevo cartel para {ev['nombre']}: {img_url}")
          ev["cartel"] = img_url
          modificado = True

    except Exception as e:
      print(f"  [ERROR] No se pudo entrar en {ev['nombre']}: {e}")

  if modificado:
    nuevo_contenido = f"const CONVENCIONES = {json.dumps(eventos, indent=2, ensure_ascii=False)};\n"
    with open(JS_FILE, "w", encoding="utf-8") as f:
      f.write(nuevo_contenido)
    print("\nArchivo convenciones.js actualizado con nuevos datos.")
  else:
    print("\nRevisión terminada: no había cambios nuevos.")


if __name__ == "__main__":
  auditar_y_actualizar()
