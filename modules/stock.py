import json
import os

RUTA_PRODUCTOS = os.path.join("data", "productos.json")


def cargar_productos():
    """Carga y devuelve la lista de productos desde productos.json"""
    if not os.path.exists(RUTA_PRODUCTOS):
        return []  # Si no existe, devolvemos lista vacía
    
    with open(RUTA_PRODUCTOS, "r", encoding="utf-8") as archivo:
        try:
            productos = json.load(archivo)
            return productos
        except json.JSONDecodeError:
            print("⚠️ Error: productos.json está mal formado.")
            return []


def guardar_productos(productos):
    """Guarda la lista de productos actualizada en productos.json"""
    with open(RUTA_PRODUCTOS, "w", encoding="utf-8") as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=4)


def restar_stock(producto_id, cantidad):
    """Resta stock de un producto dado por su ID"""
    productos = cargar_productos()
    for producto in productos:
        if producto["id"] == producto_id:
            if producto["stock_actual"] >= cantidad:
                producto["stock_actual"] -= cantidad
                guardar_productos(productos)
                print(f"✅ Stock actualizado: {producto['nombre']} - Nuevo stock: {producto['stock_actual']}")
                return True
            else:
                print(f"⚠️ No hay suficiente stock de {producto['nombre']}. Stock actual: {producto['stock_actual']}")
                return False
    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return False



def productos_con_stock_bajo():
    """Devuelve lista de productos con stock menor al mínimo"""
    productos = cargar_productos()
    productos_bajos = [p for p in productos if p["stock_actual"] < p["stock_minimo"]]
    return productos_bajos


def agregar_producto(nuevo_producto):
    """Agrega un nuevo producto a la lista de productos"""
    productos = cargar_productos()
    if any(p["id"] == nuevo_producto["id"] for p in productos):
        print(f"⚠️ Ya existe un producto con ID {nuevo_producto['id']}.")
        return False
    if nuevo_producto["stock_actual"] < 0 or nuevo_producto["precio"] < 0:
        print("⚠️ Stock y precio deben ser valores positivos.")
        return False
    productos.append(nuevo_producto)
    guardar_productos(productos)
    print(f"✅ Producto agregado: {nuevo_producto['nombre']} - ID: {nuevo_producto['id']}")
    return True

def eliminar_producto(producto_id):
    """Elimina un producto de la lista dado su ID"""
    productos = cargar_productos()
    for i, producto in enumerate(productos):
        if producto["id"] == producto_id:
            del productos[i]
            guardar_productos(productos)
            print(f"✅ Producto eliminado: {producto['nombre']} - ID: {producto['id']}")
            return True
    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return False

def actualizar_producto(producto_id, nuevos_datos):
    """Actualiza los datos de un producto dado su ID"""
    productos = cargar_productos()
    for producto in productos:
        if producto["id"] == producto_id:
            nuevos_datos.pop("id", None)
            producto.update(nuevos_datos)
            guardar_productos(productos)
            print(f"✅ Producto actualizado: {producto['nombre']} - ID: {producto['id']}")
            return True
    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return False

def buscar_producto(producto_id):
    """Busca un producto por su ID y devuelve sus datos"""
    productos = cargar_productos()
    for producto in productos:
        if producto["id"] == producto_id:
            return producto
    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return None

def listar_productos():
    """Lista todos los productos disponibles"""
    productos = cargar_productos()
    if not productos:
        print("❌ No hay productos disponibles.")
        return
    print("\n📦 Productos disponibles:")
    for producto in productos:
        print(f"ID {producto['id']}: {producto['nombre']} (${producto['precio']}) - Stock: {producto['stock_actual']} (mínimo {producto['stock_minimo']})")