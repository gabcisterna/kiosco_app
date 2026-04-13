import argparse
import base64
import csv
import ctypes
import hashlib
import hmac
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timedelta
from io import StringIO
from math import ceil

from modules.console import log
from modules.rutas import asegurar_directorio, ruta_en_base

HORAS_CACHE_LICENCIA = 12
DIAS_GRACIA_SIN_INTERNET = 3
DIAS_PRUEBA_UNICA = 7
TIMEOUT_VALIDACION = 8
VERSION_TOKEN = "K2"
REINTENTOS_VALIDACION_ESTRICTA = 2
PAUSA_REINTENTO_VALIDACION = 0.8
TIMEOUT_NOTIFICACION_REGISTRO = 6
WHATSAPP_DESTINO_REGISTRO = "+54 3517532845"
ENV_WHATSAPP_DESTINO = "KIOSCO_WHATSAPP_DESTINO"
ENV_WHATSAPP_API_KEY = "KIOSCO_WHATSAPP_API_KEY"
ENV_REGISTRO_ID_WEBHOOK = "KIOSCO_REGISTRO_ID_WEBHOOK"
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vR2NYB9XYruoPSIvB3V5Wy1_oDV4hYv3GEMmvdf3Jg9mjYU4H6vzBQdq252KNLkCboQkmnF8NJUZP20/"
    "pub?output=csv"
)


def _ahora():
    return datetime.now()


def _semilla_archivo():
    partes = ("licencia", "instalacion", "cache", "kiosco", "simple")
    orden = (3, 0, 4, 2, 1)
    return "-".join(partes[indice] for indice in orden)


def _directorio_escribible(ruta):
    try:
        os.makedirs(ruta, exist_ok=True)
        ruta_prueba = os.path.join(ruta, ".write_test")
        with open(ruta_prueba, "w", encoding="utf-8") as archivo:
            archivo.write("ok")
        os.remove(ruta_prueba)
        return True
    except OSError:
        return False


def _directorio_licencia():
    candidatos = []
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        candidatos.append(os.path.join(base, "KioscoApp", "System"))
    candidatos.append(ruta_en_base("data", "_system"))

    for candidato in candidatos:
        if _directorio_escribible(candidato):
            return candidato

    return candidatos[-1]


def _directorio_licencia_fallback():
    return ruta_en_base("data", "_system")


ARCHIVO_INSTALACION = os.path.join(_directorio_licencia(), "install.bin")
ARCHIVO_CACHE = os.path.join(_directorio_licencia(), "license_cache.bin")


def _clave_archivo():
    return hashlib.sha256(_semilla_archivo().encode("utf-8")).digest()


def _mezclar_bytes(datos):
    clave = _clave_archivo()
    return bytes(byte ^ clave[indice % len(clave)] for indice, byte in enumerate(datos))


def _firmar_payload(payload):
    base = f"{payload}|{_semilla_archivo()}|firma"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _serializar_datos(datos):
    payload = json.dumps(datos, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_codificado = base64.urlsafe_b64encode(_mezclar_bytes(payload)).decode("ascii")
    firma = _firmar_payload(payload_codificado)
    return f"{VERSION_TOKEN}.{payload_codificado}.{firma}"


def _deserializar_datos(contenido):
    partes = contenido.split(".", 2)
    if len(partes) != 3 or partes[0] != VERSION_TOKEN:
        return None

    _, payload_codificado, firma = partes
    if not hmac.compare_digest(_firmar_payload(payload_codificado), firma):
        return None

    try:
        payload = base64.urlsafe_b64decode(payload_codificado.encode("ascii"))
        return json.loads(_mezclar_bytes(payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _ocultar_ruta_windows(ruta):
    if os.name != "nt" or not ruta:
        return

    try:
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(str(ruta), FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        return


def _leer_archivo(ruta):
    if not os.path.exists(ruta):
        return ""

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return archivo.read().strip()
    except OSError:
        ruta_fallback = _ruta_fallback_archivo(ruta)
        if ruta_fallback != ruta and os.path.exists(ruta_fallback):
            with open(ruta_fallback, "r", encoding="utf-8") as archivo:
                return archivo.read().strip()
        raise


def _ruta_fallback_archivo(ruta):
    directorio_actual = os.path.abspath(os.path.dirname(ruta))
    directorio_fallback = os.path.abspath(_directorio_licencia_fallback())
    if directorio_actual == directorio_fallback:
        return ruta
    return os.path.join(directorio_fallback, os.path.basename(ruta))


def _guardar_archivo(ruta, contenido):
    rutas_candidatas = [ruta]
    ruta_fallback = _ruta_fallback_archivo(ruta)
    if ruta_fallback not in rutas_candidatas:
        rutas_candidatas.append(ruta_fallback)

    ultimo_error = None
    for ruta_candidata in rutas_candidatas:
        try:
            asegurar_directorio(ruta_candidata)
            directorio = os.path.dirname(ruta_candidata) or "."
            descriptor, ruta_temporal = tempfile.mkstemp(
                prefix=".tmp_license_",
                suffix=os.path.splitext(ruta_candidata)[1] or ".tmp",
                dir=directorio,
                text=True,
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                    archivo.write(contenido)
                os.replace(ruta_temporal, ruta_candidata)
            finally:
                if os.path.exists(ruta_temporal):
                    os.remove(ruta_temporal)

            directorios_ocultables = {
                os.path.abspath(_directorio_licencia()),
                os.path.abspath(_directorio_licencia_fallback()),
            }
            ruta_actual = os.path.abspath(ruta_candidata)
            if any(ruta_actual.startswith(directorio) for directorio in directorios_ocultables):
                _ocultar_ruta_windows(ruta_candidata)
            return ruta_candidata
        except OSError as error:
            ultimo_error = error

    if ultimo_error:
        raise ultimo_error
    raise OSError(f"No se pudo guardar el archivo de licencia: {ruta}")


def _leer_datos_de_archivo(ruta):
    contenido = _leer_archivo(ruta)
    if not contenido:
        return None
    return _deserializar_datos(contenido)


def _guardar_datos_en_archivo(ruta, datos):
    _guardar_archivo(ruta, _serializar_datos(datos))


def _leer_datos_instalacion():
    datos = _leer_datos_de_archivo(ARCHIVO_INSTALACION)
    if isinstance(datos, dict) and datos.get("tipo") == "instalacion":
        return datos
    return None


def _estado_notificacion_registro(datos_instalacion):
    notificacion = (datos_instalacion or {}).get("notificacion_registro")
    if isinstance(notificacion, dict):
        return _normalizar_texto_min(notificacion.get("estado"))
    return ""


def _guardar_datos_instalacion(datos_instalacion):
    _guardar_datos_en_archivo(ARCHIVO_INSTALACION, datos_instalacion)


def _marcar_licencia_activada(id_instalacion, fecha_validacion=None):
    datos_instalacion = _leer_datos_instalacion()
    if not datos_instalacion or datos_instalacion.get("id_instalacion") != id_instalacion:
        return

    fecha_validacion = _formatear_fecha_hora(fecha_validacion or _ahora())
    datos_actualizados = dict(datos_instalacion)
    datos_actualizados["licencia_activada_en"] = (
        datos_actualizados.get("licencia_activada_en") or fecha_validacion
    )
    datos_actualizados["ultima_licencia_activa_en"] = fecha_validacion
    _guardar_datos_instalacion(datos_actualizados)


def _actualizar_notificacion_registro(datos_instalacion, estado, error=None):
    datos_actualizados = dict(datos_instalacion or {})
    notificacion = dict(datos_actualizados.get("notificacion_registro") or {})
    notificacion["estado"] = estado
    notificacion["actualizado_en"] = _formatear_fecha_hora(_ahora())
    if error:
        notificacion["error"] = str(error)
    else:
        notificacion.pop("error", None)
    datos_actualizados["notificacion_registro"] = notificacion
    _guardar_datos_instalacion(datos_actualizados)
    return datos_actualizados


def _payload_notificacion_registro(id_instalacion, datos_instalacion=None):
    datos_instalacion = datos_instalacion or {}
    creado_en = datos_instalacion.get("creado_en") or _formatear_fecha_hora(_ahora())
    return {
        "evento": "alta_id_instalacion",
        "id_instalacion": id_instalacion,
        "creado_en": creado_en,
        "equipo": _normalizar_texto(os.environ.get("COMPUTERNAME")) or "equipo-desconocido",
        "mensaje": _mensaje_registro_id_instalacion(id_instalacion, creado_en=creado_en),
        "url_whatsapp": obtener_url_whatsapp_registro(id_instalacion),
    }


def _enviar_webhook_notificacion(payload, config):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        config["webhook_url"],
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "KioscoApp-License/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=config["timeout_segundos"]) as respuesta:
        respuesta.read()
    return True


def _enviar_whatsapp_callmebot(payload, config):
    parametros = urllib.parse.urlencode(
        {
            "phone": config["whatsapp_phone"],
            "text": payload["mensaje"],
            "apikey": config["callmebot_api_key"],
        }
    )
    request = urllib.request.Request(
        f"https://api.callmebot.com/whatsapp.php?{parametros}",
        headers={"User-Agent": "KioscoApp-License/1.0"},
    )
    with urllib.request.urlopen(request, timeout=config["timeout_segundos"]) as respuesta:
        respuesta.read()
    return True


def _enviar_notificacion_registro(id_instalacion, datos_instalacion=None, config=None):
    config = config or _configuracion_notificacion_registro()
    payload = _payload_notificacion_registro(id_instalacion, datos_instalacion=datos_instalacion)

    if config["whatsapp_phone"] and config["callmebot_api_key"]:
        return _enviar_whatsapp_callmebot(payload, config)

    if config["webhook_url"]:
        return _enviar_webhook_notificacion(payload, config)

    return False


def _persistir_resultado_notificacion(id_instalacion, estado, error=None):
    datos_instalacion = _leer_datos_instalacion()
    if not datos_instalacion or datos_instalacion.get("id_instalacion") != id_instalacion:
        return
    _actualizar_notificacion_registro(datos_instalacion, estado, error=error)


def enviar_whatsapp_registro(id_instalacion=None):
    id_instalacion = id_instalacion or obtener_id_instalacion()
    config = _configuracion_notificacion_registro()

    if config["whatsapp_phone"] and config["callmebot_api_key"]:
        datos_instalacion = _leer_datos_instalacion()
        try:
            _enviar_whatsapp_callmebot(
                _payload_notificacion_registro(id_instalacion, datos_instalacion=datos_instalacion),
                config,
            )
            _persistir_resultado_notificacion(id_instalacion, "enviada")
            return {
                "ok": True,
                "modo": "automatico",
                "mensaje": "ID enviada correctamente por WhatsApp.",
            }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as error:
            _persistir_resultado_notificacion(id_instalacion, "pendiente", error=error)
            return {
                "ok": False,
                "modo": "automatico",
                "mensaje": f"No se pudo enviar el WhatsApp automaticamente:\n{error}",
            }

    if abrir_whatsapp_registro(id_instalacion):
        return {
            "ok": True,
            "modo": "manual",
            "mensaje": "Se abrio WhatsApp con el mensaje listo para enviar.",
        }

    return {
        "ok": False,
        "modo": "manual",
        "mensaje": "No se pudo enviar automaticamente ni abrir WhatsApp.",
    }


def _asegurar_notificacion_registro(id_instalacion, datos_instalacion):
    if not id_instalacion or not datos_instalacion:
        return datos_instalacion

    if _estado_notificacion_registro(datos_instalacion) == "enviada":
        return datos_instalacion

    config = _configuracion_notificacion_registro()
    if not _notificacion_automatica_configurada(config):
        return datos_instalacion

    try:
        if _enviar_notificacion_registro(
            id_instalacion,
            datos_instalacion=datos_instalacion,
            config=config,
        ):
            return _actualizar_notificacion_registro(datos_instalacion, "enviada")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as error:
        log(f"Aviso: no se pudo notificar el alta del id_instalacion {id_instalacion}: {error}")
        return _actualizar_notificacion_registro(datos_instalacion, "pendiente", error=error)

    return datos_instalacion


def _normalizar_texto(valor):
    return (valor or "").strip()


def _normalizar_texto_min(valor):
    return _normalizar_texto(valor).lower()


def _normalizar_telefono(valor):
    return "".join(caracter for caracter in str(valor or "") if caracter.isdigit())


def _configuracion_notificacion_registro():
    return {
        "webhook_url": _normalizar_texto(os.environ.get(ENV_REGISTRO_ID_WEBHOOK)),
        "whatsapp_phone": _normalizar_telefono(
            os.environ.get(ENV_WHATSAPP_DESTINO) or WHATSAPP_DESTINO_REGISTRO
        ),
        "callmebot_api_key": _normalizar_texto(os.environ.get(ENV_WHATSAPP_API_KEY)),
        "timeout_segundos": TIMEOUT_NOTIFICACION_REGISTRO,
    }


def _notificacion_automatica_configurada(config=None):
    config = config or _configuracion_notificacion_registro()
    return bool(config["webhook_url"] or (config["whatsapp_phone"] and config["callmebot_api_key"]))


def _mensaje_registro_id_instalacion(id_instalacion, creado_en=None):
    creado_en = _formatear_fecha_hora(creado_en or _ahora())
    equipo = _normalizar_texto(os.environ.get("COMPUTERNAME")) or "equipo-desconocido"
    return (
        "Nuevo id_instalacion generado en Kiosco App.\n"
        f"ID: {id_instalacion}\n"
        f"Equipo: {equipo}\n"
        f"Fecha: {creado_en}"
    )


def obtener_url_whatsapp_registro(id_instalacion=None):
    id_instalacion = id_instalacion or obtener_id_instalacion()
    config = _configuracion_notificacion_registro()
    if not config["whatsapp_phone"]:
        return ""

    mensaje = _mensaje_registro_id_instalacion(id_instalacion)
    query = urllib.parse.urlencode({"text": mensaje})
    return f"https://wa.me/{config['whatsapp_phone']}?{query}"


def abrir_whatsapp_registro(id_instalacion=None):
    url = obtener_url_whatsapp_registro(id_instalacion)
    if not url:
        return False
    return bool(webbrowser.open(url))


def _es_uuid_valido(valor):
    try:
        uuid.UUID(str(valor))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def _parsear_fecha_hora(valor):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def _formatear_fecha_hora(valor):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor.replace(microsecond=0).isoformat()
    return valor


def _dias_restantes_hasta(fecha_limite):
    if not fecha_limite:
        return 0

    if isinstance(fecha_limite, str):
        fecha_limite = _parsear_fecha_hora(fecha_limite)

    if not fecha_limite:
        return 0

    segundos_restantes = (fecha_limite - _ahora()).total_seconds()
    if segundos_restantes <= 0:
        return 0
    return max(1, ceil(segundos_restantes / 86400))


def _crear_estado(
    id_instalacion,
    config,
    estado,
    permitir_uso,
    detalle,
    origen,
    fecha_opcional=None,
    ultima_validacion=None,
    ultima_validacion_exitosa=None,
    gracia_offline_hasta=None,
    prueba_iniciada_en=None,
    prueba_hasta=None,
):
    return {
        "id_instalacion": id_instalacion,
        "estado": estado,
        "permitir_uso": permitir_uso,
        "detalle": detalle,
        "origen": origen,
        "fecha_opcional": fecha_opcional,
        "ultima_validacion": _formatear_fecha_hora(ultima_validacion),
        "ultima_validacion_exitosa": _formatear_fecha_hora(ultima_validacion_exitosa),
        "gracia_offline_hasta": _formatear_fecha_hora(gracia_offline_hasta),
        "dias_restantes_offline": _dias_restantes_hasta(gracia_offline_hasta),
        "cache_horas": config["cache_horas"],
        "offline_grace_days": config["offline_grace_days"],
        "prueba_iniciada_en": _formatear_fecha_hora(prueba_iniciada_en),
        "prueba_hasta": _formatear_fecha_hora(prueba_hasta),
        "dias_restantes_prueba": _dias_restantes_hasta(prueba_hasta),
        "trial_days": config.get("trial_days", DIAS_PRUEBA_UNICA),
    }


def _leer_cache_licencia():
    datos = _leer_datos_de_archivo(ARCHIVO_CACHE)
    if datos and datos.get("tipo") == "cache_licencia":
        return datos
    return None


def _guardar_cache_licencia(estado):
    datos = {
        "tipo": "cache_licencia",
        "id_instalacion": estado["id_instalacion"],
        "estado": estado["estado"],
        "permitir_uso": estado["permitir_uso"],
        "detalle": estado["detalle"],
        "origen": estado["origen"],
        "fecha_opcional": estado.get("fecha_opcional"),
        "ultima_validacion": estado.get("ultima_validacion"),
        "ultima_validacion_exitosa": estado.get("ultima_validacion_exitosa"),
        "gracia_offline_hasta": estado.get("gracia_offline_hasta"),
    }
    _guardar_datos_en_archivo(ARCHIVO_CACHE, datos)


def obtener_id_instalacion():
    datos = _leer_datos_instalacion()
    id_instalacion = datos.get("id_instalacion") if datos else None
    if _es_uuid_valido(id_instalacion):
        if not isinstance(datos.get("notificacion_registro"), dict):
            datos = _actualizar_notificacion_registro(datos, "pendiente")
        _asegurar_notificacion_registro(id_instalacion, datos)
        return id_instalacion

    nuevo_id = str(uuid.uuid4())
    datos = {
        "tipo": "instalacion",
        "id_instalacion": nuevo_id,
        "creado_en": _formatear_fecha_hora(_ahora()),
        "notificacion_registro": {
            "estado": "pendiente",
            "actualizado_en": _formatear_fecha_hora(_ahora()),
        },
    }
    _guardar_datos_instalacion(datos)
    _asegurar_notificacion_registro(nuevo_id, datos)
    return nuevo_id


def cargar_configuracion_licencia():
    return {
        "google_sheet_csv_url": GOOGLE_SHEET_CSV_URL,
        "cache_horas": HORAS_CACHE_LICENCIA,
        "offline_grace_days": DIAS_GRACIA_SIN_INTERNET,
        "trial_days": DIAS_PRUEBA_UNICA,
        "timeout_segundos": TIMEOUT_VALIDACION,
    }


def _normalizar_fila_csv(fila):
    fila_normalizada = {}
    for clave, valor in (fila or {}).items():
        clave_normalizada = _normalizar_texto_min(str(clave).replace("\ufeff", ""))
        fila_normalizada[clave_normalizada] = _normalizar_texto(valor)
    return fila_normalizada


def _extraer_campo(fila, *candidatos):
    for candidato in candidatos:
        valor = fila.get(candidato)
        if valor:
            return valor
    return ""


def _normalizar_estado_remoto(valor):
    valor_normalizado = _normalizar_texto_min(valor)
    estados_activos = {"activa", "activo", "habilitada", "habilitado", "1", "si", "yes", "ok"}
    return "activa" if valor_normalizado in estados_activos else "bloqueada"


def _parsear_csv_licencias(contenido):
    lector = csv.DictReader(StringIO(contenido))
    if not lector.fieldnames:
        raise ValueError("El CSV publicado no tiene encabezados.")

    registros = []
    for fila in lector:
        fila_normalizada = _normalizar_fila_csv(fila)
        if not any(fila_normalizada.values()):
            continue

        id_instalacion = _extraer_campo(fila_normalizada, "id_instalacion", "installation_id", "id")
        if not id_instalacion:
            continue

        registros.append(
            {
                "id_instalacion": id_instalacion,
                "estado": _normalizar_estado_remoto(fila_normalizada.get("estado")),
                "fecha_opcional": _extraer_campo(
                    fila_normalizada,
                    "fecha_opcional",
                    "fecha",
                    "ultima_actualizacion",
                    "actualizado",
                ),
            }
        )

    return registros


def _url_consulta_sin_cache(url):
    partes = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(partes.query, keep_blank_values=True)
    query = [(clave, valor) for clave, valor in query if clave != "_ts"]
    query.append(("_ts", str(time.time_ns())))
    return urllib.parse.urlunsplit(
        (
            partes.scheme,
            partes.netloc,
            partes.path,
            urllib.parse.urlencode(query),
            partes.fragment,
        )
    )


def _consultar_licencias_remotas(config, intentos=1, pausa_segundos=0):
    ultimo_error = None
    ultimo_registro_exitoso = None

    for intento in range(max(1, intentos)):
        try:
            request = urllib.request.Request(
                _url_consulta_sin_cache(config["google_sheet_csv_url"]),
                headers={
                    "User-Agent": "KioscoApp-License/1.0",
                    "Cache-Control": "no-cache, no-store, max-age=0",
                    "Pragma": "no-cache",
                },
            )
            with urllib.request.urlopen(request, timeout=config["timeout_segundos"]) as respuesta:
                contenido = respuesta.read().decode("utf-8-sig")
            ultimo_registro_exitoso = _parsear_csv_licencias(contenido)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as error:
            ultimo_error = error

        if intento < max(1, intentos) - 1 and pausa_segundos > 0:
            time.sleep(pausa_segundos)

    if ultimo_registro_exitoso is not None:
        return ultimo_registro_exitoso

    if ultimo_error:
        raise ultimo_error
    raise OSError("No fue posible consultar la licencia remota.")


def _buscar_registro_licencia(registros, id_instalacion):
    coincidencia = None
    for registro in registros:
        if _normalizar_texto(registro.get("id_instalacion")) == id_instalacion:
            coincidencia = registro
    return coincidencia


def _cache_activa_vigente(cache, id_instalacion, config, forzar):
    if forzar or not cache:
        return False
    if cache.get("id_instalacion") != id_instalacion or cache.get("estado") != "activa":
        return False

    ultima_validacion = _parsear_fecha_hora(cache.get("ultima_validacion_exitosa"))
    if not ultima_validacion:
        return False

    limite_cache = ultima_validacion + timedelta(hours=config["cache_horas"])
    return _ahora() <= limite_cache


def _estado_desde_cache(cache, id_instalacion, config):
    detalle = (
        "Licencia activa desde cache local. "
        f"La app volvera a consultar online dentro de {config['cache_horas']} horas."
    )
    _marcar_licencia_activada(id_instalacion, cache.get("ultima_validacion_exitosa"))
    return _crear_estado(
        id_instalacion=id_instalacion,
        config=config,
        estado="activa",
        permitir_uso=True,
        detalle=detalle,
        origen="cache",
        fecha_opcional=cache.get("fecha_opcional"),
        ultima_validacion=cache.get("ultima_validacion"),
        ultima_validacion_exitosa=cache.get("ultima_validacion_exitosa"),
        gracia_offline_hasta=cache.get("gracia_offline_hasta"),
    )


def _estado_offline(cache, id_instalacion, config):
    if not cache:
        return None
    if cache.get("id_instalacion") != id_instalacion or cache.get("estado") != "activa":
        return None

    ultima_validacion_exitosa = _parsear_fecha_hora(cache.get("ultima_validacion_exitosa"))
    if not ultima_validacion_exitosa:
        return None

    gracia_hasta = ultima_validacion_exitosa + timedelta(days=config["offline_grace_days"])
    if _ahora() > gracia_hasta:
        return None

    detalle = (
        "No fue posible validar la licencia por internet. "
        f"Se permite uso temporal por hasta {config['offline_grace_days']} dias sin conexion."
    )
    _marcar_licencia_activada(id_instalacion, ultima_validacion_exitosa)
    return _crear_estado(
        id_instalacion=id_instalacion,
        config=config,
        estado="activa",
        permitir_uso=True,
        detalle=detalle,
        origen="gracia_offline",
        fecha_opcional=cache.get("fecha_opcional"),
        ultima_validacion=cache.get("ultima_validacion"),
        ultima_validacion_exitosa=ultima_validacion_exitosa,
        gracia_offline_hasta=gracia_hasta,
    )


def _estado_prueba_unica(id_instalacion, config, iniciar_si_falta=False):
    datos_instalacion = _leer_datos_instalacion()
    if not datos_instalacion or datos_instalacion.get("id_instalacion") != id_instalacion:
        return None
    if datos_instalacion.get("licencia_activada_en"):
        return None

    prueba = datos_instalacion.get("prueba_unica")
    if not isinstance(prueba, dict):
        prueba = {}

    inicio_prueba = _parsear_fecha_hora(prueba.get("iniciado_en"))
    prueba_hasta = _parsear_fecha_hora(prueba.get("vence_en"))
    dias_prueba = config.get("trial_days", DIAS_PRUEBA_UNICA)

    if not inicio_prueba or not prueba_hasta:
        if not iniciar_si_falta:
            return None

        ahora = _ahora()
        inicio_prueba = ahora
        prueba_hasta = ahora + timedelta(days=dias_prueba)
        datos_instalacion = dict(datos_instalacion)
        datos_instalacion["prueba_unica"] = {
            "iniciado_en": _formatear_fecha_hora(inicio_prueba),
            "vence_en": _formatear_fecha_hora(prueba_hasta),
            "consumida": True,
        }
        _guardar_datos_instalacion(datos_instalacion)

    if _ahora() <= prueba_hasta:
        detalle = (
            f"Prueba unica activa por {dias_prueba} dias. "
            f"Quedan {max(1, _dias_restantes_hasta(prueba_hasta))} dias disponibles."
        )
        return _crear_estado(
            id_instalacion=id_instalacion,
            config=config,
            estado="prueba",
            permitir_uso=True,
            detalle=detalle,
            origen="prueba",
            fecha_opcional=_formatear_fecha_hora(prueba_hasta),
            prueba_iniciada_en=inicio_prueba,
            prueba_hasta=prueba_hasta,
        )

    return _crear_estado(
        id_instalacion=id_instalacion,
        config=config,
        estado="prueba_vencida",
        permitir_uso=False,
        detalle=f"La prueba unica de {dias_prueba} dias ya vencio.",
        origen="prueba",
        fecha_opcional=_formatear_fecha_hora(prueba_hasta),
        prueba_iniciada_en=inicio_prueba,
        prueba_hasta=prueba_hasta,
    )


def validar_licencia(forzar=False):
    id_instalacion = obtener_id_instalacion()
    config = cargar_configuracion_licencia()
    cache = _leer_cache_licencia()

    if not config["google_sheet_csv_url"]:
        return _crear_estado(
            id_instalacion=id_instalacion,
            config=config,
            estado="sin_configuracion",
            permitir_uso=False,
            detalle="No se configuro la URL publica del Google Sheet para licencias.",
            origen="local",
        )

    if _cache_activa_vigente(cache, id_instalacion, config, forzar):
        return _estado_desde_cache(cache, id_instalacion, config)

    intentos_consulta = 1
    if forzar or config["cache_horas"] == 0:
        intentos_consulta = REINTENTOS_VALIDACION_ESTRICTA

    try:
        registros = _consultar_licencias_remotas(
            config,
            intentos=intentos_consulta,
            pausa_segundos=PAUSA_REINTENTO_VALIDACION if intentos_consulta > 1 else 0,
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        estado_offline = _estado_offline(cache, id_instalacion, config)
        if estado_offline:
            return estado_offline

        estado_prueba = _estado_prueba_unica(id_instalacion, config, iniciar_si_falta=True)
        if estado_prueba:
            return estado_prueba

        return _crear_estado(
            id_instalacion=id_instalacion,
            config=config,
            estado="sin_conexion",
            permitir_uso=False,
            detalle="No se pudo validar la licencia online y no hay cache activa utilizable.",
            origen="local",
        )

    registro = _buscar_registro_licencia(registros, id_instalacion)
    ahora = _ahora()

    if not registro:
        estado_prueba = _estado_prueba_unica(id_instalacion, config, iniciar_si_falta=True)
        if estado_prueba:
            return estado_prueba

        estado = _crear_estado(
            id_instalacion=id_instalacion,
            config=config,
            estado="no_encontrada",
            permitir_uso=False,
            detalle="El ID de instalacion no existe en la planilla de licencias.",
            origen="online",
            ultima_validacion=ahora,
        )
        _guardar_cache_licencia(estado)
        return estado

    if registro["estado"] != "activa":
        estado = _crear_estado(
            id_instalacion=id_instalacion,
            config=config,
            estado="bloqueada",
            permitir_uso=False,
            detalle="La licencia de esta instalacion esta bloqueada en la planilla.",
            origen="online",
            fecha_opcional=registro.get("fecha_opcional"),
            ultima_validacion=ahora,
        )
        _guardar_cache_licencia(estado)
        return estado

    gracia_hasta = ahora + timedelta(days=config["offline_grace_days"])
    estado = _crear_estado(
        id_instalacion=id_instalacion,
        config=config,
        estado="activa",
        permitir_uso=True,
        detalle="Licencia activa y validada online.",
        origen="online",
        fecha_opcional=registro.get("fecha_opcional"),
        ultima_validacion=ahora,
        ultima_validacion_exitosa=ahora,
        gracia_offline_hasta=gracia_hasta,
    )
    _marcar_licencia_activada(id_instalacion, ahora)
    _guardar_cache_licencia(estado)
    return estado


def estado_licencia(forzar=False):
    return validar_licencia(forzar=forzar)


def esta_activado():
    return validar_licencia()["permitir_uso"]


def describir_estado_licencia(estado=None):
    estado = estado or validar_licencia()

    if estado["estado"] == "activa" and estado["origen"] == "online":
        return "Licencia activa."

    if estado["estado"] == "activa" and estado["origen"] == "cache":
        return (
            "Licencia activa usando cache local. "
            f"Se revalida online cada {estado['cache_horas']} horas."
        )

    if estado["estado"] == "activa" and estado["origen"] == "gracia_offline":
        return (
            "Licencia activa de forma temporal por falta de internet. "
            f"Quedan {estado['dias_restantes_offline']} dias de gracia offline."
        )

    if estado["estado"] == "prueba":
        return (
            "Modo prueba activo. "
            f"Quedan {estado['dias_restantes_prueba']} dias de la prueba unica."
        )

    if estado["estado"] == "prueba_vencida":
        return (
            f"La prueba unica de {estado.get('trial_days', DIAS_PRUEBA_UNICA)} dias ya vencio. "
            "Envie el ID de instalacion para activar la app."
        )

    if estado["estado"] == "bloqueada":
        return "Licencia bloqueada. Contacte al administrador o revendedor."

    if estado["estado"] == "no_encontrada":
        return "Licencia no activa. Envie el ID de instalacion para habilitarla."

    if estado["estado"] == "sin_configuracion":
        return "Falta configurar la URL publica del backend de licencias."

    if estado["estado"] == "sin_conexion":
        return "No se pudo validar la licencia online y no hay gracia offline disponible."

    return estado.get("detalle") or "Estado de licencia desconocido."


def _crear_parser_argumentos():
    parser = argparse.ArgumentParser(description="Herramientas de licencia para KioscoApp.")
    parser.add_argument(
        "--id",
        action="store_true",
        help="Muestra el ID unico de la instalacion actual.",
    )
    parser.add_argument(
        "--estado",
        action="store_true",
        help="Valida online y muestra el estado actual de la licencia.",
    )
    return parser


def _mostrar_id_instalacion():
    log("ID de instalacion:", obtener_id_instalacion())


def _mostrar_estado():
    estado = validar_licencia(forzar=True)
    log(json.dumps(estado, indent=2, sort_keys=True))
    log(describir_estado_licencia(estado))


if __name__ == "__main__":
    argumentos = _crear_parser_argumentos().parse_args()
    if argumentos.id or not (argumentos.id or argumentos.estado):
        _mostrar_id_instalacion()
    if argumentos.estado or not (argumentos.id or argumentos.estado):
        _mostrar_estado()
