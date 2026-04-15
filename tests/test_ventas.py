import unittest

from modules.empleados import guardar_empleados
from modules.productos import buscar_producto, guardar_productos
from modules.ventas import cargar_ventas, registrar_venta
from tests.common import isolated_data_env


class VentasTests(unittest.TestCase):
    def test_registra_venta_por_kilo_y_descuenta_stock(self):
        with isolated_data_env():
            guardar_empleados(
                [
                    {
                        "id": "1",
                        "nombre": "Admin",
                        "correo": "admin@example.com",
                        "puesto": "Dueno",
                        "activo": True,
                    }
                ]
            )
            guardar_productos(
                [
                    {
                        "id": 1,
                        "nombre": "Queso",
                        "precio": 10000.0,
                        "stock_actual": 5.0,
                        "stock_minimo": 0.5,
                        "tipo_venta": "kilo",
                    }
                ]
            )

            ok = registrar_venta([{"id": 1, "cantidad": "0.5"}], "efectivo")

            self.assertTrue(ok)
            self.assertEqual(buscar_producto(1)["stock_actual"], 4.5)

            venta = cargar_ventas()[0]
            self.assertEqual(venta["subtotal"], 5000.0)
            self.assertEqual(venta["total"], 5000.0)
            self.assertEqual(venta["productos"][0]["cantidad"], 0.5)
            self.assertEqual(venta["productos"][0]["tipo_venta"], "kilo")
            self.assertEqual(venta["productos"][0]["unidad_medida"], "kg")
