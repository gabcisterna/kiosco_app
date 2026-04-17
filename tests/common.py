import os
import shutil
import uuid
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from modules import clientes, debito, deudas, empleados, licencia, login, productos, reposiciones, ventas


@contextmanager
def isolated_data_env():
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_dir = os.path.join(workspace_root, "tests", f"_tmp_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    try:
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        rutas = {
            "clientes": os.path.join(data_dir, "clientes.json"),
            "debito": os.path.join(data_dir, "debito.json"),
            "deudas": os.path.join(data_dir, "deudas.json"),
            "empleados": os.path.join(data_dir, "empleados.json"),
            "productos": os.path.join(data_dir, "productos.json"),
            "productos_bajos": os.path.join(data_dir, "productos_bajos.json"),
            "registro_debitos": os.path.join(data_dir, "registro_debitos.json"),
            "registro_deudas": os.path.join(data_dir, "registro_deudas.json"),
            "registro_stock": os.path.join(data_dir, "registro_stock.json"),
            "turnos": os.path.join(data_dir, "turnos.json"),
            "ventas": os.path.join(data_dir, "ventas.json"),
            "instalacion": os.path.join(temp_dir, "install.bin"),
            "cache_licencia": os.path.join(temp_dir, "license_cache.bin"),
        }

        with ExitStack() as stack:
            stack.enter_context(patch.object(clientes, "RUTA_CLIENTES", rutas["clientes"]))
            stack.enter_context(patch.object(debito, "RUTA_DEBITO", rutas["debito"]))
            stack.enter_context(patch.object(debito, "RUTA_REGISTRO_DEBITOS", rutas["registro_debitos"]))
            stack.enter_context(patch.object(deudas, "RUTA_DEUDAS", rutas["deudas"]))
            stack.enter_context(patch.object(deudas, "RUTA_REGISTRO_DEUDAS", rutas["registro_deudas"]))
            stack.enter_context(patch.object(empleados, "RUTA_EMPLEADOS", rutas["empleados"]))
            stack.enter_context(patch.object(login, "RUTA_TURNOS", rutas["turnos"]))
            stack.enter_context(patch.object(productos, "RUTA_PRODUCTOS", rutas["productos"]))
            stack.enter_context(patch.object(productos, "RUTA_PRODUCTOS_BAJOS", rutas["productos_bajos"]))
            stack.enter_context(patch.object(reposiciones, "RUTA_REGISTRO_STOCK", rutas["registro_stock"]))
            stack.enter_context(patch.object(ventas, "RUTA_VENTAS", rutas["ventas"]))
            stack.enter_context(patch.object(licencia, "ARCHIVO_INSTALACION", rutas["instalacion"]))
            stack.enter_context(patch.object(licencia, "ARCHIVO_CACHE", rutas["cache_licencia"]))
            yield temp_dir, rutas
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
