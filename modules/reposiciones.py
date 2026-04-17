import json
import os
from datetime import datetime

from modules.console import log
from modules.empleados import obtener_empleado_activo
from modules.productos import (
    _float_local,
    buscar_producto,
    formatear_cantidad,
    normalizar_cantidad_guardada,
    obtener_unidad_medida,
    parsear_cantidad_para_producto,
    sumar_stock,
)
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_REGISTRO_STOCK = ruta_datos("registro_stock.json")


def cargar_registro_stock():
    if not os.path.exists(RUTA_REGISTRO_STOCK):
        return []

    with open(RUTA_REGISTRO_STOCK, "r", encoding="utf-8") as archivo:
        try:
            data = json.load(archivo)
        except json.JSONDecodeError:
            log("Error: registro_stock.json esta mal formado.")
            return []

    return data if isinstance(data, list) else []


def guardar_registro_stock(registros):
    asegurar_directorio(RUTA_REGISTRO_STOCK)
    with open(RUTA_REGISTRO_STOCK, "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, ensure_ascii=False, indent=4)


def registrar_reposicion_stock(producto_id, cantidad, precio_costo):
    producto = buscar_producto(producto_id)
    if not producto:
        return False, "No se encontro el producto."

    try:
        cantidad_normalizada = parsear_cantidad_para_producto(cantidad, producto=producto)
    except ValueError as error:
        return False, str(error)

    try:
        precio_costo = round(float(str(precio_costo).strip().replace(",", ".")), 2)
    except ValueError:
        return False, "Ingresa un precio de compra valido."

    if precio_costo < 0:
        return False, "El precio de compra no puede ser negativo."

    stock_anterior = normalizar_cantidad_guardada(producto.get("stock_actual", 0), producto=producto)
    if not sumar_stock(producto_id, cantidad_normalizada):
        return False, "No se pudo actualizar el stock."

    producto_actualizado = buscar_producto(producto_id)
    if not producto_actualizado:
        return False, "No se pudo recargar el producto despues de la reposicion."

    empleado = obtener_empleado_activo() or {}
    total_costo = round(float(cantidad_normalizada) * precio_costo, 2)
    cantidad_guardada = normalizar_cantidad_guardada(cantidad_normalizada, producto=producto_actualizado)
    stock_nuevo = normalizar_cantidad_guardada(producto_actualizado.get("stock_actual", 0), producto=producto_actualizado)

    movimiento = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": "Reposicion de stock",
        "referencia": f"ID {producto_actualizado['id']}",
        "responsable": empleado.get("nombre") or "Sin sesion",
        "monto": total_costo,
        "producto_id": int(producto_actualizado["id"]),
        "producto_nombre": producto_actualizado["nombre"],
        "cantidad": cantidad_guardada,
        "tipo_venta": producto_actualizado.get("tipo_venta", "unidad"),
        "unidad_medida": obtener_unidad_medida(producto=producto_actualizado),
        "precio_costo": precio_costo,
        "precio_venta": round(_float_local(producto_actualizado.get("precio", 0)), 2),
        "stock_anterior": stock_anterior,
        "stock_nuevo": stock_nuevo,
        "empleado_id": str(empleado.get("id", "") or ""),
        "empleado_nombre": empleado.get("nombre") or "Sin sesion",
        "detalle": [
            {
                "id": int(producto_actualizado["id"]),
                "nombre": producto_actualizado["nombre"],
                "cantidad": cantidad_guardada,
                "precio_unitario": precio_costo,
                "subtotal": total_costo,
                "tipo_venta": producto_actualizado.get("tipo_venta", "unidad"),
                "unidad_medida": obtener_unidad_medida(producto=producto_actualizado),
                "stock_anterior": stock_anterior,
                "stock_nuevo": stock_nuevo,
                "precio_venta": round(_float_local(producto_actualizado.get("precio", 0)), 2),
            }
        ],
    }

    registros = cargar_registro_stock()
    registros.append(movimiento)
    guardar_registro_stock(registros)

    log(
        "Reposicion registrada: "
        f"{producto_actualizado['nombre']} | +{formatear_cantidad(cantidad_guardada, producto=producto_actualizado, con_unidad=True)} "
        f"| costo ${precio_costo:.2f}"
    )
    return True, movimiento
