import sys
import os

# Agrega la raíz del proyecto a sys.path para que funcione el import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import ventas

def main():
    print("🧪 Probando registrar_venta...\n")

    productos_vendidos = [
        {"id": "1", "cantidad": 1},
        {"id": "2", "cantidad": 2}
    ]

    print("➡️ Caso 1: venta en efectivo sin cliente")
    ventas.registrar_venta(productos_vendidos, "efectivo")

    print("\n➡️ Caso 2: venta en efectivo con cliente")
    ventas.registrar_venta(productos_vendidos, "efectivo", cliente_dni="12345678")

    print("\n➡️ Caso 3: venta por débito con cliente")
    ventas.registrar_venta(productos_vendidos, "debito", cliente_dni="12345678")

    print("\n➡️ Caso 4: venta fiada (deuda) con cliente")
    ventas.registrar_venta(productos_vendidos, "deuda", cliente_dni="12345678")

    print("\n➡️ Caso 5: venta con forma de pago inválida")
    ventas.registrar_venta(productos_vendidos, "bitcoin", cliente_dni="12345678")

    print("\n➡️ Caso 6: venta por débito sin cliente (debe fallar)")
    ventas.registrar_venta(productos_vendidos, "debito")

    print("\n➡️ Caso 7: venta fiada sin cliente (debe fallar)")
    ventas.registrar_venta(productos_vendidos, "deuda")

    print("\n➡️ Caso 8: venta con producto inexistente")
    productos_invalidos = [{"id": "999", "cantidad": 1}]
    ventas.registrar_venta(productos_invalidos, "efectivo")

    print("\n➡️ Caso 9: sin empleado activo (debe fallar)")
    print("⚠️ Para probar este caso, desactiva manualmente todos los empleados en empleados.json")
    ventas.registrar_venta(productos_vendidos, "efectivo", cliente_dni="12345678")


if __name__ == "__main__":
    main()
