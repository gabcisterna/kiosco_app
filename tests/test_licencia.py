import os
import unittest
from datetime import datetime
from unittest.mock import patch

from modules import licencia
from tests.common import isolated_data_env


def _config_prueba(url="https://licencias.test/sheet.csv", cache_horas=12, offline_grace_days=3, trial_days=7):
    return {
        "google_sheet_csv_url": url,
        "cache_horas": cache_horas,
        "offline_grace_days": offline_grace_days,
        "trial_days": trial_days,
        "timeout_segundos": 5,
    }


class LicenciaTests(unittest.TestCase):
    def test_genera_id_instalacion_y_lo_reutiliza(self):
        with isolated_data_env() as (_, rutas), patch.object(
            licencia, "cargar_configuracion_licencia", return_value=_config_prueba()
        ):
            primer_id = licencia.obtener_id_instalacion()
            segundo_id = licencia.obtener_id_instalacion()

            self.assertEqual(primer_id, segundo_id)
            self.assertTrue(os.path.exists(rutas["instalacion"]))

    def test_activa_licencia_si_el_id_existe_y_esta_activo_online(self):
        with isolated_data_env() as (_, rutas), patch.object(
            licencia, "cargar_configuracion_licencia", return_value=_config_prueba()
        ):
            id_instalacion = licencia.obtener_id_instalacion()
            fecha_base = datetime(2026, 4, 10, 10, 0, 0)

            with patch.object(licencia, "_ahora", return_value=fecha_base), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[
                    {
                        "id_instalacion": id_instalacion,
                        "estado": "activa",
                        "fecha_opcional": "2026-04-10",
                    }
                ],
            ):
                estado = licencia.validar_licencia(forzar=True)

            self.assertTrue(estado["permitir_uso"])
            self.assertEqual(estado["estado"], "activa")
            self.assertEqual(estado["origen"], "online")
            self.assertTrue(os.path.exists(rutas["cache_licencia"]))

    def test_si_id_no_existe_activa_prueba_unica(self):
        with isolated_data_env() as (_, rutas), patch.object(
            licencia, "cargar_configuracion_licencia", return_value=_config_prueba()
        ):
            fecha_base = datetime(2026, 4, 10, 8, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_base), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[
                    {
                        "id_instalacion": "otro-id",
                        "estado": "activa",
                        "fecha_opcional": "",
                    }
                ],
            ):
                estado = licencia.validar_licencia(forzar=True)

            self.assertTrue(estado["permitir_uso"])
            self.assertEqual(estado["estado"], "prueba")
            self.assertEqual(estado["origen"], "prueba")
            self.assertGreaterEqual(estado["dias_restantes_prueba"], 1)

            datos_instalacion = licencia._leer_datos_de_archivo(rutas["instalacion"])
            self.assertIn("prueba_unica", datos_instalacion)

    def test_bloquea_cuando_la_prueba_unica_expira(self):
        with isolated_data_env(), patch.object(
            licencia, "cargar_configuracion_licencia", return_value=_config_prueba(trial_days=7)
        ):
            fecha_inicio = datetime(2026, 4, 10, 8, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_inicio), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[],
            ):
                primer_estado = licencia.validar_licencia(forzar=True)

            self.assertEqual(primer_estado["estado"], "prueba")

            fecha_vencida = datetime(2026, 4, 18, 8, 0, 1)
            with patch.object(licencia, "_ahora", return_value=fecha_vencida), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[],
            ):
                estado = licencia.validar_licencia(forzar=True)

            self.assertFalse(estado["permitir_uso"])
            self.assertEqual(estado["estado"], "prueba_vencida")

    def test_no_habilita_prueba_si_la_licencia_esta_bloqueada(self):
        with isolated_data_env(), patch.object(
            licencia, "cargar_configuracion_licencia", return_value=_config_prueba()
        ):
            id_instalacion = licencia.obtener_id_instalacion()
            with patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[
                    {
                        "id_instalacion": id_instalacion,
                        "estado": "bloqueada",
                        "fecha_opcional": "2026-04-10",
                    }
                ],
            ):
                estado = licencia.validar_licencia(forzar=True)

            self.assertFalse(estado["permitir_uso"])
            self.assertEqual(estado["estado"], "bloqueada")

    def test_reutiliza_cache_activo_dentro_de_la_ventana_configurada(self):
        with isolated_data_env(), patch.object(
            licencia, "cargar_configuracion_licencia", return_value=_config_prueba(cache_horas=12)
        ):
            id_instalacion = licencia.obtener_id_instalacion()

            fecha_online = datetime(2026, 4, 10, 9, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_online), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[
                    {
                        "id_instalacion": id_instalacion,
                        "estado": "activa",
                        "fecha_opcional": "2026-04-10",
                    }
                ],
            ):
                licencia.validar_licencia(forzar=True)

            fecha_cache = datetime(2026, 4, 10, 15, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_cache), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                side_effect=AssertionError("No deberia consultar online dentro de la ventana de cache."),
            ):
                estado = licencia.validar_licencia()

            self.assertTrue(estado["permitir_uso"])
            self.assertEqual(estado["origen"], "cache")

    def test_permite_gracia_offline_si_hubo_validacion_exitosa_previa(self):
        with isolated_data_env(), patch.object(
            licencia,
            "cargar_configuracion_licencia",
            return_value=_config_prueba(cache_horas=1, offline_grace_days=3),
        ):
            id_instalacion = licencia.obtener_id_instalacion()

            fecha_online = datetime(2026, 4, 10, 9, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_online), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[
                    {
                        "id_instalacion": id_instalacion,
                        "estado": "activa",
                        "fecha_opcional": "2026-04-10",
                    }
                ],
            ):
                licencia.validar_licencia(forzar=True)

            fecha_offline = datetime(2026, 4, 11, 12, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_offline), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                side_effect=OSError("sin internet"),
            ):
                estado = licencia.validar_licencia(forzar=True)

            self.assertTrue(estado["permitir_uso"])
            self.assertEqual(estado["origen"], "gracia_offline")
            self.assertGreaterEqual(estado["dias_restantes_offline"], 1)

    def test_bloquea_si_se_supera_la_gracia_offline(self):
        with isolated_data_env(), patch.object(
            licencia,
            "cargar_configuracion_licencia",
            return_value=_config_prueba(cache_horas=1, offline_grace_days=3),
        ):
            id_instalacion = licencia.obtener_id_instalacion()

            fecha_online = datetime(2026, 4, 10, 9, 0, 0)
            with patch.object(licencia, "_ahora", return_value=fecha_online), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                return_value=[
                    {
                        "id_instalacion": id_instalacion,
                        "estado": "activa",
                        "fecha_opcional": "2026-04-10",
                    }
                ],
            ):
                licencia.validar_licencia(forzar=True)

            fecha_vencida = datetime(2026, 4, 14, 10, 0, 1)
            with patch.object(licencia, "_ahora", return_value=fecha_vencida), patch.object(
                licencia,
                "_consultar_licencias_remotas",
                side_effect=OSError("sin internet"),
            ):
                estado = licencia.validar_licencia(forzar=True)

            self.assertFalse(estado["permitir_uso"])
            self.assertEqual(estado["estado"], "sin_conexion")

    def test_construye_url_whatsapp_para_registro(self):
        with isolated_data_env():
            id_instalacion = "11111111-2222-3333-4444-555555555555"
            url = licencia.obtener_url_whatsapp_registro(id_instalacion)

            self.assertIn("wa.me/543517532845", url)
            self.assertIn(id_instalacion, url)

    def test_notifica_al_generar_id_si_hay_canal_automatico(self):
        with isolated_data_env(), patch.object(
            licencia, "_configuracion_notificacion_registro"
        ) as config_mock, patch.object(
            licencia, "_enviar_notificacion_registro", return_value=True
        ) as enviar_mock:
            config_mock.return_value = {
                "webhook_url": "https://hooks.test/registro-id",
                "whatsapp_phone": "543517532845",
                "callmebot_api_key": "",
                "timeout_segundos": 5,
            }

            id_instalacion = licencia.obtener_id_instalacion()

            enviar_mock.assert_called_once()
            datos = licencia._leer_datos_de_archivo(licencia.ARCHIVO_INSTALACION)
            self.assertEqual(datos["id_instalacion"], id_instalacion)
            self.assertEqual(datos["notificacion_registro"]["estado"], "enviada")

            enviar_mock.reset_mock()
            self.assertEqual(licencia.obtener_id_instalacion(), id_instalacion)
            enviar_mock.assert_not_called()

    def test_boton_whatsapp_intenta_envio_automatico_y_devuelve_estado(self):
        with isolated_data_env(), patch.object(
            licencia, "_configuracion_notificacion_registro"
        ) as config_mock, patch.object(
            licencia, "_enviar_whatsapp_callmebot", return_value=True
        ) as enviar_mock:
            config_mock.return_value = {
                "webhook_url": "",
                "whatsapp_phone": "543517532845",
                "callmebot_api_key": "api-test",
                "timeout_segundos": 5,
            }

            id_instalacion = licencia.obtener_id_instalacion()
            enviar_mock.reset_mock()

            resultado = licencia.enviar_whatsapp_registro(id_instalacion)

            self.assertTrue(resultado["ok"])
            self.assertEqual(resultado["modo"], "automatico")
            self.assertIn("ID enviada correctamente", resultado["mensaje"])
            enviar_mock.assert_called_once()

            datos = licencia._leer_datos_de_archivo(licencia.ARCHIVO_INSTALACION)
            self.assertEqual(datos["notificacion_registro"]["estado"], "enviada")
