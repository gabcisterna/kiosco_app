import unittest

from modules.clientes import (
    PREFIJO_REFERENCIA_CLIENTE,
    buscar_clientes_por_texto,
    resolver_cliente_para_venta,
)
from tests.common import isolated_data_env


class ClientesTests(unittest.TestCase):
    def test_resuelve_cliente_habitual_por_nombre_y_crea_referencia_si_falta_dni(self):
        with isolated_data_env():
            cliente_nuevo = resolver_cliente_para_venta(nombre="Juan", crear_si_no_existe=True)
            self.assertTrue(cliente_nuevo["dni"].startswith(PREFIJO_REFERENCIA_CLIENTE))
            self.assertEqual(cliente_nuevo["nombre"], "Juan")

            cliente_existente = resolver_cliente_para_venta(nombre="Juan", crear_si_no_existe=True)
            self.assertEqual(cliente_existente["dni"], cliente_nuevo["dni"])

            por_texto = buscar_clientes_por_texto("juan")
            self.assertEqual(len(por_texto), 1)
            self.assertEqual(por_texto[0]["dni"], cliente_nuevo["dni"])
