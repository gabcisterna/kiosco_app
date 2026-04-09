import json
import os
from datetime import datetime

from modules.console import log
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_DEBITO = ruta_datos("debito.json")
RUTA_REGISTRO_DEBITOS = ruta_datos("registro_debitos.json")


def cargar_debito(ruta, default):
    if not os.path.exists(ruta):
        return default

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
            return data if isinstance(data, list) else default
    except json.JSONDecodeError:
        log(f"Error al cargar {ruta}. Archivo JSON inválido.")
        return default


def cargar_registro_debito(ruta, default):
    if not os.path.exists(ruta):
        return default

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
            return data if isinstance(data, list) else default
    except json.JSONDecodeError:
        log(f"Error al cargar {ruta}. Archivo JSON inválido.")
        return default


def guardar_json(ruta, data):
    asegurar_directorio(ruta)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=4)


def registrar_pago_debito(cliente_dni, monto, nombre):
    if not isinstance(monto, (int, float)) or monto <= 0:
        log("Error: el monto debe ser un número mayor a 0.")
        return False

    pagos = cargar_debito(RUTA_DEBITO, [])
    registro = cargar_registro_debito(RUTA_REGISTRO_DEBITOS, [])

    if not isinstance(pagos, list):
        pagos = []

    if not isinstance(registro, list):
        registro = []

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_pago = {
        "fecha": fecha_actual,
        "monto": monto,
    }

    cliente = next((p for p in pagos if p["dni"] == cliente_dni), None)

    if cliente:
        cliente["pagos"].append(nuevo_pago)
        cliente["total_pagado"] += monto
    else:
        cliente = {
            "dni": cliente_dni,
            "nombre": nombre,
            "pagos": [nuevo_pago],
            "total_pagado": monto,
        }
        pagos.append(cliente)

    registro.append(
        {
            "dni": cliente_dni,
            "nombre": nombre,
            "fecha": fecha_actual,
            "monto": monto,
        }
    )

    guardar_json(RUTA_REGISTRO_DEBITOS, registro)
    guardar_json(RUTA_DEBITO, pagos)
    log(f"Pago registrado para DNI {cliente_dni}. Total acumulado: ${cliente['total_pagado']:.2f}")
    return True


def listar_pagos_debito():
    return cargar_debito(RUTA_DEBITO, [])


def listar_registro_debitos():
    return cargar_registro_debito(RUTA_REGISTRO_DEBITOS, [])
