import os
import sys


def obtener_ruta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ruta_en_base(*partes):
    return os.path.join(obtener_ruta_base(), *partes)


def ruta_datos(*partes):
    return ruta_en_base("data", *partes)


def asegurar_directorio(ruta):
    directorio = os.path.dirname(ruta)
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    return ruta
