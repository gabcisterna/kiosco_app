import json
import os
from datetime import datetime

# Rutas de archivos
RUTA_DEBITO = os.path.join("data", "debito.json")
RUTA_REGISTRO_DEBITOS = os.path.join("data", "registro_debitos.json")

# Funciones utilitarias
def cargar_debito(ruta, default):
    """Carga un archivo JSON o retorna el valor por defecto si no existe o está corrupto o no es una lista."""
    if not os.path.exists(ruta):
        return default
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
            return data if isinstance(data, list) else default
    except json.JSONDecodeError:
        print(f"⚠️ Error al cargar {ruta}. Archivo JSON inválido.")
        return default


def cargar_registro_debito(ruta, default):
    if not os.path.exists(ruta):
        return default
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            data = json.load(archivo)
            return data if isinstance(data, list) else default
    except json.JSONDecodeError:
        print(f"⚠️ Error al cargar {ruta}. Archivo JSON inválido.")
        return default


def guardar_json(ruta, data):
    """Guarda un objeto Python como JSON en la ruta especificada."""
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=4)

# Funciones principales
def registrar_pago_debito(cliente_dni, monto, nombre):

    """Registra un pago por débito para un cliente, tanto en el historial como en el resumen."""
    if not isinstance(monto, (int, float)) or monto <= 0:
        print("❌ El monto debe ser un número mayor a 0.")
        return False

    # Obtener los datos actuales
    pagos = cargar_debito(RUTA_DEBITO, [])
    registro = cargar_registro_debito(RUTA_REGISTRO_DEBITOS, [])

    if not isinstance(pagos, list):
        pagos = []

    if not isinstance(registro, list):
        registro = []

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_pago = {
        "fecha": fecha_actual,
        "monto": monto
    }

    # Buscar cliente o crear nuevo
    cliente = next((p for p in pagos if p["dni"] == cliente_dni), None)


    if cliente:
        cliente["pagos"].append(nuevo_pago)
        cliente["total_pagado"] += monto
    else:
        cliente = {
            "dni": cliente_dni,
            "nombre": nombre,  # Aquí deberías buscar el nombre real del cliente
            "pagos": [nuevo_pago],
            "total_pagado": monto
        }
        pagos.append(cliente)


    # Actualizar historial de movimientos
    registro.append({
        "dni": cliente_dni,
        "nombre": nombre,
        "fecha": fecha_actual,
        "monto": monto
    })
    guardar_json(RUTA_REGISTRO_DEBITOS, registro)

    guardar_json(RUTA_DEBITO, pagos)
    print(f"🏦 Pago registrado para DNI {cliente_dni}. Total acumulado: ${cliente['total_pagado']:.2f}")
    return True

