import unittest
from unittest.mock import MagicMock, patch

from modules.productos import guardar_productos
from tests.common import isolated_data_env
from ui.pantalla_login import limpiar_ventana_principal
from ui.pantalla_principal import PantallaCaja


class DummyEntry:
    def __init__(self, value=""):
        self.value = value
        self.config_calls = []

    def get(self):
        return self.value

    def delete(self, start, end):
        self.value = ""

    def insert(self, index, value):
        self.value = value

    def config(self, **kwargs):
        self.config_calls.append(kwargs)


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


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class UIFlowTests(unittest.TestCase):
    def _crear_pantalla_panel_cliente(self, forma="efectivo", dni="", nombre="", visible_inicial=False):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla._widget_existe = lambda widget: True
        pantalla.forma_pago_var = DummyVar(forma)
        pantalla.entry_dni = DummyEntry(dni)
        pantalla.entry_nombre = DummyEntry(nombre)
        pantalla.label_dni = MagicMock()
        pantalla.label_nombre = MagicMock()
        pantalla.boton_cliente_toggle = MagicMock()
        pantalla.label_cliente_resumen = MagicMock()
        pantalla._actualizar_scroll_panel_derecho = MagicMock()
        pantalla._cliente_panel_expandido = False

        estado = {"visible": visible_inicial}
        pantalla._panel_cliente_visible = lambda: estado["visible"]
        pantalla._mostrar_panel_cliente = lambda: estado.__setitem__("visible", True)
        pantalla._ocultar_panel_cliente = lambda: estado.__setitem__("visible", False)

        return pantalla, estado

    def test_limpiar_ventana_principal_libera_callback_responsive(self):
        master = MagicMock()
        master.winfo_children.return_value = []
        pantalla_activa = MagicMock()
        master._pantalla_activa = pantalla_activa

        limpiar_ventana_principal(master)

        pantalla_activa.liberar_recursos.assert_called_once_with()
        master.unbind.assert_any_call("<Configure>")
        master.minsize.assert_called_once_with(1, 1)
        master.resizable.assert_called_with(True, True)

    def test_cerrar_sesion_vuelve_al_login_en_la_misma_ventana(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.master = MagicMock()
        pantalla.ir_a_login = MagicMock()

        with patch("ui.pantalla_principal.cerrar_sesion") as cerrar_sesion_mock:
            PantallaCaja.cerrar_sesion_y_volver_al_login(pantalla)

        cerrar_sesion_mock.assert_called_once_with()
        pantalla.ir_a_login.assert_called_once_with(pantalla.master)

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

    def test_salir_fullscreen_restaura_ventana_redimensionable(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.master = MagicMock()
        pantalla.master.winfo_width.return_value = 800
        pantalla.master.winfo_height.return_value = 600
        pantalla.master.winfo_screenwidth.return_value = 1920
        pantalla.master.winfo_screenheight.return_value = 1080
        pantalla._programar_layout_responsive = MagicMock()

        resultado = PantallaCaja._salir_fullscreen(pantalla)

        pantalla.master.attributes.assert_any_call("-fullscreen", False)
        pantalla.master.resizable.assert_called_with(True, True)
        pantalla.master.minsize.assert_called_with(980, 640)
        pantalla.master.geometry.assert_called_once()
        pantalla._programar_layout_responsive.assert_called_once_with()
        self.assertEqual(resultado, "break")

    def test_layout_acciones_pasa_a_columna_unica_con_ancho_chico(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla._widget_existe = lambda widget: True
        pantalla.botones_acciones_frame = MagicMock()
        pantalla.boton_ajuste = MagicMock()
        pantalla.boton_finalizar = MagicMock()
        pantalla.label_acciones_descripcion = MagicMock()

        PantallaCaja._aplicar_layout_acciones(pantalla, ancho_disponible=420)

        pantalla.boton_ajuste.grid.assert_called_with(row=0, column=0, sticky="ew", pady=(0, 10))
        pantalla.boton_finalizar.grid.assert_called_with(row=1, column=0, sticky="ew", pady=(10, 0))

    def test_layout_principal_actualiza_acciones_aunque_no_cambie_de_modo(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.master = MagicMock()
        pantalla.master.winfo_width.return_value = 1200
        pantalla.master.winfo_height.return_value = 780
        pantalla.master.winfo_screenwidth.return_value = 1920
        pantalla.master.winfo_screenheight.return_value = 1080
        pantalla.master._pantalla_activa = pantalla
        pantalla.izquierda_frame = MagicMock()
        pantalla.derecha_frame = MagicMock()
        pantalla._layout_actual = "vertical"
        pantalla._widget_existe = lambda widget: True
        pantalla._aplicar_compactacion_general = MagicMock()
        pantalla._aplicar_layout_acciones = MagicMock()
        pantalla._actualizar_scroll_panel_derecho = MagicMock()

        PantallaCaja._aplicar_layout_responsive(pantalla)

        pantalla._aplicar_compactacion_general.assert_called_once_with(1200, 780)
        pantalla._aplicar_layout_acciones.assert_called_once_with()
        pantalla._actualizar_scroll_panel_derecho.assert_called_once_with()

    def test_ajustar_panel_derecho_scrollable_sincroniza_ancho_y_layout(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla._widget_existe = lambda widget: True
        pantalla.derecha_canvas = MagicMock()
        pantalla._derecha_canvas_window = "window-id"
        pantalla._actualizar_scroll_panel_derecho = MagicMock()
        pantalla._aplicar_layout_acciones = MagicMock()

        evento = MagicMock()
        evento.width = 510

        PantallaCaja._ajustar_panel_derecho_scrollable(pantalla, evento)

        pantalla.derecha_canvas.itemconfigure.assert_called_once_with("window-id", width=510)
        pantalla._actualizar_scroll_panel_derecho.assert_called_once_with()
        pantalla._aplicar_layout_acciones.assert_called_once_with(510)

    def test_compacta_botones_de_acciones_si_falta_alto(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla._widget_existe = lambda widget: True
        pantalla.font_labels = ("Segoe UI", 12)
        pantalla.font_subtitulo = ("Segoe UI", 10)
        pantalla.boton_ajuste = MagicMock()
        pantalla.boton_finalizar = MagicMock()
        pantalla.label_acciones_titulo = MagicMock()
        pantalla.label_acciones_descripcion = MagicMock()
        pantalla.label_acciones_descripcion.winfo_manager.return_value = "pack"
        pantalla.botones_acciones_frame = MagicMock()

        PantallaCaja._aplicar_compactacion_acciones(pantalla, ancho_disponible=420, alto_disponible=620)

        pantalla.boton_ajuste.config.assert_any_call(text="Ajuste", font=("Segoe UI", 9, "bold"), padx=8, pady=5)
        pantalla.boton_finalizar.config.assert_any_call(text="Finalizar", font=("Segoe UI", 10, "bold"), padx=10, pady=6)
        pantalla.label_acciones_descripcion.pack_forget.assert_called_once_with()

    def test_panel_cliente_en_efectivo_queda_oculto_y_opcional(self):
        pantalla, estado = self._crear_pantalla_panel_cliente()

        PantallaCaja._actualizar_panel_cliente(pantalla)

        self.assertFalse(estado["visible"])
        pantalla.label_dni.config.assert_any_call(text="DNI del cliente (opcional):")
        pantalla.label_nombre.config.assert_any_call(text="Nombre del cliente (opcional):")
        pantalla.boton_cliente_toggle.config.assert_any_call(text="Agregar cliente opcional")

    def test_panel_cliente_en_deuda_se_muestra_si_faltan_datos(self):
        pantalla, estado = self._crear_pantalla_panel_cliente(forma="deuda")

        PantallaCaja._actualizar_panel_cliente(pantalla)

        self.assertTrue(estado["visible"])
        pantalla.label_dni.config.assert_any_call(text="DNI o referencia:")
        pantalla.label_nombre.config.assert_any_call(text="Nombre o alias:")
        pantalla.boton_cliente_toggle.config.assert_any_call(text="Completar cliente")

    def test_cliente_requerido_no_se_oculta_mientras_se_completa(self):
        pantalla, estado = self._crear_pantalla_panel_cliente(
            forma="debito",
            nombre="Ana",
            visible_inicial=True,
        )
        pantalla.autocompletar_cliente = MagicMock()

        PantallaCaja._on_cliente_editado(pantalla, event=MagicMock())

        self.assertTrue(estado["visible"])
        pantalla.autocompletar_cliente.assert_called_once()
        pantalla.boton_cliente_toggle.config.assert_any_call(text="Ocultar cliente")

    def test_resuelve_modo_compacto_para_notebook_14_pulgadas(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)

        modo = PantallaCaja._resolver_modo_compacto_general(pantalla, 1366, 768)

        self.assertEqual(modo, "compacto")

    def test_layout_principal_usa_horizontal_en_ancho_notebook(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.master = MagicMock()
        pantalla.master.winfo_width.return_value = 1366
        pantalla.master.winfo_height.return_value = 768
        pantalla.master.winfo_screenwidth.return_value = 1366
        pantalla.master.winfo_screenheight.return_value = 768
        pantalla.master._pantalla_activa = pantalla
        pantalla.izquierda_frame = MagicMock()
        pantalla.derecha_frame = MagicMock()
        pantalla._layout_actual = None
        pantalla._widget_existe = lambda widget: True
        pantalla._modo_compacto_general = "compacto"
        pantalla._aplicar_compactacion_general = MagicMock()
        pantalla._aplicar_layout_acciones = MagicMock()
        pantalla._actualizar_scroll_panel_derecho = MagicMock()

        PantallaCaja._aplicar_layout_responsive(pantalla)

        pantalla.izquierda_frame.pack.assert_called_with(side="left", fill="both", expand=True)
        pantalla.derecha_frame.pack.assert_called_with(side="right", fill="both", expand=True, padx=(14, 0))

    def test_texto_aviso_prueba_se_acorta_en_modo_compacto(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.estado_licencia = {"dias_restantes_prueba": 5}
        pantalla._modo_compacto_general = "normal"

        texto = PantallaCaja._texto_aviso_licencia(pantalla, "compacto")

        self.assertEqual(texto, "Quedan 5 dias de prueba.")

    def test_menu_carrito_selecciona_item_y_abre_acciones(self):
        pantalla = PantallaCaja.__new__(PantallaCaja)
        pantalla.carrito = [{"id": 1, "nombre": "Producto"}]
        pantalla._widget_existe = lambda widget: True
        pantalla.lista_productos = MagicMock()
        pantalla.lista_productos.nearest.return_value = 0
        pantalla.menu_carrito_acciones = MagicMock()

        evento = MagicMock()
        evento.y = 12
        evento.x_root = 100
        evento.y_root = 150

        resultado = PantallaCaja._mostrar_menu_carrito(pantalla, evento)

        pantalla.lista_productos.selection_clear.assert_called_once()
        pantalla.lista_productos.selection_set.assert_called_once_with(0)
        pantalla.menu_carrito_acciones.tk_popup.assert_called_once_with(100, 150)
        self.assertEqual(resultado, "break")
