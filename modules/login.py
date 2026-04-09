import json
import os
from datetime import datetime

from modules.console import log
from modules.empleados import cargar_empleados, guardar_empleados
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_TURNOS = ruta_datos("turnos.json")


def _identificador_empleado(empleado):
    return empleado.get("usuario") or empleado.get("correo") or empleado.get("nombre", "")


def _nombre_empleado(empleado):
    return empleado.get("nombre") or _identificador_empleado(empleado)


def _cargar_turnos():
    if not os.path.exists(RUTA_TURNOS):
        return []

    with open(RUTA_TURNOS, "r", encoding="utf-8") as archivo:
        try:
            turnos = json.load(archivo)
        except json.JSONDecodeError:
            log("Error al cargar turnos.json")
            return []

    return turnos if isinstance(turnos, list) else []


def _guardar_turnos(turnos):
    asegurar_directorio(RUTA_TURNOS)
    with open(RUTA_TURNOS, "w", encoding="utf-8") as archivo:
        json.dump(turnos, archivo, ensure_ascii=False, indent=4)


def registrar_inicio_sesion(usuario):
    empleados = cargar_empleados()
    empleado_activo = None

    for empleado in empleados:
        empleado["activo"] = False
        if _identificador_empleado(empleado) == usuario:
            empleado_activo = empleado

    if not empleado_activo:
        log(f"Error: usuario '{usuario}' no encontrado")
        return False

    empleado_activo["activo"] = True
    guardar_empleados(empleados)

    turnos = _cargar_turnos()
    turnos.append(
        {
            "empleado": _nombre_empleado(empleado_activo),
            "usuario": _identificador_empleado(empleado_activo),
            "inicio": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fin": None,
        }
    )
    _guardar_turnos(turnos)

    log(f"Inicio de sesión registrado para {_nombre_empleado(empleado_activo)}")
    return True


def cerrar_sesion():
    empleados = cargar_empleados()
    usuario_activo = None
    nombre_activo = None

    for empleado in empleados:
        if empleado.get("activo"):
            usuario_activo = _identificador_empleado(empleado)
            nombre_activo = _nombre_empleado(empleado)
        empleado["activo"] = False

    guardar_empleados(empleados)

    if not usuario_activo:
        log("Error: no hay sesión activa.")
        return False

    if not os.path.exists(RUTA_TURNOS):
        log("Error: no se encontró turnos.json.")
        return False

    turnos = _cargar_turnos()
    for turno in reversed(turnos):
        turno_usuario = turno.get("usuario", turno.get("empleado"))
        if turno_usuario == usuario_activo and turno.get("fin") is None:
            turno["fin"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _guardar_turnos(turnos)
            log(f"Sesión cerrada para {nombre_activo}")
            return True

    log("Error: no se encontró un turno abierto para la sesión activa.")
    return False
