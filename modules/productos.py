import json
import os

from modules.console import log
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_PRODUCTOS = ruta_datos("productos.json")
RUTA_PRODUCTOS_BAJOS = ruta_datos("productos_bajos.json")


def cargar_productos():
    if not os.path.exists(RUTA_PRODUCTOS):
        return []

    with open(RUTA_PRODUCTOS, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            log("Error: productos.json está mal formado.")
            return []


def guardar_productos(productos):
    asegurar_directorio(RUTA_PRODUCTOS)
    with open(RUTA_PRODUCTOS, "w", encoding="utf-8") as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=4)


def cargar_productos_bajos():
    if not os.path.exists(RUTA_PRODUCTOS_BAJOS):
        return []

    with open(RUTA_PRODUCTOS_BAJOS, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            log("Error: productos_bajos.json está mal formado.")
            return []


def guardar_productos_bajos(productos):
    asegurar_directorio(RUTA_PRODUCTOS_BAJOS)
    with open(RUTA_PRODUCTOS_BAJOS, "w", encoding="utf-8") as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=4)


def _recalcular_deudas_pendientes():
    from modules.deudas import recalcular_deudas_pendientes

    recalcular_deudas_pendientes()


def restar_stock(producto_id, cantidad):
    productos = cargar_productos()
    for producto in productos:
        if producto["id"] == producto_id:
            if producto["stock_actual"] >= cantidad:
                producto["stock_actual"] -= cantidad
                guardar_productos(productos)

                if producto["stock_actual"] <= producto["stock_minimo"]:
                    productos_bajos = cargar_productos_bajos()
                    producto_existente = next((p for p in productos_bajos if p["id"] == producto["id"]), None)
                    if producto_existente is None:
                        productos_bajos.append(producto)
                    else:
                        producto_existente["stock_actual"] = producto["stock_actual"]
                    guardar_productos_bajos(productos_bajos)

                log(f"Stock actualizado: {producto['nombre']} - Nuevo stock: {producto['stock_actual']}")
                return True

            log(
                f"Aviso: no hay suficiente stock de {producto['nombre']}. "
                f"Stock actual: {producto['stock_actual']}"
            )
            return False

    log(f"Error: producto con ID {producto_id} no encontrado.")
    return False


def agregar_producto(nuevo_producto):
    productos = cargar_productos()
    if any(p["id"] == nuevo_producto["id"] for p in productos):
        log(f"Aviso: ya existe un producto con ID {nuevo_producto['id']}.")
        return False

    if nuevo_producto["stock_actual"] < 0 or nuevo_producto["precio"] < 0:
        log("Aviso: stock y precio deben ser valores positivos.")
        return False

    productos.append(nuevo_producto)
    guardar_productos(productos)

    if nuevo_producto.get("stock_actual", 0) <= nuevo_producto.get("stock_minimo", 0):
        _sincronizar_productos_bajos(nuevo_producto)

    log(f"Producto agregado: {nuevo_producto['nombre']} - ID: {nuevo_producto['id']}")
    return True


def eliminar_producto(producto_id):
    productos = cargar_productos()
    for i, producto in enumerate(productos):
        if int(producto["id"]) == int(producto_id):
            del productos[i]
            guardar_productos(productos)

            productos_bajos = cargar_productos_bajos()
            productos_bajos = [p for p in productos_bajos if str(p["id"]) != str(producto_id)]
            guardar_productos_bajos(productos_bajos)

            log(f"Producto eliminado: {producto['nombre']} - ID: {producto['id']}")
            return True

    log(f"Error: producto con ID {producto_id} no encontrado.")
    return False


def _sincronizar_productos_bajos(producto_actualizado):
    productos_bajos = cargar_productos_bajos()
    stock_actual = producto_actualizado.get("stock_actual", 0)
    stock_minimo = producto_actualizado.get("stock_minimo", 0)
    producto_id = str(producto_actualizado["id"])

    if stock_actual > stock_minimo:
        productos_bajos = [p for p in productos_bajos if str(p["id"]) != producto_id]
    else:
        existente = next((p for p in productos_bajos if str(p["id"]) == producto_id), None)
        if existente:
            existente.update(producto_actualizado)
        else:
            productos_bajos.append(producto_actualizado.copy())

    guardar_productos_bajos(productos_bajos)


def actualizar_producto(producto_id, nuevos_datos):
    productos = cargar_productos()
    for producto in productos:
        if int(producto["id"]) == int(producto_id):
            precio_anterior = float(producto.get("precio", 0))
            nuevos_datos = dict(nuevos_datos)
            nuevos_datos.pop("id", None)
            producto.update(nuevos_datos)
            guardar_productos(productos)

            _sincronizar_productos_bajos(producto)

            if "precio" in nuevos_datos and float(producto.get("precio", 0)) != precio_anterior:
                _recalcular_deudas_pendientes()

            log(f"Producto actualizado: {producto['nombre']} - ID: {producto['id']}")
            return True

    log(f"Error: producto con ID {producto_id} no encontrado.")
    return False


def buscar_producto(producto_id):
    productos = cargar_productos()
    for producto in productos:
        if int(producto["id"]) == int(producto_id):
            return producto
    return None


def listar_productos():
    productos = cargar_productos()
    if not productos:
        log("Error: no hay productos registrados.")
        return []

    log("Productos disponibles:")
    for producto in productos:
        log(
            f"ID: {producto['id']}, Nombre: {producto['nombre']}, Precio: ${producto['precio']:.2f}, "
            f"Stock: {producto['stock_actual']}, Stock mínimo: {producto['stock_minimo']}"
        )

    return productos


def listar_productos_con_stock_bajo():
    return cargar_productos_bajos()


def buscar_productos_por_nombre(parcial):
    productos = cargar_productos()
    return [p for p in productos if parcial.lower() in p["nombre"].lower()]


def buscar_productos_por_texto(texto):
    texto = str(texto).strip().lower()
    productos = cargar_productos()
    if not texto:
        return productos

    productos_filtrados = [
        producto
        for producto in productos
        if texto in str(producto.get("id", "")).lower()
        or texto in str(producto.get("nombre", "")).lower()
    ]

    def clave_orden(producto):
        producto_id = str(producto.get("id", ""))
        nombre = str(producto.get("nombre", "")).lower()
        return (
            producto_id != texto,
            nombre != texto,
            not producto_id.startswith(texto),
            not nombre.startswith(texto),
            nombre,
            producto_id,
        )

    productos_filtrados.sort(key=clave_orden)
    return productos_filtrados
