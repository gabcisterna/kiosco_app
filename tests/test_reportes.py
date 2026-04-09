import os
import unittest

from modules.empleados import guardar_empleados
from modules.reportes import exportar_reporte_ventas, generar_reporte_ventas
from modules.ventas import guardar_ventas
from tests.common import isolated_data_env


class ReportesTests(unittest.TestCase):
    def test_genera_reportes_diarios_semanales_y_mensuales(self):
        with isolated_data_env():
            guardar_empleados(
                [
                    {
                        "id": "1",
                        "nombre": "Ana",
                        "correo": "ana@example.com",
                        "puesto": "Dueño",
                        "activo": False,
                    },
                    {
                        "id": "2",
                        "nombre": "Luis",
                        "correo": "luis@example.com",
                        "puesto": "Encargado",
                        "activo": False,
                    },
                ]
            )
            guardar_ventas(
                [
                    {
                        "fecha": "2026-04-08 10:00:00",
                        "empleado_id": "1",
                        "cliente_dni": None,
                        "forma_pago": "efectivo",
                        "subtotal": 100.0,
                        "ajuste": {"tipo": None, "modo": None, "valor": 0, "importe_aplicado": 0},
                        "total": 100.0,
                        "productos": [
                            {
                                "id": 1,
                                "nombre": "Coca Cola",
                                "cantidad": 2,
                                "precio_unitario": 50.0,
                                "subtotal": 100.0,
                            }
                        ],
                    },
                    {
                        "fecha": "2026-04-08 18:00:00",
                        "empleado_id": "2",
                        "cliente_dni": None,
                        "forma_pago": "debito",
                        "subtotal": 50.0,
                        "ajuste": {"tipo": None, "modo": None, "valor": 0, "importe_aplicado": 0},
                        "total": 50.0,
                        "productos": [
                            {
                                "id": 2,
                                "nombre": "Papas",
                                "cantidad": 1,
                                "precio_unitario": 50.0,
                                "subtotal": 50.0,
                            }
                        ],
                    },
                    {
                        "fecha": "2026-04-07 09:00:00",
                        "empleado_id": "1",
                        "cliente_dni": None,
                        "forma_pago": "deuda",
                        "subtotal": 200.0,
                        "ajuste": {"tipo": None, "modo": None, "valor": 0, "importe_aplicado": 0},
                        "total": 200.0,
                        "productos": [
                            {
                                "id": 1,
                                "nombre": "Coca Cola",
                                "cantidad": 1,
                                "precio_unitario": 50.0,
                                "subtotal": 50.0,
                            },
                            {
                                "id": 3,
                                "nombre": "Galletitas",
                                "cantidad": 3,
                                "precio_unitario": 50.0,
                                "subtotal": 150.0,
                            },
                        ],
                    },
                    {
                        "fecha": "2026-03-30 15:00:00",
                        "empleado_id": "2",
                        "cliente_dni": None,
                        "forma_pago": "efectivo",
                        "subtotal": 999.0,
                        "ajuste": {"tipo": None, "modo": None, "valor": 0, "importe_aplicado": 0},
                        "total": 999.0,
                        "productos": [
                            {
                                "id": 9,
                                "nombre": "Fuera de mes",
                                "cantidad": 1,
                                "precio_unitario": 999.0,
                                "subtotal": 999.0,
                            }
                        ],
                    },
                ]
            )

            diario = generar_reporte_ventas("diario", "2026-04-08")
            self.assertEqual(diario["cantidad_ventas"], 2)
            self.assertEqual(diario["total_facturado"], 150.0)
            self.assertEqual(diario["mejor_producto"]["nombre"], "Coca Cola")

            semanal = generar_reporte_ventas("semanal", "2026-04-09")
            self.assertEqual(semanal["cantidad_ventas"], 3)
            self.assertEqual(semanal["mejor_producto"]["cantidad_vendida"], 3)
            self.assertEqual(semanal["mejor_empleado"]["nombre"], "Ana")

            mensual = generar_reporte_ventas("mensual", "2026-04-15")
            self.assertEqual(mensual["cantidad_ventas"], 3)
            self.assertEqual(mensual["productos_distintos"], 3)
            self.assertEqual(mensual["formas_pago"][0]["forma_pago"], "deuda")

    def test_exporta_reporte_a_csv_compatible_con_excel(self):
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
            guardar_ventas(
                [
                    {
                        "fecha": "2026-04-08 10:00:00",
                        "empleado_id": "1",
                        "cliente_dni": None,
                        "forma_pago": "efectivo",
                        "subtotal": 100.0,
                        "ajuste": {"tipo": None, "modo": None, "valor": 0, "importe_aplicado": 0},
                        "total": 100.0,
                        "productos": [
                            {
                                "id": 1,
                                "nombre": "Coca Cola",
                                "cantidad": 2,
                                "precio_unitario": 50.0,
                                "subtotal": 100.0,
                            }
                        ],
                    }
                ]
            )

            reporte = generar_reporte_ventas("diario", "2026-04-08")
            ruta_csv = os.path.join(temp_dir, "reporte.csv")
            exportar_reporte_ventas(reporte, ruta_csv)

            with open(ruta_csv, "r", encoding="utf-8-sig") as archivo:
                contenido = archivo.read()

            self.assertIn("Resumen", contenido)
            self.assertIn("Productos mas vendidos", contenido)
            self.assertIn("Coca Cola", contenido)
