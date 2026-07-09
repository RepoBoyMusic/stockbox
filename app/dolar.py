"""Cotización del dólar blue en vivo, vía DolarAPI (https://dolarapi.com).

Es una API pública argentina y NO requiere API key. Dos decisiones acá:

- Caché en memoria de 10 minutos: la página no golpea la API en cada
  request (la cotización no cambia segundo a segundo) y evitamos depender
  de un servicio externo para renderizar.
- Falla en silencio: si la API no responde, devolvemos la última cotización
  conocida (o None la primera vez) y la UI simplemente no muestra el dato.
  Un widget informativo nunca debe tirar abajo la tienda.
"""
import json
import time
import urllib.request

_URL = "https://dolarapi.com/v1/dolares/blue"
_TTL = 600  # segundos de validez del caché (10 minutos)
_cache = {"valor": None, "vence": 0.0}

# DolarAPI (Cloudflare) devuelve 403 al User-Agent default de Python
# ("Python-urllib/3.x"): hay que identificarse con un UA propio.
_HEADERS = {"User-Agent": "StockBox/1.0 (+https://github.com/RepoBoyMusic/stockbox)"}


def cotizacion_blue():
    """Devuelve {'compra': float, 'venta': float, 'fecha': str} o None."""
    ahora = time.time()
    if ahora < _cache["vence"]:
        return _cache["valor"]

    try:
        pedido = urllib.request.Request(_URL, headers=_HEADERS)
        with urllib.request.urlopen(pedido, timeout=4) as respuesta:
            data = json.load(respuesta)
        _cache["valor"] = {
            "compra": data["compra"],
            "venta": data["venta"],
            "fecha": data.get("fechaActualizacion", ""),
        }
    except Exception:
        pass  # nos quedamos con el último valor conocido (o None)

    _cache["vence"] = ahora + _TTL
    return _cache["valor"]
