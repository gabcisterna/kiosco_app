import json
import os
import unicodedata

from modules.console import log
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_CLIENTES = ruta_datos("clientes.json")
PREFIJO_REFERENCIA_CLIENTE = "CLI-"


def _normalizar_texto_busqueda(texto):
    texto = str(texto or "").strip().lower()
    if not texto:
        return ""

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")
    return " ".join(texto.split())


def _normalizar_cliente(cliente):
    cliente_normalizado = dict(cliente)
    cliente_normalizado["nombre"] = str(cliente_normalizado.get("nombre", "")).strip()
    cliente_normalizado["dni"] = str(cliente_normalizado.get("dni", "")).strip()
    cliente_normalizado["deuda"] = round(float(cliente_normalizado.get("deuda", 0) or 0), 2)
    return cliente_normalizado


def cargar_clientes():
    if not os.path.exists(RUTA_CLIENTES):
        return []

    with open(RUTA_CLIENTES, "r", encoding="utf-8") as archivo:
        try:
            clientes = json.load(archivo)
        except json.JSONDecodeError:
            log("Error: clientes.json está mal formado.")
            return []

    if not isinstance(clientes, list):
        return []

    clientes_normalizados = [_normalizar_cliente(cliente) for cliente in clientes]
    if clientes != clientes_normalizados:
        guardar_clientes(clientes_normalizados)
    return clientes_normalizados


def guardar_clientes(clientes):
    asegurar_directorio(RUTA_CLIENTES)
    clientes_normalizados = [_normalizar_cliente(cliente) for cliente in clientes]
    with open(RUTA_CLIENTES, "w", encoding="utf-8") as archivo:
        json.dump(clientes_normalizados, archivo, ensure_ascii=False, indent=4)


def generar_referencia_cliente(nombre=None):
    clientes = cargar_clientes()
    mayor = 0
    for cliente in clientes:
        dni = str(cliente.get("dni", ""))
        if dni.startswith(PREFIJO_REFERENCIA_CLIENTE):
            sufijo = dni[len(PREFIJO_REFERENCIA_CLIENTE) :]
            if sufijo.isdigit():
                mayor = max(mayor, int(sufijo))

    siguiente = mayor + 1
    return f"{PREFIJO_REFERENCIA_CLIENTE}{siguiente:04d}"


def agregar_cliente(cliente):
    cliente = _normalizar_cliente(cliente)
    clientes = cargar_clientes()

    if not cliente["nombre"]:
        log("Aviso: el nombre del cliente es obligatorio.")
        return False

    if not cliente["dni"]:
        cliente["dni"] = generar_referencia_cliente(cliente["nombre"])

    if any(str(c.get("dni", "")) == cliente["dni"] for c in clientes):
        log(f"Aviso: ya existe un cliente con DNI/referencia {cliente['dni']}.")
        return False

    clientes.append(cliente)
    guardar_clientes(clientes)
    return True


def eliminar_cliente(dni):
    dni = str(dni).strip()
    clientes = cargar_clientes()
    for i, cliente in enumerate(clientes):
        if cliente["dni"] == dni:
            del clientes[i]
            guardar_clientes(clientes)
            log(f"Cliente eliminado: {cliente['nombre']} - DNI/referencia: {cliente['dni']}")
            return True

    log(f"Error: cliente con DNI/referencia {dni} no encontrado.")
    return False


def actualizar_cliente(dni, nuevos_datos):
    dni = str(dni).strip()
    clientes = cargar_clientes()
    for cliente in clientes:
        if cliente["dni"] == dni:
            cliente.update(nuevos_datos)
            cliente_actualizado = _normalizar_cliente(cliente)
            cliente.clear()
            cliente.update(cliente_actualizado)
            guardar_clientes(clientes)
            log(f"Cliente actualizado: {cliente['nombre']} - DNI/referencia: {cliente['dni']}")
            return True

    log(f"Error: cliente con DNI/referencia {dni} no encontrado.")
    return False


def buscar_cliente(dni):
    dni = str(dni or "").strip()
    if not dni:
        return None

    clientes = cargar_clientes()
    for cliente in clientes:
        if cliente.get("dni") == dni:
            return cliente
    return None


def buscar_cliente_por_nombre(nombre):
    nombre_normalizado = _normalizar_texto_busqueda(nombre)
    if not nombre_normalizado:
        return None

    clientes = cargar_clientes()
    for cliente in clientes:
        if _normalizar_texto_busqueda(cliente.get("nombre")) == nombre_normalizado:
            return cliente
    return None


def buscar_clientes_por_texto(texto):
    texto_normalizado = _normalizar_texto_busqueda(texto)
    clientes = cargar_clientes()
    if not texto_normalizado:
        return clientes

    clientes_filtrados = []
    for cliente in clientes:
        dni = str(cliente.get("dni", ""))
        nombre = str(cliente.get("nombre", ""))
        if texto_normalizado in _normalizar_texto_busqueda(dni) or texto_normalizado in _normalizar_texto_busqueda(nombre):
            clientes_filtrados.append(cliente)

    def clave_orden(cliente):
        dni = str(cliente.get("dni", ""))
        nombre = str(cliente.get("nombre", ""))
        dni_normalizado = _normalizar_texto_busqueda(dni)
        nombre_normalizado = _normalizar_texto_busqueda(nombre)
        return (
            dni_normalizado != texto_normalizado,
            nombre_normalizado != texto_normalizado,
            not dni_normalizado.startswith(texto_normalizado),
            not nombre_normalizado.startswith(texto_normalizado),
            nombre_normalizado,
            dni_normalizado,
        )

    clientes_filtrados.sort(key=clave_orden)
    return clientes_filtrados


def resolver_cliente_para_venta(dni=None, nombre=None, crear_si_no_existe=False):
    dni = str(dni or "").strip()
    nombre = str(nombre or "").strip()

    if dni:
        cliente = buscar_cliente(dni)
        if cliente:
            if nombre and cliente.get("nombre") != nombre:
                actualizar_cliente(cliente["dni"], {"nombre": nombre})
                cliente = buscar_cliente(cliente["dni"])
            return cliente

    if nombre:
        cliente = buscar_cliente_por_nombre(nombre)
        if cliente:
            return cliente

    if not crear_si_no_existe:
        return None

    referencia = dni or generar_referencia_cliente(nombre)
    cliente_nuevo = {
        "dni": referencia,
        "nombre": nombre or f"Cliente {referencia}",
        "deuda": 0.0,
    }

    if not agregar_cliente(cliente_nuevo):
        return buscar_cliente(referencia) or buscar_cliente_por_nombre(cliente_nuevo["nombre"])

    return buscar_cliente(referencia)
