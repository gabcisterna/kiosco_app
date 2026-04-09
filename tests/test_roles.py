import unittest

from modules.empleados import (
    PUESTO_CONSULTA_PRODUCTOS,
    PUESTO_DUENO,
    PUESTO_REPOSITOR,
    empleado_tiene_permiso,
    obtener_permisos_por_puesto,
)
from ui.pantalla_principal import PantallaCaja


class RolesTests(unittest.TestCase):
    def test_puestos_tienen_permisos_esperados(self):
        self.assertTrue(empleado_tiene_permiso({"puesto": PUESTO_DUENO}, "ver_reportes"))
        self.assertTrue(empleado_tiene_permiso({"puesto": PUESTO_REPOSITOR}, "gestionar_productos"))
        self.assertFalse(empleado_tiene_permiso({"puesto": PUESTO_REPOSITOR}, "usar_caja"))
        self.assertTrue(empleado_tiene_permiso({"puesto": PUESTO_CONSULTA_PRODUCTOS}, "ver_productos"))
        self.assertFalse(empleado_tiene_permiso({"puesto": PUESTO_CONSULTA_PRODUCTOS}, "gestionar_productos"))
        self.assertFalse(empleado_tiene_permiso({"puesto": PUESTO_CONSULTA_PRODUCTOS}, "usar_caja"))

    def test_panel_superior_muestra_solo_productos_para_consulta(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.permisos = obtener_permisos_por_puesto(PUESTO_CONSULTA_PRODUCTOS)
        pantalla.abrir_popup_productos = lambda: None
        pantalla.abrir_popup_ventas = lambda: None
        pantalla.abrir_popup_registros = lambda: None
        pantalla.abrir_popup_deudas = lambda: None
        pantalla.abrir_popup_debito = lambda: None
        pantalla.abrir_popup_clientes = lambda: None
        pantalla.abrir_popup_reportes = lambda: None
        pantalla.abrir_popup_empleados = lambda: None

        botones = PantallaCaja._definir_botones_admin(pantalla)

        self.assertEqual([texto for texto, _ in botones], ["Productos"])
