import os
import json
from datetime import datetime

from modules.clientes import buscar_cliente, actualizar_cliente, agregar_cliente
from modules.empleados import buscar_empleado, cargar_empleados
from modules.productos import restar_stock, buscar_producto
from modules.debito import registrar_pago_debito
from modules.deudas import registrar_deuda

RUTA_VENTAS = os.path.join("data", "ventas.json")


def cargar_ventas():
    if not os.path.exists(RUTA_VENTAS):
        return []
    with open(RUTA_VENTAS, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            print("⚠️ Error al cargar ventas.json")
            return []


def guardar_ventas(ventas):
    with open(RUTA_VENTAS, "w", encoding="utf-8") as archivo:
        json.dump(ventas, archivo, ensure_ascii=False, indent=4)


def obtener_empleado_activo():
    empleados = cargar_empleados()
    for emp in empleados:
        if emp.get("activo"):
            return emp
    return None


def registrar_venta(productos_vendidos, forma_pago, cliente_dni=None, cliente_nombre=None):
    empleado = obtener_empleado_activo()
    if not empleado:
        print("❌ No hay ningún empleado activo.")
        return False
    empleado_id = empleado["id"]

    cliente = None
    if cliente_dni:
        cliente = buscar_cliente(cliente_dni)
        if not cliente:
            print(f"⚠️ Cliente con DNI {cliente_dni} no encontrado. Se registrará automáticamente.")
            cliente = {
                "dni": cliente_dni,
                "nombre": cliente_nombre,
                "deuda": 0,
            }
            agregar_cliente(cliente)
        else:
            cliente_nombre = cliente["nombre"]

    # Validar productos y stock
    total = 0
    detalle_productos = []
    for item in productos_vendidos:
        producto = buscar_producto(item["id"])
        if not producto:
            return False
        if producto["stock_actual"] < item["cantidad"]:
            print(f"❌ No hay suficiente stock para el producto {producto['nombre']}.")
            return False

        subtotal = producto["precio"] * item["cantidad"]
        total += subtotal
        detalle_productos.append({
            "id": producto["id"],
            "nombre": producto["nombre"],
            "cantidad": item["cantidad"],
            "subtotal": subtotal
        })

    # Validar forma de pago
    if forma_pago == "debito":
        if not cliente:
            print("❌ No se puede registrar un pago por débito sin un cliente.")
            return False
    elif forma_pago == "deuda":
        if not cliente:
            print("❌ No se puede fiar una venta sin un cliente.")
            return False
    elif forma_pago != "efectivo":
        print("⚠️ Forma de pago inválida. Use 'efectivo', 'debito' o 'deuda'.")
        return False

    # Restar stock
    for item in productos_vendidos:
        restar_stock(item["id"], item["cantidad"])

    # Procesar forma de pago
    if forma_pago == "debito":
        registrar_pago_debito(cliente_dni, total, cliente_nombre)
    elif forma_pago == "deuda":
        registrar_deuda(cliente_dni, detalle_productos, total, cliente_nombre)
        cliente["deuda"] += total
        actualizar_cliente(cliente_dni, {"deuda": cliente["deuda"]})

    # Registrar venta
    ventas = cargar_ventas()
    nueva_venta = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "empleado_id": empleado_id,
        "cliente_dni": cliente_dni if cliente else None,
        "forma_pago": forma_pago,
        "total": total,
        "productos": detalle_productos
    }
    ventas.append(nueva_venta)
    guardar_ventas(ventas)
    print("✅ Venta registrada correctamente.")
    return True
