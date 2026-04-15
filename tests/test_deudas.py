import unittest

from modules.clientes import PREFIJO_REFERENCIA_CLIENTE, buscar_cliente, guardar_clientes
from modules.deudas import cargar_deudas, pagar_productos_deuda
from modules.empleados import guardar_empleados
from modules.productos import actualizar_producto, guardar_productos
from modules.ventas import registrar_venta
from tests.common import isolated_data_env


class DeudasTests(unittest.TestCase):
    def test_deuda_y_cliente_se_recalcular_con_precio_actual(self):
        with isolated_data_env():
            guardar_clientes([{"dni": "1", "nombre": "Juan", "deuda": 0}])
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
                        "nombre": "Producto",
                        "precio": 100.0,
                        "stock_actual": 10,
                        "stock_minimo": 1,
                    }
                ]
            )

            ok = registrar_venta(
                [{"id": 1, "cantidad": 1}],
                "deuda",
                cliente_dni="1",
                cliente_nombre="Juan",
                ajuste={"tipo": "descuento", "modo": "porcentaje", "valor": 50, "importe_aplicado": 50},
            )

            self.assertTrue(ok)
            self.assertEqual(cargar_deudas()[0]["monto"], 100.0)
            self.assertEqual(buscar_cliente("1")["deuda"], 100.0)

            self.assertTrue(actualizar_producto(1, {"precio": 200.0}))
            self.assertEqual(cargar_deudas()[0]["monto"], 200.0)
            self.assertEqual(buscar_cliente("1")["deuda"], 200.0)

    def test_permite_registrar_deuda_con_nombre_sin_dni(self):
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
                        "nombre": "Producto",
                        "precio": 100.0,
                        "stock_actual": 10,
                        "stock_minimo": 1,
                    }
                ]
            )

            ok = registrar_venta(
                [{"id": 1, "cantidad": 1}],
                "deuda",
                cliente_dni=None,
                cliente_nombre="Cliente rapido",
            )

            self.assertTrue(ok)
            deudas = cargar_deudas()
            self.assertEqual(len(deudas), 1)
            self.assertTrue(deudas[0]["dni"].startswith(PREFIJO_REFERENCIA_CLIENTE))
            self.assertEqual(deudas[0]["nombre"], "Cliente rapido")
            self.assertEqual(buscar_cliente(deudas[0]["dni"])["deuda"], 100.0)

    def test_permite_pagar_deuda_por_kilo(self):
        with isolated_data_env():
            guardar_clientes([{"dni": "1", "nombre": "Ana", "deuda": 0}])
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
                        "precio": 8000.0,
                        "stock_actual": 5.0,
                        "stock_minimo": 0.5,
                        "tipo_venta": "kilo",
                    }
                ]
            )

            ok = registrar_venta(
                [{"id": 1, "cantidad": 1.5}],
                "deuda",
                cliente_dni="1",
                cliente_nombre="Ana",
            )

            self.assertTrue(ok)
            self.assertEqual(cargar_deudas()[0]["monto"], 12000.0)

            ok, _ = pagar_productos_deuda("1", [{"id": 1, "cantidad": "0.5"}])
            self.assertTrue(ok)

            deuda = cargar_deudas()[0]
            self.assertEqual(deuda["monto"], 8000.0)
            self.assertEqual(deuda["productos"][0]["cantidad_total"], 1.5)
            self.assertEqual(deuda["productos"][0]["cantidad_pagada"], 0.5)
