import json
import os
import unicodedata

from modules.console import log
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_EMPLEADOS = ruta_datos("empleados.json")

PUESTO_DUENO = "Dueño"
PUESTO_ENCARGADO = "Encargado"
PUESTO_CAJERO = "Cajero"
PUESTO_REPOSITOR = "Repositor"
PUESTO_CONSULTA_PRODUCTOS = "Consulta productos"

PUESTOS_DISPONIBLES = [
    PUESTO_DUENO,
    PUESTO_ENCARGADO,
    PUESTO_CAJERO,
    PUESTO_REPOSITOR,
    PUESTO_CONSULTA_PRODUCTOS,
]

PERMISOS_POR_PUESTO = {
    PUESTO_DUENO: {
        "usar_caja": True,
        "ver_productos": True,
        "gestionar_productos": True,
        "ver_ventas": True,
        "ver_registros": True,
        "ver_deudas": True,
        "ver_debito": True,
        "ver_clientes": True,
        "gestionar_empleados": True,
        "ver_reportes": True,
    },
    PUESTO_ENCARGADO: {
        "usar_caja": True,
        "ver_productos": True,
        "gestionar_productos": True,
        "ver_ventas": True,
        "ver_registros": True,
        "ver_deudas": True,
        "ver_debito": True,
        "ver_clientes": True,
        "gestionar_empleados": False,
        "ver_reportes": True,
    },
    PUESTO_CAJERO: {
        "usar_caja": True,
        "ver_productos": True,
        "gestionar_productos": False,
        "ver_ventas": False,
        "ver_registros": False,
        "ver_deudas": False,
        "ver_debito": False,
        "ver_clientes": False,
        "gestionar_empleados": False,
        "ver_reportes": False,
    },
    PUESTO_REPOSITOR: {
        "usar_caja": False,
        "ver_productos": True,
        "gestionar_productos": True,
        "ver_ventas": False,
        "ver_registros": False,
        "ver_deudas": False,
        "ver_debito": False,
        "ver_clientes": False,
        "gestionar_empleados": False,
        "ver_reportes": False,
    },
    PUESTO_CONSULTA_PRODUCTOS: {
        "usar_caja": False,
        "ver_productos": True,
        "gestionar_productos": False,
        "ver_ventas": False,
        "ver_registros": False,
        "ver_deudas": False,
        "ver_debito": False,
        "ver_clientes": False,
        "gestionar_empleados": False,
        "ver_reportes": False,
    },
}

_ALIAS_PUESTOS = {
    "dueno": PUESTO_DUENO,
    "dueño": PUESTO_DUENO,
    "encargado": PUESTO_ENCARGADO,
    "cajero": PUESTO_CAJERO,
    "repositor": PUESTO_REPOSITOR,
    "consulta": PUESTO_CONSULTA_PRODUCTOS,
    "consulta productos": PUESTO_CONSULTA_PRODUCTOS,
    "solo lectura": PUESTO_CONSULTA_PRODUCTOS,
}


def _clave_puesto(puesto):
    texto = str(puesto or "").strip().lower()
    if not texto:
        return ""

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    return " ".join(texto.split())


def normalizar_puesto(puesto):
    clave = _clave_puesto(puesto)
    return _ALIAS_PUESTOS.get(clave, PUESTO_CAJERO)


def listar_puestos_disponibles():
    return list(PUESTOS_DISPONIBLES)


def obtener_permisos_por_puesto(puesto):
    puesto_normalizado = normalizar_puesto(puesto)
    return dict(PERMISOS_POR_PUESTO[puesto_normalizado])


def obtener_permisos_empleado(empleado):
    if not empleado:
        permisos_base = next(iter(PERMISOS_POR_PUESTO.values()))
        return {permiso: False for permiso in permisos_base}
    return obtener_permisos_por_puesto(empleado.get("puesto"))


def empleado_tiene_permiso(empleado, permiso):
    return bool(obtener_permisos_empleado(empleado).get(permiso, False))


def _normalizar_empleado(empleado):
    empleado_normalizado = dict(empleado)
    nombre = str(empleado_normalizado.get("nombre", "")).strip()
    correo = str(empleado_normalizado.get("correo", "")).strip()

    empleado_normalizado["id"] = str(empleado_normalizado.get("id", "")).strip()
    empleado_normalizado["nombre"] = nombre
    empleado_normalizado["correo"] = correo
    empleado_normalizado["usuario"] = str(
        empleado_normalizado.get("usuario") or correo or nombre
    ).strip()
    empleado_normalizado["puesto"] = normalizar_puesto(empleado_normalizado.get("puesto"))
    empleado_normalizado["activo"] = bool(empleado_normalizado.get("activo", False))

    return empleado_normalizado


def cargar_empleados():
    if not os.path.exists(RUTA_EMPLEADOS):
        return []

    with open(RUTA_EMPLEADOS, "r", encoding="utf-8") as archivo:
        try:
            empleados = json.load(archivo)
        except json.JSONDecodeError:
            log("Error: empleados.json está mal formado.")
            return []

    if not isinstance(empleados, list):
        return []

    return [_normalizar_empleado(empleado) for empleado in empleados]


def guardar_empleados(empleados):
    asegurar_directorio(RUTA_EMPLEADOS)
    empleados_normalizados = [_normalizar_empleado(empleado) for empleado in empleados]
    with open(RUTA_EMPLEADOS, "w", encoding="utf-8") as archivo:
        json.dump(empleados_normalizados, archivo, ensure_ascii=False, indent=4)


def agregar_empleado(nuevo_empleado):
    nuevo_empleado = _normalizar_empleado(nuevo_empleado)
    empleados = cargar_empleados()
    if any(empleado["id"] == nuevo_empleado["id"] for empleado in empleados):
        log(f"Aviso: ya existe un empleado con ID {nuevo_empleado['id']}.")
        return False

    empleados.append(nuevo_empleado)
    guardar_empleados(empleados)
    log(f"Empleado agregado: {nuevo_empleado['nombre']} - ID: {nuevo_empleado['id']}")
    return True


def eliminar_empleado(empleado_id):
    empleado_id = str(empleado_id)
    empleados = cargar_empleados()
    for i, empleado in enumerate(empleados):
        if empleado["id"] == empleado_id:
            del empleados[i]
            guardar_empleados(empleados)
            return True
    return False


def actualizar_empleado(empleado_id, nuevos_datos):
    empleado_id = str(empleado_id)
    empleados = cargar_empleados()
    for empleado in empleados:
        if empleado["id"] == empleado_id:
            empleado.update(nuevos_datos)
            guardar_empleados(empleados)
            return True
    return False


def buscar_empleado(empleado_id):
    empleado_id = str(empleado_id)
    empleados = cargar_empleados()
    for empleado in empleados:
        if empleado["id"] == empleado_id:
            return empleado

    log(f"Error: empleado con ID {empleado_id} no encontrado.")
    return None


def obtener_empleado_activo():
    empleados = cargar_empleados()
    for empleado in empleados:
        if empleado.get("activo"):
            return empleado
    return None
