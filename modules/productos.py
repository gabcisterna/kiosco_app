import json
import os

RUTA_PRODUCTOS = os.path.join("data", "productos.json")
RUTA_PRODUCTOS_BAJOS = os.path.join("data", "productos_bajos.json")


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


def cargar_productos_bajos():
    """Carga y devuelve la lista de productos desde productos.json"""
    if not os.path.exists(RUTA_PRODUCTOS):
        return []  # Si no existe, devolvemos lista vacía
    
    with open(RUTA_PRODUCTOS_BAJOS, "r", encoding="utf-8") as archivo:
        try:
            productos = json.load(archivo)
            return productos
        except json.JSONDecodeError:
            print("⚠️ Error: productos.json está mal formado.")
            return []


def guardar_productos_bajos(productos):
    """Guarda la lista de productos actualizada en productos.json"""
    with open(RUTA_PRODUCTOS_BAJOS, "w", encoding="utf-8") as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=4)


def restar_stock(producto_id, cantidad):
    """Resta stock de un producto dado por su ID"""
    productos = cargar_productos()
    for producto in productos:
        if producto["id"] == str(producto_id):
            if producto["stock_actual"] >= cantidad:
                producto["stock_actual"] -= cantidad
                guardar_productos(productos)

                # Verificar si el stock actual es menor o igual al mínimo
                # y si es así, agregarlo a la lista de productos bajos
                if producto["stock_actual"] <= producto["stock_minimo"]:
                    # Cargar productos con stock bajo
                    productos_bajos = cargar_productos_bajos()
                    # Verificar si el producto ya está en la lista
                    producto_existente = next((p for p in productos_bajos if p["id"] == producto["id"]), None)
                    if producto_existente is None:
                        # No estaba, lo agregamos
                        productos_bajos.append(producto)
                        guardar_productos_bajos(productos_bajos)
                    else:
                        # Ya estaba, actualizamos su stock
                        producto_existente["stock_actual"] = producto["stock_actual"]
                        # Guardamos la lista actualizada
                        guardar_productos_bajos(productos_bajos)



                #Se puede eliminar despues de la UI
                print(f"✅ Stock actualizado: {producto['nombre']} - Nuevo stock: {producto['stock_actual']}")



                return True
            else:

                #"Se puede eliminar despues de la UI"
                print(f"⚠️ No hay suficiente stock de {producto['nombre']}. Stock actual: {producto['stock_actual']}")


                return False
            

    #"Se puede eliminar despues de la UI"
    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return False





def agregar_producto(nuevo_producto):
    """Agrega un nuevo producto a la lista de productos"""
    productos = cargar_productos()
    if any(p["id"] == nuevo_producto["id"] for p in productos):

        #"Se puede eliminar despues de la UI"
        print(f"⚠️ Ya existe un producto con ID {nuevo_producto['id']}.")


        return False
    if nuevo_producto["stock_actual"] < 0 or nuevo_producto["precio"] < 0:

        #"Se puede eliminar despues de la UI"
        print("⚠️ Stock y precio deben ser valores positivos.")


        return False
    
    productos.append(nuevo_producto)
    guardar_productos(productos)

    #"Se puede eliminar despues de la UI"
    print(f"✅ Producto agregado: {nuevo_producto['nombre']} - ID: {nuevo_producto['id']}")


    return True


def eliminar_producto(producto_id):
    """Elimina un producto de la lista dado su ID"""
    productos = cargar_productos()
    for i, producto in enumerate(productos):
        if int(producto["id"]) == int(producto_id):
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
        if int(producto["id"]) == int(producto_id):
            nuevos_datos.pop("id", None)
            producto.update(nuevos_datos)
            guardar_productos(productos)

            #"Se puede eliminar despues de la UI"
            print(f"✅ Producto actualizado: {producto['nombre']} - ID: {producto['id']}")
            return True
        
    #"Se puede eliminar despues de la UI"
    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return False


def buscar_producto(producto_id):
    """Busca un producto por su ID y devuelve sus datos"""
    productos = cargar_productos()
    for producto in productos:
        if int(producto["id"]) == int(producto_id):
            return producto

    print(f"❌ Producto con ID {producto_id} no encontrado.")
    return None



def listar_productos():
    """
    Lista todos los productos disponibles en el sistema.
    """
    productos = cargar_productos()
    if not productos:
        print("❌ No hay productos registrados.")
        return []

    print("📦 Productos disponibles:")
    for producto in productos:
        print(f"ID: {producto['id']}, Nombre: {producto['nombre']}, Precio: ${producto['precio']:.2f}, Stock: {producto['stock_actual']}, Stock_mínimo: {producto['stock_minimo']}")

    return productos

def listar_productos_con_stock_bajo():
    """Devuelve lista de productos con stock menor al mínimo"""
    productos = cargar_productos_bajos()
    return productos