import unittest

from modules.empleados import guardar_empleados
from modules.productos import buscar_producto, guardar_productos
from modules.reposiciones import cargar_registro_stock, registrar_reposicion_stock
from tests.common import isolated_data_env


class ReposicionesTests(unittest.TestCase):
    def test_registrar_reposicion_actualiza_stock_y_guarda_movimiento(self):
        with isolated_data_env():
            guardar_empleados(
                [
                    {
                        "id": "1",
                        "nombre": "Ana",
                        "correo": "ana@example.com",
                        "puesto": "Encargado",
                        "activo": True,
                    }
                ]
            )
            guardar_productos(
                [
                    {
                        "id": 10,
                        "nombre": "Galletitas",
                        "precio": 1500.0,
                        "stock_actual": 4,
                        "stock_minimo": 1,
                    }
                ]
            )

            ok, movimiento = registrar_reposicion_stock(10, 6, 900)

            self.assertTrue(ok)
            self.assertEqual(buscar_producto(10)["stock_actual"], 10)
            self.assertEqual(movimiento["empleado_nombre"], "Ana")
            self.assertEqual(movimiento["precio_costo"], 900.0)
            self.assertEqual(movimiento["precio_venta"], 1500.0)
            self.assertEqual(movimiento["stock_anterior"], 4)
            self.assertEqual(movimiento["stock_nuevo"], 10)
            self.assertEqual(cargar_registro_stock()[0]["producto_id"], 10)

    def test_registrar_reposicion_respeta_decimales_en_kilos(self):
        with isolated_data_env():
            guardar_productos(
                [
                    {
                        "id": 20,
                        "nombre": "Queso",
                        "precio": 8000.0,
                        "stock_actual": 1.5,
                        "stock_minimo": 0.5,
                        "tipo_venta": "kilo",
                    }
                ]
            )

            ok, movimiento = registrar_reposicion_stock(20, "0.750", "5200")

            self.assertTrue(ok)
            self.assertEqual(buscar_producto(20)["stock_actual"], 2.25)
            self.assertEqual(movimiento["cantidad"], 0.75)
            self.assertEqual(movimiento["detalle"][0]["subtotal"], 3900.0)
