import sys


def log(*partes, sep=" ", end="\n"):
    texto = sep.join(str(parte) for parte in partes)
    salida = texto + end
    stream = sys.stdout
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
        stream.write(texto_seguro)
