from modules.ventas import registrar_venta

if __name__ == "__main__":
    venta = [
        (1, 2),  # 2 unidades del producto con ID 1
        (3, 1)   # 1 unidad del producto con ID 3
    ]
    registrar_venta(venta, empleado="Gabriel")
