import json
import os
from datetime import datetime

from modules.clientes import buscar_cliente, cargar_clientes, guardar_clientes
from modules.console import log
from modules.productos import buscar_producto
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_DEUDAS = ruta_datos("deudas.json")
RUTA_REGISTRO_DEUDAS = ruta_datos("registro_deudas.json")


def cargar_json(ruta):
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as archivo:
        try:
            data = json.load(archivo)
        except json.JSONDecodeError:
            return []

    return data if isinstance(data, list) else []


def guardar_json(ruta, data):
    asegurar_directorio(ruta)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=4)


def cargar_registro_deudas():
    return cargar_json(RUTA_REGISTRO_DEUDAS)


def registrar_movimiento_deuda(tipo, cliente_dni, monto, nombre, detalle=None):
    registro = cargar_registro_deudas()
    movimiento = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,
        "dni": str(cliente_dni),
        "nombre": nombre,
        "monto": round(float(monto), 2),
    }

    if detalle is not None:
        movimiento["detalle"] = detalle

    registro.append(movimiento)
    guardar_json(RUTA_REGISTRO_DEUDAS, registro)


def _normalizar_item_producto(item):
    cantidad_total = int(item.get("cantidad_total", item.get("cantidad", 0)))
    cantidad_pagada = int(item.get("cantidad_pagada", 0))

    return {
        "id": int(item["id"]),
        "nombre": item.get("nombre", ""),
        "cantidad_total": max(cantidad_total, 0),
        "cantidad_pagada": max(min(cantidad_pagada, cantidad_total), 0),
    }


def _precio_actual_producto(producto_id):
    producto = buscar_producto(producto_id)
    if not producto:
        return None
    return float(producto.get("precio", 0))


def _enriquecer_item(item):
    item = _normalizar_item_producto(item)

    precio_actual = _precio_actual_producto(item["id"])
    if precio_actual is None:
        precio_actual = 0.0

    cantidad_pendiente = item["cantidad_total"] - item["cantidad_pagada"]

    return {
        **item,
        "precio_actual": round(precio_actual, 2),
        "cantidad_pendiente": cantidad_pendiente,
        "subtotal_pendiente": round(cantidad_pendiente * precio_actual, 2),
        "subtotal_total_actual": round(item["cantidad_total"] * precio_actual, 2),
    }


def _monto_pendiente_deuda(deuda):
    total = 0.0
    for item in deuda.get("productos", []):
        total += _enriquecer_item(item)["subtotal_pendiente"]
    return round(total, 2)


def _monto_productos(productos):
    total = 0.0
    for producto in productos:
        total += _enriquecer_item(producto)["subtotal_pendiente"]
    return round(total, 2)


def _normalizar_deuda(deuda):
    productos = [_normalizar_item_producto(producto) for producto in deuda.get("productos", [])]
    pagos = deuda.get("pagos", [])

    deuda_normalizada = {
        "dni": str(deuda.get("dni", "")),
        "nombre": deuda.get("nombre", ""),
        "productos": productos,
        "pagos": pagos,
    }
    deuda_normalizada["monto"] = _monto_pendiente_deuda(deuda_normalizada)
    return deuda_normalizada


def _sincronizar_deuda_clientes(deudas):
    clientes = cargar_clientes()
    if not clientes:
        return

    montos_por_dni = {
        str(deuda["dni"]): round(float(deuda.get("monto", 0) or 0), 2)
        for deuda in deudas
    }

    actualizado = False
    for cliente in clientes:
        dni = str(cliente.get("dni", ""))
        nuevo_monto = montos_por_dni.get(dni, 0.0)
        monto_actual = round(float(cliente.get("deuda", 0) or 0), 2)
        if monto_actual != nuevo_monto:
            cliente["deuda"] = nuevo_monto
            actualizado = True

    if actualizado:
        guardar_clientes(clientes)


def cargar_deudas():
    deudas = cargar_json(RUTA_DEUDAS)
    deudas_normalizadas = [_normalizar_deuda(deuda) for deuda in deudas]

    if deudas != deudas_normalizadas:
        _guardar_deudas_normalizadas(deudas_normalizadas)
    else:
        _sincronizar_deuda_clientes(deudas_normalizadas)

    return deudas_normalizadas


def _guardar_deudas_normalizadas(deudas):
    deudas_limpias = []

    for deuda in deudas:
        deuda_normalizada = _normalizar_deuda(deuda)
        productos_filtrados = []

        for producto in deuda_normalizada["productos"]:
            producto_enriquecido = _enriquecer_item(producto)
            if producto_enriquecido["cantidad_pendiente"] > 0 or producto_enriquecido["cantidad_pagada"] > 0:
                productos_filtrados.append(
                    {
                        "id": producto_enriquecido["id"],
                        "nombre": producto_enriquecido["nombre"],
                        "cantidad_total": producto_enriquecido["cantidad_total"],
                        "cantidad_pagada": producto_enriquecido["cantidad_pagada"],
                    }
                )

        deuda_normalizada["productos"] = productos_filtrados
        deuda_normalizada["monto"] = _monto_pendiente_deuda(deuda_normalizada)

        if deuda_normalizada["monto"] > 0 or deuda_normalizada["productos"] or deuda_normalizada["pagos"]:
            deudas_limpias.append(deuda_normalizada)

    guardar_json(RUTA_DEUDAS, deudas_limpias)
    _sincronizar_deuda_clientes(deudas_limpias)


def recalcular_deudas_pendientes():
    deudas = cargar_json(RUTA_DEUDAS)
    _guardar_deudas_normalizadas(deudas)
    return cargar_deudas()


def registrar_deuda(cliente_dni, productos, monto, nombre):
    _ = monto
    deudas = cargar_deudas()

    cliente = buscar_cliente(cliente_dni)
    if not cliente:
        log(f"Error: cliente con DNI {cliente_dni} no encontrado.")
        return False

    deuda_existente = next((deuda for deuda in deudas if deuda["dni"] == str(cliente_dni)), None)

    productos_nuevos = [
        {
            "id": int(producto["id"]),
            "nombre": producto.get("nombre", ""),
            "cantidad_total": int(producto.get("cantidad", 0)),
            "cantidad_pagada": 0,
        }
        for producto in productos
    ]

    if deuda_existente:
        for nuevo in productos_nuevos:
            existente = next(
                (producto for producto in deuda_existente["productos"] if int(producto["id"]) == int(nuevo["id"])),
                None,
            )
            if existente:
                existente["cantidad_total"] = int(
                    existente.get("cantidad_total", existente.get("cantidad", 0))
                ) + nuevo["cantidad_total"]
            else:
                deuda_existente["productos"].append(nuevo)
    else:
        deuda_existente = {
            "dni": str(cliente_dni),
            "nombre": nombre,
            "productos": productos_nuevos,
            "pagos": [],
        }
        deudas.append(deuda_existente)

    _guardar_deudas_normalizadas(deudas)
    registrar_movimiento_deuda(
        "carga",
        str(cliente_dni),
        _monto_productos(productos_nuevos),
        nombre,
        detalle=productos_nuevos,
    )

    log(f"Deuda registrada para {nombre} (DNI {cliente_dni}).")
    return True


def pagar_productos_deuda(cliente_dni, items_a_pagar):
    deudas = cargar_deudas()
    deuda = next((deuda for deuda in deudas if deuda["dni"] == str(cliente_dni)), None)

    if not deuda:
        log(f"Error: no se encontró deuda para el cliente con DNI {cliente_dni}")
        return False, "No se encontró la deuda."

    detalle_pago = []
    total_pagado = 0.0

    for item_pago in items_a_pagar:
        producto_id = int(item_pago["id"])
        cantidad_a_pagar = int(item_pago["cantidad"])

        if cantidad_a_pagar <= 0:
            continue

        deuda_item = next((producto for producto in deuda["productos"] if int(producto["id"]) == producto_id), None)
        if not deuda_item:
            continue

        deuda_item_enriquecido = _enriquecer_item(deuda_item)
        pendiente = deuda_item_enriquecido["cantidad_pendiente"]
        if pendiente <= 0:
            continue

        cantidad_real = min(cantidad_a_pagar, pendiente)
        precio_actual = deuda_item_enriquecido["precio_actual"]
        subtotal = round(cantidad_real * precio_actual, 2)

        item_real = next((producto for producto in deuda["productos"] if int(producto["id"]) == producto_id), None)
        item_real["cantidad_pagada"] = int(item_real.get("cantidad_pagada", 0)) + cantidad_real

        detalle_pago.append(
            {
                "id": producto_id,
                "nombre": deuda_item_enriquecido["nombre"],
                "cantidad": cantidad_real,
                "precio_unitario": precio_actual,
                "subtotal": subtotal,
            }
        )
        total_pagado += subtotal

    if total_pagado <= 0:
        return False, "No se seleccionaron productos válidos para pagar."

    deuda["monto"] = _monto_pendiente_deuda(deuda)
    deuda["pagos"].append(
        {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "monto": round(total_pagado, 2),
            "detalle": detalle_pago,
        }
    )

    registrar_movimiento_deuda(
        "pago",
        str(cliente_dni),
        total_pagado,
        deuda.get("nombre", ""),
        detalle=detalle_pago,
    )

    deuda["productos"] = [
        _normalizar_item_producto(producto)
        for producto in deuda["productos"]
        if _enriquecer_item(producto)["cantidad_pendiente"] > 0
    ]
    deuda["monto"] = _monto_pendiente_deuda(deuda)

    if deuda["monto"] <= 0:
        deudas = [deuda_actual for deuda_actual in deudas if deuda_actual["dni"] != str(cliente_dni)]
    else:
        for i, deuda_actual in enumerate(deudas):
            if deuda_actual["dni"] == str(cliente_dni):
                deudas[i] = deuda
                break

    _guardar_deudas_normalizadas(deudas)
    return True, f"Pago registrado por ${total_pagado:.2f}"


def pagar_deuda(cliente_dni, pago):
    deudas = cargar_deudas()
    deuda = next((deuda for deuda in deudas if deuda["dni"] == str(cliente_dni)), None)
    if not deuda:
        return False

    try:
        pago = float(pago)
    except (TypeError, ValueError):
        return False

    if pago <= 0:
        return False

    items_a_pagar = []
    restante = round(pago, 2)

    for item in deuda.get("productos", []):
        item_enriquecido = _enriquecer_item(item)
        if item_enriquecido["cantidad_pendiente"] <= 0 or item_enriquecido["precio_actual"] <= 0:
            continue

        max_unidades = int(restante // item_enriquecido["precio_actual"])
        if max_unidades <= 0:
            continue

        cantidad = min(max_unidades, item_enriquecido["cantidad_pendiente"])
        if cantidad > 0:
            items_a_pagar.append({"id": item_enriquecido["id"], "cantidad": cantidad})
            restante = round(restante - (cantidad * item_enriquecido["precio_actual"]), 2)

        if restante <= 0:
            break

    ok, _ = pagar_productos_deuda(cliente_dni, items_a_pagar)
    return ok


def listar_deudas():
    return cargar_deudas()
