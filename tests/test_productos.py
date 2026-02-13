import sys
import os

# Agrega la raíz del proyecto a sys.path para que funcione el import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import productos

def main():
    print("🔍 Probando restar_stock...\n")

    # Prueba 1: Producto existe y hay suficiente stock
    print("➡️ Caso 1: stock suficiente")
    productos.restar_stock("1", 1)

    # Prueba 2: Producto existe pero stock insuficiente
    print("\n➡️ Caso 2: stock insuficiente")
    productos.restar_stock("1", 999)

    # Prueba 3: Producto no existe
    print("\n➡️ Caso 3: producto inexistente")
    productos.restar_stock("999", 1)

    print("Probando agregar_producto...\n")
    # Prueba 1: Producto nuevo
    print("➡️ Caso 1: producto nuevo")
    nuevo_producto = {"id": "4","nombre": "Producto 4","precio": 100.0,"stock_actual": 10,"stock_minimo": 2}
    productos.agregar_producto(nuevo_producto)

    # Prueba 2: Producto existente
    print("\n➡️ Caso 2: producto existente")
    producto_existente = {"id": "1","nombre": "Producto 1","precio": 50.0,"stock_actual": 5,"stock_minimo": 2}
    productos.agregar_producto(producto_existente)

    # Prueba 3: Stock o precio negativos
    print("\n➡️ Caso 3: stock o precio negativos")
    producto_invalido = {"id": "5","nombre": "Producto 5","precio": -10.0,"stock_actual": -5,"stock_minimo": 5}
    productos.agregar_producto(producto_invalido)

    print("Probando eliminar_producto...\n")
    # Prueba 1: Producto existe
    print("➡️ Caso 1: producto existe")
    productos.eliminar_producto("1")

    # Prueba 2: Producto no existe
    print("\n➡️ Caso 2: producto no existe")
    productos.eliminar_producto("999")

    print("Probando actualizar_producto...\n")
    # Prueba 1: Producto existe y stock suficiente
    print("➡️ Caso 1: producto existe y stock suficiente")
    productos.actualizar_producto("2", {"stock_actual": 10})

    # Prueba 2: Producto no existe
    print("\n➡️ Caso 2: producto no existe")
    productos.actualizar_producto("999", {"stock_actual": 10})

    print("Probando buscar_producto...\n")
    # Prueba 1: Producto existe
    print("➡️ Caso 1: producto existe")
    producto = productos.buscar_producto("2")
    if producto:
        print(f"Producto encontrado: {producto['nombre']} - ID: {producto['id']}")
    else:
        print("❌ Producto no encontrado.")

    # Prueba 2: Producto no existe
    print("\n➡️ Caso 2: producto no existe")
    producto = productos.buscar_producto("999")
    if producto:
        print(f"Producto encontrado: {producto['nombre']} - ID: {producto['id']}")
    else:
        print("❌ Producto no encontrado.")

if __name__ == "__main__":
    main()
