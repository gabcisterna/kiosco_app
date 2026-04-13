import os
import unittest

from modules import clientes, debito, deudas, empleados, licencia, login, productos, ventas
from modules.clientes import buscar_cliente, guardar_clientes
from modules.empleados import guardar_empleados
from modules.productos import cargar_productos, guardar_productos
from tests.common import isolated_data_env


class PathConfigTests(unittest.TestCase):
    def test_project_paths_are_absolute(self):
        rutas = [
            clientes.RUTA_CLIENTES,
            debito.RUTA_DEBITO,
            debito.RUTA_REGISTRO_DEBITOS,
            deudas.RUTA_DEUDAS,
            deudas.RUTA_REGISTRO_DEUDAS,
            empleados.RUTA_EMPLEADOS,
            login.RUTA_TURNOS,
            productos.RUTA_PRODUCTOS,
            productos.RUTA_PRODUCTOS_BAJOS,
            ventas.RUTA_VENTAS,
            licencia.ARCHIVO_INSTALACION,
            licencia.ARCHIVO_CACHE,
        ]

        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertTrue(os.path.isabs(ruta))

    def test_data_access_does_not_depend_on_current_workdir(self):
        with isolated_data_env() as (temp_dir, _):
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
            guardar_clientes([{"dni": "1", "nombre": "Cliente", "deuda": 0}])
            guardar_productos(
                [
                    {
                        "id": 1,
                        "nombre": "Producto",
                        "precio": 10.0,
                        "stock_actual": 5,
                        "stock_minimo": 1,
                    }
                ]
            )

            otro_cwd = os.path.join(temp_dir, "otro")
            os.makedirs(otro_cwd, exist_ok=True)
            cwd_original = os.getcwd()

            try:
                os.chdir(otro_cwd)
                self.assertEqual(buscar_cliente("1")["nombre"], "Cliente")
                self.assertEqual(cargar_productos()[0]["nombre"], "Producto")
            finally:
                os.chdir(cwd_original)
