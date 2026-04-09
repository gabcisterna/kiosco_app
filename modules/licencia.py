import hashlib
from datetime import datetime
import os

from modules.console import log
from modules.rutas import ruta_en_base

ARCHIVO_ACTIVACION = ruta_en_base("activacion.txt")
CLAVE_MAESTRA = "clave-super-secreta"


def hash_string(texto):
    return hashlib.sha256(texto.encode()).hexdigest()


def generar_clave_mensual():
    fecha = datetime.now()
    clave_base = f"clave-secreta-{fecha.year}-{fecha.month}"
    hash_resultado = hashlib.sha256(clave_base.encode()).hexdigest()
    return hash_resultado[:8]


def esta_activado():
    if not os.path.exists(ARCHIVO_ACTIVACION):
        return False

    with open(ARCHIVO_ACTIVACION, "r", encoding="utf-8") as archivo:
        contenido = archivo.read().strip()

    if contenido == hash_string("PERMANENTE"):
        return True

    ahora = datetime.now()
    valor_mes_actual = f"{ahora.year}-{ahora.month}"
    return contenido == hash_string(valor_mes_actual)


def activar(metodo="mensual"):
    with open(ARCHIVO_ACTIVACION, "w", encoding="utf-8") as archivo:
        if metodo == "permanente":
            archivo.write(hash_string("PERMANENTE"))
        elif metodo == "mensual":
            fecha = datetime.now()
            valor = f"{fecha.year}-{fecha.month}"
            archivo.write(hash_string(valor))


if __name__ == "__main__":
    log("Clave de este mes:", generar_clave_mensual())
