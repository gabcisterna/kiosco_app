import json
import os

from datetime import datetime
from modules.empleados import cargar_empleados, guardar_empleados  # ✅ Importado correctamente

RUTA_EMPLEADOS = os.path.join("data", "empleados.json")
RUTA_TURNOS = os.path.join("data", "turnos.json")


def registrar_inicio_sesion(usuario):
    empleados = cargar_empleados()

    # Cerrar sesión de todos
    for e in empleados:
        e["activo"] = False

    # Activar solo el usuario que inicia sesión
    for e in empleados:
        if e["usuario"] == usuario:
            e["activo"] = True
            guardar_empleados(empleados)

            turno = {
                "empleado": usuario,
                "inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fin": None
            }

            turnos = []
            if os.path.exists(RUTA_TURNOS):
                with open(RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                    try:
                        turnos = json.load(archivo)
                    except json.JSONDecodeError:
                        print("⚠️ Error al cargar turnos.json")

            turnos.append(turno)
            with open(RUTA_TURNOS, "w", encoding="utf-8") as archivo:
                json.dump(turnos, archivo, ensure_ascii=False, indent=4)

            print(f"✅ Inicio de sesión registrado para {usuario}")
            return True

    print(f"❌ Usuario '{usuario}' no encontrado")
    return False

def cerrar_sesion():
    empleados = cargar_empleados()
    usuario_activo = None

    for e in empleados:
        if e.get("activo"):
            usuario_activo = e["usuario"]
        e["activo"] = False

    guardar_empleados(empleados)

    if not usuario_activo:
        print("❌ No hay sesión activa.")
        return False

    if os.path.exists(RUTA_TURNOS):
        with open(RUTA_TURNOS, "r", encoding="utf-8") as archivo:
            try:
                turnos = json.load(archivo)
            except json.JSONDecodeError:
                print("⚠️ Error al cargar turnos.json")
                return False

        for t in reversed(turnos):
            if t["empleado"] == usuario_activo and t["fin"] is None:
                t["fin"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break

        with open(RUTA_TURNOS, "w", encoding="utf-8") as archivo:
            json.dump(turnos, archivo, ensure_ascii=False, indent=4)

        print(f"✅ Sesión cerrada para {usuario_activo}")
        return True

    print("❌ No se encontró turnos.json.")
    return False
