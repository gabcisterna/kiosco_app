import sys
import traceback

from modules.rutas import asegurar_directorio, ruta_datos

RUTA_LOG_FALLBACK = ruta_datos("_system", "app.log")


def _append_fallback_log(salida):
    try:
        asegurar_directorio(RUTA_LOG_FALLBACK)
        with open(RUTA_LOG_FALLBACK, "a", encoding="utf-8") as archivo:
            archivo.write(salida)
    except Exception:
        pass


def _obtener_stream():
    return (
        sys.stdout
        or getattr(sys, "__stdout__", None)
        or sys.stderr
        or getattr(sys, "__stderr__", None)
    )


def log(*partes, sep=" ", end="\n"):
    texto = sep.join(str(parte) for parte in partes)
    salida = texto + end
    stream = _obtener_stream()

    if stream is None:
        _append_fallback_log(salida)
        return

    encoding = getattr(stream, "encoding", None) or "utf-8"

    try:
        stream.write(salida)
    except UnicodeEncodeError:
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            buffer.write(salida.encode(encoding, errors="replace"))
            buffer.flush()
            return

        texto_seguro = salida.encode(encoding, errors="replace").decode(encoding, errors="replace")
        try:
            stream.write(texto_seguro)
        except Exception:
            _append_fallback_log(texto_seguro)
    except Exception:
        _append_fallback_log(salida)


def registrar_excepcion(contexto, exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()

    encabezado = f"[ERROR] {contexto}\n"
    detalle = "".join(traceback.format_exception(*exc_info))
    _append_fallback_log(encabezado + detalle + "\n")
