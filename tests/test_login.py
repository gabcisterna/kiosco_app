import json
import unittest
from unittest.mock import MagicMock, patch

from modules import login as login_module
from modules import console
from modules.empleados import cargar_empleados, guardar_empleados
from modules.login import cerrar_sesion, registrar_inicio_sesion
from tests.common import isolated_data_env
from ui.pantalla_login import LoginApp


class DummyEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value


class LoginTests(unittest.TestCase):
    def test_login_handles_employees_without_usuario(self):
        with isolated_data_env():
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

            self.assertTrue(registrar_inicio_sesion("ana@example.com"))

            empleado = cargar_empleados()[0]
            self.assertTrue(empleado["activo"])
            self.assertEqual(empleado["usuario"], "ana@example.com")

            with open(login_module.RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                turnos = json.load(archivo)

            self.assertEqual(turnos[0]["empleado"], "Ana")
            self.assertEqual(turnos[0]["usuario"], "ana@example.com")
            self.assertIsNone(turnos[0]["fin"])

            self.assertTrue(cerrar_sesion())

            with open(login_module.RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                turnos = json.load(archivo)

            self.assertIsNotNone(turnos[0]["fin"])

    def test_login_ui_acepta_correo_con_mayusculas(self):
        app = LoginApp.__new__(LoginApp)
        app.entry_correo = DummyEntry("ANA@EXAMPLE.COM")
        app.master = MagicMock()

        empleado = {
            "id": "1",
            "nombre": "Ana",
            "correo": "ana@example.com",
            "usuario": "ana@example.com",
            "puesto": "Dueño",
            "activo": False,
        }

        with patch("ui.pantalla_login.buscar_empleado_por_correo", return_value=empleado) as buscar_mock, patch(
            "ui.pantalla_login.registrar_inicio_sesion", return_value=True
        ) as registrar_mock, patch("ui.pantalla_login.messagebox.showinfo") as showinfo_mock, patch(
            "ui.pantalla_login.mostrar_caja"
        ) as mostrar_caja_mock:
            LoginApp.iniciar_sesion(app)
            app.master.after_idle.assert_called_once()
            callback = app.master.after_idle.call_args.args[0]
            callback()

        buscar_mock.assert_called_once_with("ana@example.com")
        registrar_mock.assert_called_once_with("ana@example.com")
        showinfo_mock.assert_called_once_with(
            "Sesion iniciada",
            "Bienvenido: Ana",
            parent=app.master,
        )
        mostrar_caja_mock.assert_called_once_with(app.master)

    def test_fuerza_registro_inicial_si_no_hay_empleados(self):
        app = LoginApp.__new__(LoginApp)
        app.mensaje_secundario_var = MagicMock()
        app.boton_registro = MagicMock()
        app.boton_login = MagicMock()
        app.abrir_registro = MagicMock()

        with patch("ui.pantalla_login.cargar_empleados", return_value=[]):
            LoginApp._forzar_registro_inicial_si_hace_falta(app)

        app.boton_registro.config.assert_called_with(text="Registrar dueño")
        app.boton_login.config.assert_called_with(state="disabled")
        app.abrir_registro.assert_called_once_with(es_obligatorio=True)

    def test_registrar_inicio_sesion_funciona_sin_stdout_en_modo_exe(self):
        with isolated_data_env():
            guardar_empleados(
                [
                    {
                        "id": "1",
                        "nombre": "Ana",
                        "correo": "ana@example.com",
                        "puesto": "Dueño",
                        "usuario": "ana@example.com",
                        "activo": False,
                    }
                ]
            )

            with patch.object(console.sys, "stdout", None), patch.object(
                console.sys, "__stdout__", None
            ), patch.object(console.sys, "stderr", None), patch.object(
                console.sys, "__stderr__", None
            ):
                self.assertTrue(registrar_inicio_sesion("ana@example.com"))

            empleado = cargar_empleados()[0]
            self.assertTrue(empleado["activo"])

            with open(login_module.RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                turnos = json.load(archivo)

            self.assertEqual(turnos[0]["usuario"], "ana@example.com")
