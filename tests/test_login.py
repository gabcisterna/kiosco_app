import sys
import os

# Agrega la raíz del proyecto a sys.path para que funcione el import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import login, empleados

def main():
    print("🔐 Probando funciones de inicio y cierre de sesión...\n")

    print("📦 Preparando empleados de prueba...")
    empleados_prueba = [
        {"usuario": "juan", "nombre": "Juan Pérez", "activo": False},
        {"usuario": "ana", "nombre": "Ana Gómez", "activo": False}
    ]
    empleados.guardar_empleados(empleados_prueba)

    print("\n➡️ Caso 1: iniciar sesión con usuario válido")
    login.registrar_inicio_sesion("juan")

    print("\n➡️ Verificando que solo 'juan' esté activo")
    datos = empleados.cargar_empleados()
    for e in datos:
        estado = "🟢 ACTIVO" if e["activo"] else "⚪ INACTIVO"
        print(f"{e['usuario']}: {estado}")

    print("\n➡️ Caso 2: iniciar sesión con otro usuario (ana)")
    login.registrar_inicio_sesion("ana")

    print("\n➡️ Verificando que solo 'ana' esté activa")
    datos = empleados.cargar_empleados()
    for e in datos:
        estado = "🟢 ACTIVO" if e["activo"] else "⚪ INACTIVO"
        print(f"{e['usuario']}: {estado}")

    print("\n➡️ Caso 3: iniciar sesión con usuario inexistente")
    login.registrar_inicio_sesion("noexiste")

    print("\n➡️ Caso 4: cerrar sesión")
    login.cerrar_sesion()

    print("\n➡️ Verificando que todos estén inactivos")
    datos = empleados.cargar_empleados()
    for e in datos:
        estado = "🟢 ACTIVO" if e["activo"] else "⚪ INACTIVO"
        print(f"{e['usuario']}: {estado}")

if __name__ == "__main__":
    main()
