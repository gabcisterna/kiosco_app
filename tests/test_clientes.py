import sys
import os

# Agrega la raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import clientes

def main():
    print("🔍 Probando agregar_cliente...\n")

    # Caso 1: cliente nuevo
    print("➡️ Caso 1: cliente nuevo")
    nuevo_cliente = {"dni": "12345678", "nombre": "Juan Pérez", "deuda": 0.0}
    clientes.agregar_cliente(nuevo_cliente)

    # Caso 2: cliente ya existente
    print("\n➡️ Caso 2: cliente existente")
    clientes.agregar_cliente(nuevo_cliente)

    print("\n🔍 Probando eliminar_cliente...\n")

    # Caso 1: cliente existe
    print("➡️ Caso 1: cliente existe")
    clientes.eliminar_cliente("12345678")

    # Caso 2: cliente no existe
    print("\n➡️ Caso 2: cliente no existe")
    clientes.eliminar_cliente("99999999")

    print("\n🔍 Probando actualizar_cliente...\n")

    # Agregamos cliente otra vez para actualizarlo
    clientes.agregar_cliente({"dni": "87654321", "nombre": "Ana Gómez", "deuda": 50.0})

    # Caso 1: cliente existe
    print("➡️ Caso 1: cliente existe")
    clientes.actualizar_cliente("87654321", {"deuda": 25.0})

    # Caso 2: cliente no existe
    print("\n➡️ Caso 2: cliente no existe")
    clientes.actualizar_cliente("99999999", {"deuda": 0.0})

    print("\n🔍 Probando buscar_cliente...\n")

    # Caso 1: cliente existe
    print("➡️ Caso 1: cliente existe")
    cliente = clientes.buscar_cliente("87654321")
    if cliente:
        print(f"Cliente encontrado: {cliente['nombre']} - Deuda: ${cliente['deuda']:.2f}")
    else:
        print("❌ Cliente no encontrado.")

    # Caso 2: cliente no existe
    print("\n➡️ Caso 2: cliente no existe")
    cliente = clientes.buscar_cliente("99999999")
    if cliente:
        print(f"Cliente encontrado: {cliente['nombre']} - Deuda: ${cliente['deuda']:.2f}")
    else:
        print("❌ Cliente no encontrado.")

if __name__ == "__main__":
    main()
