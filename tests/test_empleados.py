import unittest

from modules.empleados import (
    PUESTO_CAJERO,
    PUESTO_DUENO,
    agregar_empleado,
    buscar_empleado_por_correo,
    cargar_empleados,
)
from tests.common import isolated_data_env


class EmpleadosTests(unittest.TestCase):
    def test_primer_empleado_se_guarda_como_dueno(self):
        with isolated_data_env():
            self.assertTrue(
                agregar_empleado(
                    {
                        "id": "1",
                        "nombre": "Ana",
                        "correo": "Ana@Example.com",
                        "puesto": PUESTO_CAJERO,
                        "activo": False,
                    }
                )
            )

            empleado = cargar_empleados()[0]
            self.assertEqual(empleado["puesto"], PUESTO_DUENO)
            self.assertEqual(empleado["correo"], "ana@example.com")

    def test_buscar_empleado_por_correo_ignora_mayusculas(self):
        with isolated_data_env():
            self.assertTrue(
                agregar_empleado(
                    {
                        "id": "1",
                        "nombre": "Ana",
                        "correo": "ana@example.com",
                        "puesto": PUESTO_DUENO,
                        "activo": False,
                    }
                )
            )

            empleado = buscar_empleado_por_correo("ANA@EXAMPLE.COM")
            self.assertIsNotNone(empleado)
            self.assertEqual(empleado["nombre"], "Ana")
