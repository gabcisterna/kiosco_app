import sys
import os

# Agrega la raíz del proyecto a sys.path para que funcione el import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import empleados

def main():
    print("👥 Probando funciones del módulo empleados...\n")

    # Datos iniciales
    empleados_prueba = [
        {"id": "e1", "nombre": "Juan Pérez", "cargo": "Vendedor", "usuario": "juan", "activo": False},
        {"id": "e2", "nombre": "Ana Gómez", "cargo": "Cajera", "usuario": "ana", "activo": False}
    ]
    empleados.guardar_empleados(empleados_prueba)

    print("📄 Probando listar_empleados:")
    empleados.listar_empleados()

    print("\n➕ Caso 1: agregar nuevo empleado")
    nuevo_empleado = {"id": "e3", "nombre": "Carlos López", "cargo": "Supervisor", "usuario": "carlos", "activo": False}
    empleados.agregar_empleado(nuevo_empleado)

    print("\n❌ Caso 2: intentar agregar empleado existente (e1)")
    empleados.agregar_empleado({"id": "e1", "nombre": "Duplicado", "cargo": "N/A", "usuario": "dup", "activo": False})

    print("\n🔍 Caso 3: buscar empleado existente (e2)")
    encontrado = empleados.buscar_empleado("e2")
    if encontrado:
        print(f"✅ Encontrado: {encontrado['nombre']}")
    else:
        print("❌ No se encontró el empleado.")

    print("\n🔍 Caso 4: buscar empleado inexistente (e99)")
    empleados.buscar_empleado("e99")

    print("\n✏️ Caso 5: actualizar empleado existente (e2)")
    empleados.actualizar_empleado("e2", {"cargo": "Encargada"})

    print("\n❌ Caso 6: actualizar empleado inexistente (e99)")
    empleados.actualizar_empleado("e99", {"cargo": "Gerente"})

    print("\n🗑️ Caso 7: eliminar empleado existente (e1)")
    empleados.eliminar_empleado("e1")

    print("\n❌ Caso 8: eliminar empleado inexistente (e99)")
    empleados.eliminar_empleado("e99")

    print("\n📄 Listado final de empleados:")
    empleados.listar_empleados()

if __name__ == "__main__":
    main()
