import unittest

from modules.productos import buscar_productos_por_texto, guardar_productos
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
