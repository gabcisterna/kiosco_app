import io
import unittest
from unittest.mock import patch

from modules import console
from modules.console import log


class _StdoutQueFalla:
    def __init__(self):
        self.encoding = "cp1252"
        self.buffer = io.BytesIO()

    def write(self, texto):
        raise UnicodeEncodeError("cp1252", texto, 0, 1, "no representable")


class ConsoleTests(unittest.TestCase):
    def test_log_no_falla_con_caracteres_fuera_de_cp1252(self):
        stdout_falso = _StdoutQueFalla()

        with patch("sys.stdout", stdout_falso):
            log("Mensaje con emoji")

        self.assertTrue(stdout_falso.buffer.getvalue())

    def test_log_no_falla_si_no_hay_stdout_en_modo_exe(self):
        with patch.object(console.sys, "stdout", None), patch.object(
            console.sys, "__stdout__", None
        ), patch.object(console.sys, "stderr", None), patch.object(
            console.sys, "__stderr__", None
        ), patch("modules.console._append_fallback_log") as fallback_mock:
            log("Mensaje sin consola")

        fallback_mock.assert_called_once_with("Mensaje sin consola\n")
