import unittest
from unittest.mock import MagicMock, patch

from modules.productos import guardar_productos
from tests.common import isolated_data_env
from ui.pantalla_principal import PantallaCaja


class DummyEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def delete(self, start, end):
        self.value = ""

    def insert(self, index, value):
        self.value = value


class DummyListbox:
    def __init__(self, value=None, selection=()):
        self.value = value
        self.selection = selection

    def curselection(self):
        return self.selection

    def get(self, index):
        return self.value

    def delete(self, start, end):
        self.value = None
        self.selection = ()

    def grid_remove(self):
        return None


class UIFlowTests(unittest.TestCase):
    def test_cerrar_sesion_vuelve_al_login_y_arranca_el_nuevo_mainloop(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.master = MagicMock()
        pantalla.ir_a_login = MagicMock()

        nuevo_root = MagicMock()
        with patch("ui.pantalla_principal.cerrar_sesion") as cerrar_sesion_mock, patch(
            "ui.pantalla_principal.tk.Tk", return_value=nuevo_root
        ):
            PantallaCaja.cerrar_sesion_y_volver_al_login(pantalla)

        cerrar_sesion_mock.assert_called_once_with()
        pantalla.master.destroy.assert_called_once_with()
        pantalla.ir_a_login.assert_called_once_with(nuevo_root)
        nuevo_root.mainloop.assert_called_once_with()

    def test_resolver_producto_desde_entrada_acepta_nombre_e_id_en_sugerencia(self):
        with isolated_data_env():
            guardar_productos(
                [
                    {
                        "id": 10,
                        "nombre": "Coca Cola",
                        "precio": 1200.0,
                        "stock_actual": 8,
                        "stock_minimo": 1,
                    },
                    {
                        "id": 25,
                        "nombre": "Yerba Suave",
                        "precio": 3500.0,
                        "stock_actual": 4,
                        "stock_minimo": 1,
                    },
                ]
            )

            pantalla = PantallaCaja.__new__(PantallaCaja)
            pantalla.entrada_id = DummyEntry("Yerba Suave")
            pantalla.lista_sugerencias = DummyListbox()

            producto = PantallaCaja._resolver_producto_desde_entrada(pantalla)
            self.assertEqual(producto["id"], 25)

            pantalla.entrada_id = DummyEntry("10 - Coca Cola")
            pantalla.lista_sugerencias = DummyListbox(value="10 - Coca Cola", selection=(0,))

            producto = PantallaCaja._resolver_producto_desde_entrada(pantalla)
            self.assertEqual(producto["id"], 10)
