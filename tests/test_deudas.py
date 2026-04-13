import unittest

from modules.clientes import PREFIJO_REFERENCIA_CLIENTE, buscar_cliente, guardar_clientes
from modules.deudas import cargar_deudas
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
                        "puesto": "Dueño",
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
                        "puesto": "Dueño",
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
                cliente_nombre="Cliente rápido",
            )

            self.assertTrue(ok)
            deudas = cargar_deudas()
            self.assertEqual(len(deudas), 1)
            self.assertTrue(deudas[0]["dni"].startswith(PREFIJO_REFERENCIA_CLIENTE))
            self.assertEqual(deudas[0]["nombre"], "Cliente rápido")
            self.assertEqual(buscar_cliente(deudas[0]["dni"])["deuda"], 100.0)
