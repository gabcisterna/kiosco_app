import json
import unittest

from modules import login as login_module
from modules.empleados import cargar_empleados, guardar_empleados
from modules.login import cerrar_sesion, registrar_inicio_sesion
from tests.common import isolated_data_env


class LoginTests(unittest.TestCase):
    def test_login_handles_employees_without_usuario(self):
        with isolated_data_env():
            guardar_empleados(
                [
                    {
                        "id": "1",
                        "nombre": "Ana",
                        "correo": "ana@example.com",
                        "puesto": "Dueño",
                        "activo": False,
                    }
                ]
            )

            self.assertTrue(registrar_inicio_sesion("ana@example.com"))

            empleado = cargar_empleados()[0]
            self.assertTrue(empleado["activo"])
            self.assertEqual(empleado["usuario"], "ana@example.com")

            with open(login_module.RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                turnos = json.load(archivo)

            self.assertEqual(turnos[0]["empleado"], "Ana")
            self.assertEqual(turnos[0]["usuario"], "ana@example.com")
            self.assertIsNone(turnos[0]["fin"])

            self.assertTrue(cerrar_sesion())

            with open(login_module.RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                turnos = json.load(archivo)

            self.assertIsNotNone(turnos[0]["fin"])
