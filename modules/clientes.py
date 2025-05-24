import json
import os

RUTA_CLIENTES = os.path.join("data", "clientes.json")

def cargar_clientes():
    if not os.path.exists(RUTA_CLIENTES):
        return []
    with open(RUTA_CLIENTES, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            print("⚠️ Error: clientes.json está mal formado.")
            return []

def guardar_clientes(clientes):
    with open(RUTA_CLIENTES, "w", encoding="utf-8") as archivo:
        json.dump(clientes, archivo, ensure_ascii=False, indent=4)

def agregar_cliente(cliente):
    clientes = cargar_clientes()
    if any(c["dni"] == cliente["dni"] for c in clientes):
        print(f"⚠️ Ya existe un cliente con DNI {cliente['dni']}.")
        return False
    clientes.append(cliente)
    guardar_clientes(clientes)
    return True

def eliminar_cliente(dni):
    clientes = cargar_clientes()
    for i, c in enumerate(clientes):
        if c["dni"] == dni:
            del clientes[i]
            guardar_clientes(clientes)
            print(f"✅ Cliente eliminado: {c['nombre']} - DNI: {c['dni']}")
            return True
    print(f"❌ Cliente con DNI {dni} no encontrado.")
    return False

def actualizar_cliente(dni, nuevos_datos):
    clientes = cargar_clientes()
    for c in clientes:
        if c["dni"] == dni:
            c.update(nuevos_datos)
            guardar_clientes(clientes)
            print(f"✅ Cliente actualizado: {c['nombre']} - DNI: {c['dni']}")
            return True
    print(f"❌ Cliente con DNI {dni} no encontrado.")
    return False

def buscar_cliente(dni):
    dni = str(dni)  # Convertimos a string
    clientes = cargar_clientes()
    for cliente in clientes:
        if cliente.get("dni") == dni:
            return cliente
    return None

