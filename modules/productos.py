import json
import os

from modules.console import log
from modules.rutas import asegurar_directorio, ruta_datos

RUTA_PRODUCTOS = ruta_datos("productos.json")
RUTA_PRODUCTOS_BAJOS = ruta_datos("productos_bajos.json")

TIPO_VENTA_UNIDAD = "unidad"
TIPO_VENTA_KILO = "kilo"
DECIMALES_KILO = 3
EPSILON_CANTIDAD = 10 ** (-DECIMALES_KILO)


def _float_local(valor, default=0.0):
    try:
        return float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        return default


def normalizar_tipo_venta(valor):
    texto = str(valor or "").strip().lower()
    if texto in {TIPO_VENTA_KILO, "kg", "peso", "por kilo", "kilos"}:
        return TIPO_VENTA_KILO
    return TIPO_VENTA_UNIDAD


def producto_se_vende_por_kilo(producto=None, tipo_venta=None):
    tipo = normalizar_tipo_venta(tipo_venta or (producto or {}).get("tipo_venta"))
    return tipo == TIPO_VENTA_KILO


def obtener_unidad_medida(producto=None, tipo_venta=None):
    return "kg" if producto_se_vende_por_kilo(producto=producto, tipo_venta=tipo_venta) else "u"


def normalizar_cantidad_guardada(valor, producto=None, tipo_venta=None):
    cantidad = _float_local(valor, default=0.0)
    if producto_se_vende_por_kilo(producto=producto, tipo_venta=tipo_venta):
        cantidad = round(cantidad, DECIMALES_KILO)
        return 0.0 if abs(cantidad) < EPSILON_CANTIDAD else cantidad
    return int(round(cantidad))


def parsear_cantidad_para_producto(valor, producto=None, tipo_venta=None):
    texto = str(valor or "").strip().replace(",", ".")
    if not texto:
        raise ValueError("Ingresa una cantidad.")

    try:
        cantidad = float(texto)
    except ValueError as exc:
        raise ValueError("La cantidad debe ser numerica.") from exc

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor a cero.")

    if producto_se_vende_por_kilo(producto=producto, tipo_venta=tipo_venta):
        cantidad = round(cantidad, DECIMALES_KILO)
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        return cantidad

    if not cantidad.is_integer():
        raise ValueError("Este producto se vende por unidad. Usa un numero entero.")

    return int(cantidad)


def formatear_cantidad(cantidad, producto=None, tipo_venta=None, con_unidad=False):
    if producto_se_vende_por_kilo(producto=producto, tipo_venta=tipo_venta):
        texto = f"{_float_local(cantidad):.{DECIMALES_KILO}f}".rstrip("0").rstrip(".")
        if not texto:
            texto = "0"
    else:
        texto = str(int(round(_float_local(cantidad))))

    if con_unidad:
        return f"{texto} {obtener_unidad_medida(producto=producto, tipo_venta=tipo_venta)}"
    return texto


def describir_precio_producto(producto):
    sufijo = " / kg" if producto_se_vende_por_kilo(producto=producto) else " c/u"
    return f"${_float_local(producto.get('precio', 0)):.2f}{sufijo}"


def normalizar_producto(producto):
    if not isinstance(producto, dict):
        return None

    tipo_venta = normalizar_tipo_venta(producto.get("tipo_venta"))
    return {
        **producto,
        "id": int(producto["id"]),
        "nombre": str(producto.get("nombre", "")).strip(),
        "precio": round(_float_local(producto.get("precio", 0)), 2),
        "stock_actual": normalizar_cantidad_guardada(producto.get("stock_actual", 0), tipo_venta=tipo_venta),
        "stock_minimo": normalizar_cantidad_guardada(producto.get("stock_minimo", 0), tipo_venta=tipo_venta),
        "tipo_venta": tipo_venta,
    }


def _leer_lista_productos(ruta):
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as archivo:
        try:
            productos = json.load(archivo)
        except json.JSONDecodeError:
            log(f"Error: {os.path.basename(ruta)} esta mal formado.")
            return []

    if not isinstance(productos, list):
        return []

    normalizados = [normalizar_producto(producto) for producto in productos if isinstance(producto, dict)]
    normalizados = [producto for producto in normalizados if producto is not None]

    if normalizados != productos:
        _guardar_lista_productos(ruta, normalizados)

    return normalizados


def _guardar_lista_productos(ruta, productos):
    productos_normalizados = []
    for producto in productos:
        normalizado = normalizar_producto(producto)
        if normalizado is not None:
            productos_normalizados.append(normalizado)

    asegurar_directorio(ruta)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(productos_normalizados, archivo, ensure_ascii=False, indent=4)


def cargar_productos():
    return _leer_lista_productos(RUTA_PRODUCTOS)


def guardar_productos(productos):
    _guardar_lista_productos(RUTA_PRODUCTOS, productos)


def cargar_productos_bajos():
    return _leer_lista_productos(RUTA_PRODUCTOS_BAJOS)


def guardar_productos_bajos(productos):
    _guardar_lista_productos(RUTA_PRODUCTOS_BAJOS, productos)


def _quitar_de_productos_bajos(producto_id):
    productos_bajos = [
        producto
        for producto in cargar_productos_bajos()
        if str(producto["id"]) != str(producto_id)
    ]
    guardar_productos_bajos(productos_bajos)


def _recalcular_deudas_pendientes():
    from modules.deudas import recalcular_deudas_pendientes

    recalcular_deudas_pendientes()


def restar_stock(producto_id, cantidad):
    productos = cargar_productos()
    for producto in productos:
        if int(producto["id"]) != int(producto_id):
            continue

        cantidad_normalizada = parsear_cantidad_para_producto(cantidad, producto=producto)
        stock_actual = _float_local(producto.get("stock_actual", 0))
        if stock_actual + EPSILON_CANTIDAD < cantidad_normalizada:
            log(
                f"Aviso: no hay suficiente stock de {producto['nombre']}. "
                f"Stock actual: {formatear_cantidad(stock_actual, producto=producto, con_unidad=True)}"
            )
            return False

        producto["stock_actual"] = normalizar_cantidad_guardada(
            stock_actual - cantidad_normalizada,
            producto=producto,
        )
        guardar_productos(productos)
        _sincronizar_productos_bajos(producto)

        log(
            f"Stock actualizado: {producto['nombre']} - Nuevo stock: "
            f"{formatear_cantidad(producto['stock_actual'], producto=producto, con_unidad=True)}"
        )
        return True

    log(f"Error: producto con ID {producto_id} no encontrado.")
    return False


def agregar_producto(nuevo_producto):
    producto_normalizado = normalizar_producto(nuevo_producto)
    productos = cargar_productos()

    if any(int(p["id"]) == int(producto_normalizado["id"]) for p in productos):
        log(f"Aviso: ya existe un producto con ID {producto_normalizado['id']}.")
        return False

    if producto_normalizado["stock_actual"] < 0 or producto_normalizado["precio"] < 0:
        log("Aviso: stock y precio deben ser valores positivos.")
        return False

    if producto_normalizado["stock_minimo"] < 0:
        log("Aviso: el stock minimo debe ser un valor positivo.")
        return False

    productos.append(producto_normalizado)
    guardar_productos(productos)

    if producto_normalizado.get("stock_actual", 0) <= producto_normalizado.get("stock_minimo", 0):
        _sincronizar_productos_bajos(producto_normalizado)

    log(f"Producto agregado: {producto_normalizado['nombre']} - ID: {producto_normalizado['id']}")
    return True


def eliminar_producto(producto_id):
    productos = cargar_productos()
    for i, producto in enumerate(productos):
        if int(producto["id"]) == int(producto_id):
            del productos[i]
            guardar_productos(productos)
            _quitar_de_productos_bajos(producto_id)

            log(f"Producto eliminado: {producto['nombre']} - ID: {producto['id']}")
            return True

    log(f"Error: producto con ID {producto_id} no encontrado.")
    return False


def _sincronizar_productos_bajos(producto_actualizado):
    producto_actualizado = normalizar_producto(producto_actualizado)
    productos_bajos = cargar_productos_bajos()
    stock_actual = _float_local(producto_actualizado.get("stock_actual", 0))
    stock_minimo = _float_local(producto_actualizado.get("stock_minimo", 0))
    producto_id = str(producto_actualizado["id"])

    if stock_actual > stock_minimo + EPSILON_CANTIDAD:
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
    for indice, producto in enumerate(productos):
        if int(producto["id"]) != int(producto_id):
            continue

        producto_anterior = normalizar_producto(producto)
        precio_anterior = float(producto.get("precio", 0))
        nuevos_datos = dict(nuevos_datos)
        nuevo_id = nuevos_datos.get("id", producto_id)

        try:
            nuevo_id = int(nuevo_id)
        except (TypeError, ValueError):
            log("Error: el nuevo ID del producto no es valido.")
            return False

        if nuevo_id != int(producto_id) and any(int(p["id"]) == nuevo_id for p in productos):
            log(f"Aviso: ya existe un producto con ID {nuevo_id}.")
            return False

        producto_actualizado = {**producto, **nuevos_datos, "id": nuevo_id}
        producto_normalizado = normalizar_producto(producto_actualizado)
        productos[indice] = producto_normalizado
        guardar_productos(productos)

        if int(producto_anterior["id"]) != int(producto_normalizado["id"]):
            _quitar_de_productos_bajos(producto_anterior["id"])

        _sincronizar_productos_bajos(producto_normalizado)

        if "precio" in nuevos_datos and float(producto_normalizado.get("precio", 0)) != precio_anterior:
            _recalcular_deudas_pendientes()

        log(f"Producto actualizado: {producto_normalizado['nombre']} - ID: {producto_normalizado['id']}")
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
            f"ID: {producto['id']}, Nombre: {producto['nombre']}, "
            f"Precio: {describir_precio_producto(producto)}, "
            f"Stock: {formatear_cantidad(producto['stock_actual'], producto=producto, con_unidad=True)}, "
            f"Stock minimo: {formatear_cantidad(producto['stock_minimo'], producto=producto, con_unidad=True)}"
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
