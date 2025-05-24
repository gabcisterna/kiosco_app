import json
import os

RUTA_EMPLEADOS = os.path.join("data", "empleados.json")

def cargar_empleados():
    if not os.path.exists(RUTA_EMPLEADOS):
        return []
    with open(RUTA_EMPLEADOS, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            print("⚠️ Error: empleados.json está mal formado.")
            return []

def guardar_empleados(empleados):
    with open(RUTA_EMPLEADOS, "w", encoding="utf-8") as archivo:
        json.dump(empleados, archivo, ensure_ascii=False, indent=4)

def agregar_empleado(nuevo_empleado):
    empleados = cargar_empleados()
    if any(e["id"] == nuevo_empleado["id"] for e in empleados):
        print(f"⚠️ Ya existe un empleado con ID {nuevo_empleado['id']}.")
        return False
    empleados.append(nuevo_empleado)
    guardar_empleados(empleados)
    print(f"✅ Empleado agregado: {nuevo_empleado['nombre']} - ID: {nuevo_empleado['id']}")
    return True

def eliminar_empleado(empleado_id):
    empleado_id = str(empleado_id)  # ✅
    empleados = cargar_empleados()
    for i, emp in enumerate(empleados):
        if emp["id"] == empleado_id:
            del empleados[i]
            guardar_empleados(empleados)
            return True


def actualizar_empleado(empleado_id, nuevos_datos):
    empleado_id = str(empleado_id)  # ✅ Conversión a string
    empleados = cargar_empleados()
    for emp in empleados:
        if emp["id"] == empleado_id:
            emp.update(nuevos_datos)
            guardar_empleados(empleados)
            return True


def buscar_empleado(empleado_id):
    empleado_id = str(empleado_id)  # ✅ Conversión a string
    empleados = cargar_empleados()
    for emp in empleados:
        if emp["id"] == empleado_id:
            return emp
    print(f"❌ Empleado con ID {empleado_id} no encontrado.")
    return None


def obtener_empleado_activo():
    empleados = cargar_empleados()
    for e in empleados:
        if e.get("activo"):
            return e
    return None


