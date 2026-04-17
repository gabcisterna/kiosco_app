import unittest

from modules.productos import (
    actualizar_producto,
    buscar_producto,
    buscar_productos_por_texto,
    guardar_productos,
    guardar_productos_bajos,
    listar_productos_con_stock_bajo,
)
from tests.common import isolated_data_env


class ProductSearchTests(unittest.TestCase):
    def test_busca_productos_por_id_y_nombre(self):
        with isolated_data_env():
            guardar_productos(
                [
                    {
                        "id": 1,
                        "nombre": "Coca Cola 500",
                        "precio": 1200.0,
                        "stock_actual": 10,
                        "stock_minimo": 2,
                    },
                    {
                        "id": 15,
                        "nombre": "Coca Cola Zero",
                        "precio": 1300.0,
                        "stock_actual": 10,
                        "stock_minimo": 2,
                    },
                    {
                        "id": 22,
                        "nombre": "Yerba Suave",
                        "precio": 2500.0,
                        "stock_actual": 7,
                        "stock_minimo": 2,
                    },
                ]
            )

            self.assertEqual(buscar_productos_por_texto("22")[0]["nombre"], "Yerba Suave")
            coincidencias = buscar_productos_por_texto("coca")
            self.assertEqual([producto["id"] for producto in coincidencias], [1, 15])
            self.assertEqual(buscar_productos_por_texto("Yerba")[0]["id"], 22)

    def test_actualizar_producto_permite_cambiar_id_y_sincroniza_stock_bajo(self):
        with isolated_data_env():
            producto = {
                "id": 1,
                "nombre": "Pan",
                "precio": 1200.0,
                "stock_actual": 1,
                "stock_minimo": 2,
            }
            guardar_productos([producto])
            guardar_productos_bajos([producto])

            ok = actualizar_producto(
                1,
                {
                    "id": 44,
                    "nombre": "Pan",
                    "precio": 1200.0,
                    "stock_actual": 1,
                    "stock_minimo": 2,
                },
            )

            self.assertTrue(ok)
            self.assertIsNone(buscar_producto(1))
            self.assertEqual(buscar_producto(44)["nombre"], "Pan")
            self.assertEqual([p["id"] for p in listar_productos_con_stock_bajo()], [44])

    def test_actualizar_producto_rechaza_id_duplicado(self):
        with isolated_data_env():
            guardar_productos(
                [
                    {
                        "id": 1,
                        "nombre": "Pan",
                        "precio": 1200.0,
                        "stock_actual": 5,
                        "stock_minimo": 2,
                    },
                    {
                        "id": 2,
                        "nombre": "Leche",
                        "precio": 1500.0,
                        "stock_actual": 8,
                        "stock_minimo": 2,
                    },
                ]
            )

            ok = actualizar_producto(
                1,
                {
                    "id": 2,
                    "nombre": "Pan",
                    "precio": 1200.0,
                    "stock_actual": 5,
                    "stock_minimo": 2,
                },
            )

            self.assertFalse(ok)
            self.assertIsNotNone(buscar_producto(1))
