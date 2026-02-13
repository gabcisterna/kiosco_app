import sys
import os

# Agrega la raíz del proyecto a sys.path para que funcione el import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import debito

def main():
    print("🧪 Probando registrar_pago_debito...\n")

    # Caso 1: Pago válido
    print("➡️ Caso 1: pago válido")
    debito.registrar_pago_debito("12345678", 200)

    # Caso 2: Otro pago válido para el mismo cliente
    print("\n➡️ Caso 2: otro pago válido para el mismo cliente")
    debito.registrar_pago_debito("12345678", 100)

    # Caso 3: Pago para un cliente nuevo
    print("\n➡️ Caso 3: pago válido para nuevo cliente")
    debito.registrar_pago_debito("87654321", 300)

    # Caso 4: Monto inválido (0 o negativo)
    print("\n➡️ Caso 4: monto inválido")
    debito.registrar_pago_debito("12345678", -50)

    print("\n📄 Probando listar_pagos_debito...\n")
    pagos = debito.listar_pagos_debito()
    for cliente in pagos:
        print(f"👤 Cliente DNI: {cliente['dni']}, Total pagado: ${cliente['total_pagado']:.2f}")

    print("\n📋 Probando listar_registro_debitos...\n")
    registro = debito.listar_registro_debitos()
    for movimiento in registro:
        print(f"🗓️ {movimiento['fecha']} - DNI: {movimiento['dni']} - Monto: ${movimiento['monto']:.2f}")

if __name__ == "__main__":
    main()
