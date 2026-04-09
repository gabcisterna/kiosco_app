import io
import unittest
from unittest.mock import patch

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
            log("✅ Mensaje con emoji")

        self.assertTrue(stdout_falso.buffer.getvalue())
