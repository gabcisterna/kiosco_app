import json
import os
import sys
from datetime import datetime

from modules.clientes import buscar_cliente, actualizar_cliente
from modules.productos import buscar_producto


def _obtener_ruta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


RUTA_DEUDAS = os.path.join(_obtener_ruta_base(), "data", "deudas.json")
RUTA_REGISTRO_DEUDAS = os.path.join(_obtener_ruta_base(), "data", "registro_deudas.json")


def cargar_json(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            return []


def guardar_json(ruta, data):
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
    """
    Soporta formato viejo:
      {id, nombre, cantidad, subtotal}
    y formato nuevo:
      {id, nombre, cantidad_total, cantidad_pagada}
    """
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
        item_ok = _enriquecer_item(item)
        total += item_ok["subtotal_pendiente"]
    return round(total, 2)


def _normalizar_deuda(deuda):
    productos = [_normalizar_item_producto(p) for p in deuda.get("productos", [])]
    pagos = deuda.get("pagos", [])

    deuda_ok = {
        "dni": str(deuda.get("dni", "")),
        "nombre": deuda.get("nombre", ""),
        "productos": productos,
        "pagos": pagos,
    }
    deuda_ok["monto"] = _monto_pendiente_deuda(deuda_ok)
    return deuda_ok


def cargar_deudas():
    deudas = cargar_json(RUTA_DEUDAS)
    return [_normalizar_deuda(d) for d in deudas]


def _guardar_deudas_normalizadas(deudas):
    deudas_limpias = []

    for deuda in deudas:
        deuda_ok = _normalizar_deuda(deuda)

        productos_filtrados = []
        for p in deuda_ok["productos"]:
            p_enriquecido = _enriquecer_item(p)

            # Conserva productos pendientes o con algo ya pagado
            if p_enriquecido["cantidad_pendiente"] > 0 or p_enriquecido["cantidad_pagada"] > 0:
                productos_filtrados.append({
                    "id": p_enriquecido["id"],
                    "nombre": p_enriquecido["nombre"],
                    "cantidad_total": p_enriquecido["cantidad_total"],
                    "cantidad_pagada": p_enriquecido["cantidad_pagada"]
                })

        deuda_ok["productos"] = productos_filtrados
        deuda_ok["monto"] = _monto_pendiente_deuda(deuda_ok)

        # Si ya no debe nada y no querés conservar historial vacío, no la guardes
        if deuda_ok["monto"] > 0 or deuda_ok["productos"] or deuda_ok["pagos"]:
            deudas_limpias.append(deuda_ok)

    guardar_json(RUTA_DEUDAS, deudas_limpias)


def registrar_deuda(cliente_dni, productos, monto, nombre):
    deudas = cargar_deudas()

    cliente = buscar_cliente(cliente_dni)
    if not cliente:
        print(f"❌ Cliente con DNI {cliente_dni} no encontrado.")
        return False

    deuda_existente = next((d for d in deudas if d["dni"] == str(cliente_dni)), None)

    productos_nuevos = []
    for p in productos:
        productos_nuevos.append({
            "id": int(p["id"]),
            "nombre": p.get("nombre", ""),
            "cantidad_total": int(p.get("cantidad", 0)),
            "cantidad_pagada": 0
        })

    if deuda_existente:
        for nuevo in productos_nuevos:
            existente = next(
                (x for x in deuda_existente["productos"] if int(x["id"]) == int(nuevo["id"])),
                None
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
            "pagos": []
        }
        deudas.append(deuda_existente)

    deuda_existente["monto"] = _monto_pendiente_deuda(deuda_existente)
    _guardar_deudas_normalizadas(deudas)

    registrar_movimiento_deuda(
        "carga",
        str(cliente_dni),
        deuda_existente["monto"],
        nombre,
        detalle=productos_nuevos
    )

    cliente = buscar_cliente(cliente_dni)
    if cliente:
        actualizar_cliente(cliente_dni, {"deuda": deuda_existente["monto"]})

    print(f"✅ Deuda registrada para {nombre} (DNI {cliente_dni}).")
    return True


def pagar_productos_deuda(cliente_dni, items_a_pagar):
    """
    items_a_pagar:
    [
        {"id": 1, "cantidad": 2},
        {"id": 3, "cantidad": 1}
    ]
    """
    deudas = cargar_deudas()
    deuda = next((d for d in deudas if d["dni"] == str(cliente_dni)), None)

    if not deuda:
        print(f"❌ No se encontró deuda para el cliente con DNI {cliente_dni}")
        return False, "No se encontró la deuda."

    detalle_pago = []
    total_pagado = 0.0

    for item_pago in items_a_pagar:
        producto_id = int(item_pago["id"])
        cantidad_a_pagar = int(item_pago["cantidad"])

        if cantidad_a_pagar <= 0:
            continue

        deuda_item = next((p for p in deuda["productos"] if int(p["id"]) == producto_id), None)
        if not deuda_item:
            continue

        deuda_item_enriquecido = _enriquecer_item(deuda_item)
        pendiente = deuda_item_enriquecido["cantidad_pendiente"]

        if pendiente <= 0:
            continue

        cantidad_real = min(cantidad_a_pagar, pendiente)
        precio_actual = deuda_item_enriquecido["precio_actual"]
        subtotal = round(cantidad_real * precio_actual, 2)

        item_real = next((p for p in deuda["productos"] if int(p["id"]) == producto_id), None)
        item_real["cantidad_pagada"] = int(item_real.get("cantidad_pagada", 0)) + cantidad_real

        detalle_pago.append({
            "id": producto_id,
            "nombre": deuda_item_enriquecido["nombre"],
            "cantidad": cantidad_real,
            "precio_unitario": precio_actual,
            "subtotal": subtotal
        })
        total_pagado += subtotal

    if total_pagado <= 0:
        return False, "No se seleccionaron productos válidos para pagar."

    deuda["monto"] = _monto_pendiente_deuda(deuda)
    deuda["pagos"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "monto": round(total_pagado, 2),
        "detalle": detalle_pago
    })

    registrar_movimiento_deuda(
        "pago",
        str(cliente_dni),
        total_pagado,
        deuda.get("nombre", ""),
        detalle=detalle_pago
    )

    deuda["productos"] = [
        _normalizar_item_producto(p)
        for p in deuda["productos"]
        if _enriquecer_item(p)["cantidad_pendiente"] > 0
    ]

    deuda["monto"] = _monto_pendiente_deuda(deuda)

    if deuda["monto"] <= 0:
        deudas = [d for d in deudas if d["dni"] != str(cliente_dni)]
        nuevo_monto_cliente = 0
    else:
        for i, d in enumerate(deudas):
            if d["dni"] == str(cliente_dni):
                deudas[i] = deuda
                break
        nuevo_monto_cliente = deuda["monto"]

    _guardar_deudas_normalizadas(deudas)

    cliente = buscar_cliente(cliente_dni)
    if cliente:
        actualizar_cliente(cliente_dni, {"deuda": nuevo_monto_cliente})

    return True, f"Pago registrado por ${total_pagado:.2f}"


def pagar_deuda(cliente_dni, pago):
    """
    Compatibilidad con la función vieja.
    Intenta saldar productos en orden hasta cubrir el monto ingresado.
    """
    deudas = cargar_deudas()
    deuda = next((d for d in deudas if d["dni"] == str(cliente_dni)), None)

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
        item_ok = _enriquecer_item(item)
        if item_ok["cantidad_pendiente"] <= 0 or item_ok["precio_actual"] <= 0:
            continue

        max_unidades = int(restante // item_ok["precio_actual"])
        if max_unidades <= 0:
            continue

        cantidad = min(max_unidades, item_ok["cantidad_pendiente"])
        if cantidad > 0:
            items_a_pagar.append({"id": item_ok["id"], "cantidad": cantidad})
            restante = round(restante - (cantidad * item_ok["precio_actual"]), 2)

        if restante <= 0:
            break

    ok, _ = pagar_productos_deuda(cliente_dni, items_a_pagar)
    return ok