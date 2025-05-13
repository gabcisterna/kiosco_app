from modules.stock import (
    cargar_productos,
    agregar_producto,
    restar_stock,
    productos_con_stock_bajo
)

def probar_cargar():
    productos = cargar_productos()
    print("\n📦 Productos cargados:")
    for p in productos:
        print(f"ID {p['id']}: {p['nombre']} (${p['precio']}) - Stock: {p['stock_actual']} (mínimo {p['stock_minimo']})")

def probar_agregar():
    nuevo = {
        "id": 3,
        "nombre": "Coca-Cola 1.5L",
        "precio": 1200,
        "stock_actual": 10,
        "stock_minimo": 3
    }
    agregar_producto(nuevo)

def probar_restar():
    restar_stock(3, 2)

def probar_stock_bajo():
    bajos = productos_con_stock_bajo()
    print("\n🔻 Productos con stock bajo:")
    if bajos:
        for p in bajos:
            print(f"{p['nombre']} - Stock actual: {p['stock_actual']}, mínimo: {p['stock_minimo']}")
    else:
        print("Todo el stock está bien.")

if __name__ == "__main__":
    print("=== Prueba de módulo de stock ===")
    probar_cargar()
    probar_agregar()
    probar_restar()
    probar_stock_bajo()
