import sys
import os

# Agrega la raíz del proyecto a sys.path para que funcione el import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import deudas

def main():
    print("🧪 Probando registrar_deuda...\n")

    productos_comprados = [
        {"id": "1", "nombre": "Producto A", "cantidad": 2, "subtotal": 100},
        {"id": "2", "nombre": "Producto B", "cantidad": 1, "subtotal": 50}
    ]

    # Caso 1: Registrar deuda nueva
    print("➡️ Caso 1: registrar nueva deuda")
    deudas.registrar_deuda("12345678", productos_comprados)

    # Caso 2: Agregar más deuda al mismo cliente
    print("\n➡️ Caso 2: agregar más deuda al mismo cliente")
    deudas.registrar_deuda("12345678", productos_comprados)

    # Caso 3: Registrar deuda para otro cliente
    print("\n➡️ Caso 3: registrar deuda para nuevo cliente")
    deudas.registrar_deuda("87654321", productos_comprados)

    print("\n🧪 Probando pagar_deuda...\n")

    # Caso 4: Pagar parte de la deuda
    print("➡️ Caso 4: pago parcial")
    deudas.pagar_deuda("12345678", 50)

    # Caso 5: Pagar más de lo que debe (debe devolver vuelto)
    print("\n➡️ Caso 5: pago con vuelto")
    deudas.pagar_deuda("12345678", 500)

    # Caso 6: Pagar deuda inexistente
    print("\n➡️ Caso 6: pagar deuda inexistente")
    deudas.pagar_deuda("00000000", 100)

    # Caso 7: Pago con monto inválido
    print("\n➡️ Caso 7: monto de pago inválido")
    deudas.pagar_deuda("87654321", -20)

    print("\n🧪 Probando listar_deudas...\n")

    # Caso 8: Listar deudas actuales
    deudas_actuales = deudas.listar_deudas()
    for d in deudas_actuales:
        print(f"🧾 Cliente {d['dni']}, deuda: ${d['monto']:.2f}")

if __name__ == "__main__":
    main()
