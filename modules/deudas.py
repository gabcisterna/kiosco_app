import json
import os
from datetime import datetime

from modules.clientes import buscar_cliente

RUTA_DEUDAS = os.path.join("data", "deudas.json")
RUTA_REGISTRO_DEUDAS = os.path.join("data", "registro_deudas.json")

def cargar_deudas():
    """Carga y devuelve la lista de productos desde productos.json"""
    if not os.path.exists(RUTA_DEUDAS):
        return []  # Si no existe, devolvemos lista vacía
    
    with open(RUTA_DEUDAS, "r", encoding="utf-8") as archivo:
        try:
            productos = json.load(archivo)
            return productos
        except json.JSONDecodeError:
            print("⚠️ Error: productos.json está mal formado.")
            return []

def cargar_registro_deudas():
    """Carga y devuelve la lista de productos desde productos.json"""
    if not os.path.exists(RUTA_REGISTRO_DEUDAS):
        return []  # Si no existe, devolvemos lista vacía
    
    with open(RUTA_REGISTRO_DEUDAS, "r", encoding="utf-8") as archivo:
        try:
            productos = json.load(archivo)
            return productos
        except json.JSONDecodeError:
            print("⚠️ Error: productos.json está mal formado.")
            return []

def guardar_json(ruta, data):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=4)

def registrar_movimiento_deuda(tipo, cliente_dni, monto, nombre, detalle=None):
    registro = cargar_registro_deudas()
    movimiento = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,  # "carga" o "pago"
        "dni": cliente_dni,
        "nombre": nombre,
        "monto": monto
    }
    if detalle:
        movimiento["detalle"] = detalle
    registro.append(movimiento)
    guardar_json(RUTA_REGISTRO_DEUDAS, registro)

from modules.clientes import buscar_cliente

def registrar_deuda(cliente_dni, productos, monto, nombre):
    deudas = cargar_deudas()

    # Buscar cliente para obtener el nombre
    cliente = buscar_cliente(cliente_dni)
    if not cliente:
        print(f"❌ Cliente con DNI {cliente_dni} no encontrado.")
        return False


    deuda_existente = next((d for d in deudas if d["dni"] == cliente_dni), None)

    if deuda_existente:
        deuda_existente["monto"] += monto
        deuda_existente["productos"].extend(productos)
    else:
        deuda_existente = {
            "dni": cliente_dni,
            "nombre": nombre,  # ✅ Incluir nombre
            "monto": monto,
            "productos": productos,
            "pagos": []
        }
        deudas.append(deuda_existente)
    

    guardar_json(RUTA_DEUDAS, deudas)
    registrar_movimiento_deuda("carga", cliente_dni, monto, nombre, detalle=productos)

    print(f"💰 Deuda registrada para {nombre} (DNI {cliente_dni}). Total adeudado: ${deuda_existente['monto']:.2f}")
    return True



def pagar_deuda(cliente_dni, pago):
    deudas = cargar_deudas()
    deuda = next((d for d in deudas if d["dni"] == cliente_dni), None)

    nombre=deuda["nombre"]
    print(f"💳 Pago de deuda para {nombre} (DNI {cliente_dni})")
    if not deuda:
        print(f"❌ No se encontró deuda para el cliente con DNI {cliente_dni}")
        return False

    monto_adeudado = deuda["monto"]

    if pago <= 0:
        print("❌ El monto pagado debe ser mayor que 0.")
        return False

    if pago > monto_adeudado:
        vuelto = round(pago - monto_adeudado, 2)
        pago_realizado = monto_adeudado
    else:
        vuelto = 0
        pago_realizado = pago

    deuda["monto"] -= pago_realizado
    deuda["pagos"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pago": pago_realizado
    })

    registrar_movimiento_deuda("pago", cliente_dni, pago_realizado, nombre)

    if deuda["monto"] <= 0:
        deudas = [d for d in deudas if d["dni"] != cliente_dni]
        print(f"✅ Deuda saldada completamente. Vuelto: ${vuelto:.2f}")
    else:
        print(f"💳 Pago registrado: ${pago_realizado:.2f}. Deuda restante: ${deuda['monto']:.2f}, Vuelto: ${vuelto:.2f}")

    guardar_json(RUTA_DEUDAS, deudas)
    return True

