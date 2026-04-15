import tkinter as tk
from tkinter import messagebox, simpledialog, font, ttk
from modules.clientes import buscar_clientes_por_texto, resolver_cliente_para_venta
from modules.empleados import obtener_empleado_activo, obtener_permisos_empleado
from modules.login import cerrar_sesion
from modules.productos import (
    buscar_producto,
    buscar_productos_por_texto,
    describir_precio_producto,
    formatear_cantidad,
    listar_productos_con_stock_bajo,
    obtener_unidad_medida,
    parsear_cantidad_para_producto,
    producto_se_vende_por_kilo,
)
from modules.ventas import registrar_venta
from ui.pantalla_productos import PantallaProductos
from ui.pantalla_ventas import PantallaVentas
from ui.pantalla_deudas import PantallaDeudas
from ui.pantalla_registros import PantallaRegistros
from ui.pantalla_debito import PantallaDebitos
from ui.pantalla_clientes import PantallaClientes
from ui.pantalla_empleados import PantallaEmpleados
from ui.pantalla_reportes import PantallaReportes

class PantallaCaja:
    def __init__(self, master, ir_a_login):
        self.master = master
        self.ir_a_login = ir_a_login
        self.master._pantalla_activa = self
        self.master.title("Caja y Ventas - Kiosco App")
        self.estado_licencia = getattr(self.master, "_estado_licencia", None) or {}
        self.color_fondo = "#edf3f8"
        self.color_tarjeta = "#ffffff"
        self.color_borde = "#d8e2ec"
        self.color_texto = "#1f2937"
        self.color_secundario = "#5b6470"
        self.color_primario = "#0f4c81"
        self.color_primario_hover = "#0b3d68"
        self.color_exito = "#1f8f5f"
        self.color_exito_hover = "#18714b"
        self.color_peligro = "#c2413b"
        self.color_peligro_hover = "#9f312c"
        self.color_alerta = "#d97706"
        self.color_alerta_hover = "#b65f05"
        self.master.configure(bg=self.color_fondo)
        self.master.resizable(True, True)
        self.master.minsize(980, 640)
        self.master.attributes('-fullscreen', True)
        self.master.bind("<Escape>", self._salir_fullscreen)
        self.master.bind("<Return>", self.agregar_producto)
        self.master.bind("<F2>", lambda event: self.confirmar_venta())
        self.ajuste_tipo_var = tk.StringVar(value="ninguno")       # ninguno / descuento / interes
        self.ajuste_modo_var = tk.StringVar(value="porcentaje")    # porcentaje / monto
        self.ajuste_valor_var = tk.StringVar(value="")
        self.ajuste_resumen_var = tk.StringVar(value="Subtotal: $0.00 | Sin ajuste aplicado")
        self.ajuste_info_label = None
        self.boton_ajuste = None
        self.ventana_ajuste = None
        self._layout_actual = None
        self._layout_job = None
        self._acciones_layout_actual = None
        self._acciones_modo_altura = "normal"
        self.botones_acciones_frame = None
        self.boton_modificar = None
        self.boton_eliminar = None
        self.boton_finalizar = None
        self.label_acciones_descripcion = None
        self.label_acciones_titulo = None
        self.barra_superior = None
        self.label_barra_titulo = None
        self.label_barra_subtitulo = None
        self.botones_admin_frame = None
        self.botones_admin = []
        self.boton_cerrar_sesion = None
        self.tarjeta_entrada_producto = None
        self.entrada_producto_frame = None
        self.label_entrada_producto_titulo = None
        self.label_entrada_producto_descripcion = None
        self.label_buscar_producto = None
        self.label_cantidad_producto = None
        self.boton_agregar_producto = None
        self.encabezado_carrito = None
        self.label_carrito_titulo = None
        self.label_ayuda_carrito = None
        self.menu_carrito_acciones = None
        self.label_cliente_pago_titulo = None
        self.forma_frame = None
        self.fila_pago_frame = None
        self.label_resumen_pago_titulo = None
        self.resumen_frame = None
        self.aviso_licencia_frame = None
        self.label_aviso_licencia = None
        self.label_aviso_licencia_detalle = None
        self._modo_compacto_general = "normal"
        self.cliente_frame = None
        self.cliente_toggle_frame = None
        self.boton_cliente_toggle = None
        self.label_cliente_resumen = None
        self._cliente_panel_expandido = False
        self.derecha_canvas = None
        self.derecha_scrollbar = None
        self.derecha_scroll_content = None
        self._derecha_canvas_window = None
        self.popup_sugerencias = None
        self.lista_sugerencias = None

        self.carrito = []
        self._sugerencias_producto_actuales = []
        self.empleado = obtener_empleado_activo()
        self.permisos = obtener_permisos_empleado(self.empleado)
        self.label_resumen_carrito = None
        self.actualizar_total = self._actualizar_total_responsive
        self.limpiar_despues_de_venta = self._limpiar_despues_de_venta_responsive

        # Fuentes
        self.font_lista = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_labels = font.Font(family="Segoe UI", size=12)
        self.font_pequena = font.Font(family="Segoe UI", size=10)
        self.font_busqueda = font.Font(family="Segoe UI", size=17, weight="bold")
        self.font_sugerencias = font.Font(family="Segoe UI", size=12)
        self.font_titulo = font.Font(family="Segoe UI", size=18, weight="bold")
        self.font_subtitulo = font.Font(family="Segoe UI", size=10)
        self._configurar_estilos()

        self.main_frame = tk.Frame(master, bg=self.color_fondo, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.crear_barra_superior_completa(self.main_frame)

        if not self.permisos.get("usar_caja"):
            self.crear_panel_sin_caja(self.main_frame)
            return

        self.contenido_frame = tk.Frame(self.main_frame, bg=self.color_fondo)
        self.contenido_frame.pack(fill=tk.BOTH, expand=True)

        self.izquierda_frame = tk.Frame(self.contenido_frame, bg=self.color_fondo)
        self.derecha_frame = tk.Frame(self.contenido_frame, bg=self.color_fondo)
        self._crear_panel_derecho_scrollable()

        # Parte izquierda
        self.crear_lista_productos(self.izquierda_frame)
        self.crear_entrada_producto(self.izquierda_frame)
        self.mostrar_productos_stock_bajo(self.izquierda_frame)
        # Eliminamos la creación de botones aquí:
        # self.crear_botones_y_finalizar(self.izquierda_frame)

        # Parte derecha
        self.crear_aviso_licencia(self.derecha_scroll_content)
        self.crear_info_pago(self.derecha_scroll_content)
        self.crear_total_y_vuelto_responsive(self.derecha_scroll_content)

        # Ahora los botones van en la derecha, debajo del total y vuelto:
        self.crear_botones_y_finalizar(self.derecha_scroll_content)
        self.actualizar_lista()
        self.actualizar_total()
        self.master.bind("<Configure>", self._programar_layout_responsive)
        self.master.after_idle(self._aplicar_layout_responsive)

    def _configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Caja.Treeview",
            background="white",
            fieldbackground="white",
            foreground=self.color_texto,
            rowheight=28,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Caja.Treeview.Heading",
            background="#e7eef6",
            foreground=self.color_texto,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Caja.Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", self.color_texto)],
        )

    def _crear_tarjeta(self, parent, pady=(0, 14), padx=0):
        tarjeta = tk.Frame(
            parent,
            bg=self.color_tarjeta,
            bd=1,
            relief="solid",
            highlightthickness=0,
        )
        tarjeta._pack_config = {"fill": tk.BOTH, "expand": False, "padx": padx, "pady": pady}
        return tarjeta

    def _resolver_modo_compacto_general(self, ancho_disponible=0, alto_disponible=0):
        if (alto_disponible and alto_disponible < 700) or (ancho_disponible and ancho_disponible < 1180):
            return "ultra"
        if (alto_disponible and alto_disponible < 820) or (ancho_disponible and ancho_disponible < 1380):
            return "compacto"
        return "normal"

    def _texto_aviso_licencia(self, modo=None):
        modo = modo or self._modo_compacto_general
        dias = max(1, int((self.estado_licencia or {}).get("dias_restantes_prueba") or 0))

        if modo == "ultra":
            return f"{dias} dias restantes."
        if modo == "compacto":
            return f"Quedan {dias} dias de prueba."
        return f"Quedan {dias} dias de prueba. La app funciona normal mientras tanto."

    def crear_aviso_licencia(self, frame):
        if (self.estado_licencia or {}).get("estado") != "prueba":
            return

        self.aviso_licencia_frame = tk.Frame(
            frame,
            bg="#fff4db",
            bd=1,
            relief="solid",
            highlightthickness=0,
            padx=12,
            pady=10,
        )
        self.aviso_licencia_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.label_aviso_licencia = tk.Label(
            self.aviso_licencia_frame,
            text="Prueba activa",
            bg="#fff4db",
            fg="#9a6700",
            font=("Segoe UI", 11, "bold"),
        )
        self.label_aviso_licencia.pack(anchor="w")

        self.label_aviso_licencia_detalle = tk.Label(
            self.aviso_licencia_frame,
            text=self._texto_aviso_licencia(),
            bg="#fff4db",
            fg="#7c5b12",
            font=("Segoe UI", 10),
            justify="left",
            wraplength=420,
        )
        self.label_aviso_licencia_detalle.pack(anchor="w", pady=(2, 0))

    def _widget_existe(self, widget):
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False

    def _crear_panel_derecho_scrollable(self):
        self.derecha_canvas = tk.Canvas(
            self.derecha_frame,
            bg=self.color_fondo,
            highlightthickness=0,
            bd=0,
        )
        self.derecha_scrollbar = ttk.Scrollbar(
            self.derecha_frame,
            orient="vertical",
            command=self.derecha_canvas.yview,
        )
        self.derecha_canvas.configure(yscrollcommand=self.derecha_scrollbar.set)

        self.derecha_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.derecha_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.derecha_scroll_content = tk.Frame(self.derecha_canvas, bg=self.color_fondo)
        self._derecha_canvas_window = self.derecha_canvas.create_window(
            (0, 0),
            window=self.derecha_scroll_content,
            anchor="nw",
        )

        self.derecha_scroll_content.bind("<Configure>", self._actualizar_scroll_panel_derecho)
        self.derecha_canvas.bind("<Configure>", self._ajustar_panel_derecho_scrollable)

    def _actualizar_scroll_panel_derecho(self, event=None):
        if not self._widget_existe(self.derecha_canvas):
            return
        try:
            self.derecha_canvas.configure(scrollregion=self.derecha_canvas.bbox("all"))
        except tk.TclError:
            return

    def _ajustar_panel_derecho_scrollable(self, event=None):
        if not self._widget_existe(self.derecha_canvas):
            return
        if self._derecha_canvas_window is None:
            return

        ancho = 0
        if event is not None:
            ancho = int(getattr(event, "width", 0) or 0)
        if not ancho:
            try:
                ancho = self.derecha_canvas.winfo_width()
            except tk.TclError:
                ancho = 0

        if not ancho:
            return

        try:
            self.derecha_canvas.itemconfigure(self._derecha_canvas_window, width=ancho)
        except tk.TclError:
            return

        self._actualizar_scroll_panel_derecho()
        self._aplicar_layout_acciones(ancho)

    def _aplicar_compactacion_general(self, ancho_disponible=None, alto_disponible=None):
        ancho_disponible = int(ancho_disponible or 0)
        alto_disponible = int(alto_disponible or 0)
        modo = self._resolver_modo_compacto_general(ancho_disponible, alto_disponible)
        self._modo_compacto_general = modo

        estilos = {
            "normal": {
                "main_padx": 20,
                "main_pady": 20,
                "barra_padx": 20,
                "barra_pady": 14,
                "barra_titulo_font": ("Segoe UI", 18, "bold"),
                "barra_subtitulo_font": ("Segoe UI", 10),
                "barra_boton_font": ("Segoe UI", 10, "bold"),
                "barra_boton_padx": 14,
                "barra_boton_pady": 7,
                "cerrar_padx": 14,
                "cerrar_pady": 8,
                "titulo_seccion_font": ("Segoe UI", 16, "bold"),
                "subtitulo_font": ("Segoe UI", 10),
                "entrada_frame_padx": 18,
                "entrada_frame_pady": 16,
                "campo_label_font": ("Segoe UI", 13, "bold"),
                "entrada_busqueda_font": ("Segoe UI", 17, "bold"),
                "entrada_cantidad_font": ("Segoe UI", 15, "bold"),
                "sugerencias_font": self.font_sugerencias,
                "sugerencias_altura": 7,
                "lista_font": self.font_lista,
                "stock_width": 300,
                "forma_font": self.font_pequena,
                "forma_padx": 10,
                "forma_pady": 5,
                "toggle_font": self.font_pequena,
                "toggle_padx": 12,
                "toggle_pady": 6,
                "toggle_wrap": 280,
                "cliente_padx": 12,
                "cliente_pady": 12,
                "cliente_entry_font": self.font_labels,
                "cliente_entry_dni_width": 20,
                "cliente_entry_nombre_width": 25,
                "cliente_sugerencias_altura": 4,
                "cliente_sugerencias_font": self.font_pequena,
                "resumen_padx": 12,
                "resumen_pady": 12,
                "total_font": ("Segoe UI", 28, "bold"),
                "vuelto_font": ("Segoe UI", 20),
                "ajuste_font": ("Segoe UI", 10),
                "aviso_titulo_font": ("Segoe UI", 11, "bold"),
                "aviso_detalle_font": ("Segoe UI", 10),
                "aviso_padx": 12,
                "aviso_pady": 10,
            },
            "compacto": {
                "main_padx": 14,
                "main_pady": 14,
                "barra_padx": 16,
                "barra_pady": 10,
                "barra_titulo_font": ("Segoe UI", 16, "bold"),
                "barra_subtitulo_font": ("Segoe UI", 9),
                "barra_boton_font": ("Segoe UI", 9, "bold"),
                "barra_boton_padx": 10,
                "barra_boton_pady": 6,
                "cerrar_padx": 10,
                "cerrar_pady": 6,
                "titulo_seccion_font": ("Segoe UI", 15, "bold"),
                "subtitulo_font": ("Segoe UI", 9),
                "entrada_frame_padx": 14,
                "entrada_frame_pady": 12,
                "campo_label_font": ("Segoe UI", 12, "bold"),
                "entrada_busqueda_font": ("Segoe UI", 15, "bold"),
                "entrada_cantidad_font": ("Segoe UI", 13, "bold"),
                "sugerencias_font": ("Segoe UI", 11),
                "sugerencias_altura": 5,
                "lista_font": ("Segoe UI", 13, "bold"),
                "stock_width": 260,
                "forma_font": ("Segoe UI", 9),
                "forma_padx": 8,
                "forma_pady": 4,
                "toggle_font": ("Segoe UI", 9),
                "toggle_padx": 10,
                "toggle_pady": 5,
                "toggle_wrap": 230,
                "cliente_padx": 10,
                "cliente_pady": 10,
                "cliente_entry_font": ("Segoe UI", 11),
                "cliente_entry_dni_width": 18,
                "cliente_entry_nombre_width": 22,
                "cliente_sugerencias_altura": 3,
                "cliente_sugerencias_font": ("Segoe UI", 9),
                "resumen_padx": 10,
                "resumen_pady": 10,
                "total_font": ("Segoe UI", 24, "bold"),
                "vuelto_font": ("Segoe UI", 17),
                "ajuste_font": ("Segoe UI", 9),
                "aviso_titulo_font": ("Segoe UI", 10, "bold"),
                "aviso_detalle_font": ("Segoe UI", 9),
                "aviso_padx": 10,
                "aviso_pady": 8,
            },
            "ultra": {
                "main_padx": 10,
                "main_pady": 10,
                "barra_padx": 12,
                "barra_pady": 8,
                "barra_titulo_font": ("Segoe UI", 15, "bold"),
                "barra_subtitulo_font": ("Segoe UI", 9),
                "barra_boton_font": ("Segoe UI", 9, "bold"),
                "barra_boton_padx": 8,
                "barra_boton_pady": 5,
                "cerrar_padx": 8,
                "cerrar_pady": 5,
                "titulo_seccion_font": ("Segoe UI", 14, "bold"),
                "subtitulo_font": ("Segoe UI", 8),
                "entrada_frame_padx": 12,
                "entrada_frame_pady": 10,
                "campo_label_font": ("Segoe UI", 11, "bold"),
                "entrada_busqueda_font": ("Segoe UI", 14, "bold"),
                "entrada_cantidad_font": ("Segoe UI", 12, "bold"),
                "sugerencias_font": ("Segoe UI", 10),
                "sugerencias_altura": 4,
                "lista_font": ("Segoe UI", 12, "bold"),
                "stock_width": 220,
                "forma_font": ("Segoe UI", 8),
                "forma_padx": 6,
                "forma_pady": 4,
                "toggle_font": ("Segoe UI", 8),
                "toggle_padx": 8,
                "toggle_pady": 4,
                "toggle_wrap": 200,
                "cliente_padx": 8,
                "cliente_pady": 8,
                "cliente_entry_font": ("Segoe UI", 10),
                "cliente_entry_dni_width": 16,
                "cliente_entry_nombre_width": 20,
                "cliente_sugerencias_altura": 3,
                "cliente_sugerencias_font": ("Segoe UI", 8),
                "resumen_padx": 8,
                "resumen_pady": 8,
                "total_font": ("Segoe UI", 21, "bold"),
                "vuelto_font": ("Segoe UI", 15),
                "ajuste_font": ("Segoe UI", 8),
                "aviso_titulo_font": ("Segoe UI", 9, "bold"),
                "aviso_detalle_font": ("Segoe UI", 8),
                "aviso_padx": 8,
                "aviso_pady": 6,
            },
        }
        estilo = estilos[modo]

        if self._widget_existe(self.main_frame):
            self.main_frame.config(padx=estilo["main_padx"], pady=estilo["main_pady"])

        if self._widget_existe(self.barra_superior):
            self.barra_superior.config(padx=estilo["barra_padx"], pady=estilo["barra_pady"])
        if self._widget_existe(self.label_barra_titulo):
            self.label_barra_titulo.config(font=estilo["barra_titulo_font"])
        if self._widget_existe(self.label_barra_subtitulo):
            self.label_barra_subtitulo.config(font=estilo["barra_subtitulo_font"])
        for boton in self.botones_admin:
            if self._widget_existe(boton):
                boton.config(
                    font=estilo["barra_boton_font"],
                    padx=estilo["barra_boton_padx"],
                    pady=estilo["barra_boton_pady"],
                )
        if self._widget_existe(self.boton_cerrar_sesion):
            self.boton_cerrar_sesion.config(
                font=estilo["barra_boton_font"],
                padx=estilo["cerrar_padx"],
                pady=estilo["cerrar_pady"],
            )

        if self._widget_existe(self.entrada_producto_frame):
            self.entrada_producto_frame.config(
                padx=estilo["entrada_frame_padx"],
                pady=estilo["entrada_frame_pady"],
            )
        if self._widget_existe(self.label_entrada_producto_titulo):
            self.label_entrada_producto_titulo.config(font=estilo["titulo_seccion_font"])
        if self._widget_existe(self.label_entrada_producto_descripcion):
            self.label_entrada_producto_descripcion.config(font=estilo["subtitulo_font"])
        if self._widget_existe(self.label_buscar_producto):
            self.label_buscar_producto.config(font=estilo["campo_label_font"])
        if self._widget_existe(self.label_cantidad_producto):
            self.label_cantidad_producto.config(font=estilo["campo_label_font"])
        if self._widget_existe(self.entrada_id):
            self.entrada_id.config(font=estilo["entrada_busqueda_font"])
        if self._widget_existe(self.entrada_cantidad):
            self.entrada_cantidad.config(font=estilo["entrada_cantidad_font"])
        if self._widget_existe(self.boton_agregar_producto):
            self.boton_agregar_producto.config(
                font=estilo["campo_label_font"],
                padx=estilo["barra_boton_padx"] + 4,
                pady=estilo["barra_boton_pady"] + 2,
            )

        if self._widget_existe(self.encabezado_carrito):
            self.encabezado_carrito.config(
                padx=estilo["entrada_frame_padx"] - 2,
                pady=estilo["entrada_frame_pady"] - 2,
            )
        if self._widget_existe(self.label_carrito_titulo):
            self.label_carrito_titulo.config(font=estilo["titulo_seccion_font"])
        if self._widget_existe(self.label_resumen_carrito):
            self.label_resumen_carrito.config(font=estilo["subtitulo_font"])
        if self._widget_existe(self.label_ayuda_carrito):
            self.label_ayuda_carrito.config(font=estilo["subtitulo_font"])
        if self._widget_existe(self.lista_productos):
            self.lista_productos.config(font=estilo["lista_font"])
        if self._widget_existe(self.stock_bajo_frame):
            self.stock_bajo_frame.config(width=estilo["stock_width"])

        if self._widget_existe(self.aviso_licencia_frame):
            self.aviso_licencia_frame.config(padx=estilo["aviso_padx"], pady=estilo["aviso_pady"])
        if self._widget_existe(self.label_aviso_licencia):
            self.label_aviso_licencia.config(font=estilo["aviso_titulo_font"])
        if self._widget_existe(self.label_aviso_licencia_detalle):
            wraplength = max(int((ancho_disponible or 420) * 0.28), 180)
            self.label_aviso_licencia_detalle.config(
                text=self._texto_aviso_licencia(modo),
                font=estilo["aviso_detalle_font"],
                wraplength=wraplength,
            )

        if self._widget_existe(self.label_cliente_pago_titulo):
            self.label_cliente_pago_titulo.config(font=estilo["titulo_seccion_font"])
        if self._widget_existe(self.forma_frame):
            self.forma_frame.config(padx=estilo["cliente_padx"], pady=estilo["cliente_pady"])
        for boton in getattr(self, "botones_pago", {}).values():
            if self._widget_existe(boton):
                boton.config(
                    font=estilo["forma_font"],
                    padx=estilo["forma_padx"],
                    pady=estilo["forma_pady"],
                )
        if self._widget_existe(self.label_pago):
            self.label_pago.config(font=estilo["toggle_font"])
        if self._widget_existe(self.entry_pago):
            self.entry_pago.config(font=estilo["cliente_entry_font"], width=max(8, estilo["cliente_entry_dni_width"] - 8))
        if self._widget_existe(self.boton_cliente_toggle):
            self.boton_cliente_toggle.config(
                font=estilo["toggle_font"],
                padx=estilo["toggle_padx"],
                pady=estilo["toggle_pady"],
            )
        if self._widget_existe(self.label_cliente_resumen):
            self.label_cliente_resumen.config(
                font=estilo["toggle_font"],
                wraplength=estilo["toggle_wrap"],
            )
        if self._widget_existe(self.cliente_frame):
            self.cliente_frame.config(padx=estilo["cliente_padx"], pady=estilo["cliente_pady"])
        if self._widget_existe(self.label_dni):
            self.label_dni.config(font=estilo["toggle_font"])
        if self._widget_existe(self.label_nombre):
            self.label_nombre.config(font=estilo["toggle_font"])
        if self._widget_existe(self.entry_dni):
            self.entry_dni.config(
                font=estilo["cliente_entry_font"],
                width=estilo["cliente_entry_dni_width"],
            )
        if self._widget_existe(self.entry_nombre):
            self.entry_nombre.config(
                font=estilo["cliente_entry_font"],
                width=estilo["cliente_entry_nombre_width"],
            )
        if self._widget_existe(self.lista_clientes_sugeridos):
            self.lista_clientes_sugeridos.config(
                font=estilo["cliente_sugerencias_font"],
                height=estilo["cliente_sugerencias_altura"],
            )

        if self._widget_existe(self.label_resumen_pago_titulo):
            self.label_resumen_pago_titulo.config(font=estilo["titulo_seccion_font"])
        if self._widget_existe(self.resumen_frame):
            self.resumen_frame.config(padx=estilo["resumen_padx"], pady=estilo["resumen_pady"])
        if self._widget_existe(self.total_label):
            self.total_label.config(font=estilo["total_font"])
        if self._widget_existe(self.vuelto_label):
            self.vuelto_label.config(font=estilo["vuelto_font"])
        if self._widget_existe(self.ajuste_info_label):
            self.ajuste_info_label.config(
                font=estilo["ajuste_font"],
                wraplength=max(int((ancho_disponible or 420) * 0.3), 220),
            )

        self._aplicar_layout_busqueda_producto(ancho_disponible)

    def _aplicar_layout_busqueda_producto(self, ancho_disponible=None):
        widgets = [
            self.entrada_producto_frame,
            self.label_buscar_producto,
            self.entrada_id,
            self.label_cantidad_producto,
            self.entrada_cantidad,
            self.boton_agregar_producto,
        ]
        if not all(self._widget_existe(widget) for widget in widgets):
            return

        compacto = (
            getattr(self, "_modo_compacto_general", "normal") != "normal"
            or (ancho_disponible and int(ancho_disponible) < 1400)
        )

        for widget in [
            self.label_buscar_producto,
            self.entrada_id,
            self.label_cantidad_producto,
            self.entrada_cantidad,
            self.boton_agregar_producto,
        ]:
            widget.grid_forget()

        if compacto:
            self.label_buscar_producto.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
            self.entrada_id.grid(row=2, column=1, columnspan=4, sticky="ew", padx=(0, 0), ipady=6)
            self.label_cantidad_producto.grid(row=4, column=0, sticky="w", padx=(0, 8))
            self.entrada_cantidad.grid(row=4, column=1, sticky="w", padx=(0, 12), ipady=6)
            self.boton_agregar_producto.grid(row=4, column=4, sticky="e")
        else:
            self.label_buscar_producto.grid(row=2, column=0, sticky="w", padx=(0, 8))
            self.entrada_id.grid(row=2, column=1, padx=(0, 20), sticky="ew", ipady=6)
            self.label_cantidad_producto.grid(row=2, column=2, sticky="w", padx=(0, 8))
            self.entrada_cantidad.grid(row=2, column=3, padx=(0, 20), ipady=6)
            self.boton_agregar_producto.grid(row=2, column=4)


    def _aplicar_compactacion_acciones(self, ancho_disponible=None, alto_disponible=None):
        widgets = [
            self.boton_ajuste,
            self.boton_finalizar,
        ]
        if not all(self._widget_existe(widget) for widget in widgets):
            return

        if alto_disponible is None:
            alto_disponible = 0
            try:
                if self.derecha_canvas:
                    alto_disponible = self.derecha_canvas.winfo_height()
            except tk.TclError:
                alto_disponible = 0
            except AttributeError:
                alto_disponible = 0

            if not alto_disponible:
                try:
                    if self.master:
                        alto_disponible = self.master.winfo_height()
                except tk.TclError:
                    alto_disponible = 0
                except AttributeError:
                    alto_disponible = 0

        if alto_disponible and alto_disponible < 660:
            modo = "ultra"
        elif alto_disponible and alto_disponible < 760:
            modo = "compacto"
        else:
            modo = "normal"

        self._acciones_modo_altura = modo

        font_labels = getattr(self, "font_labels", ("Segoe UI", 12))
        font_subtitulo = getattr(self, "font_subtitulo", ("Segoe UI", 10))

        estilos = {
            "normal": {
                "texto_ajuste": "Agregar descuento / interes",
                "texto_finalizar": "Finalizar venta (F2)",
                "font": font_labels,
                "final_font": ("Segoe UI", 12, "bold"),
                "padx": 15,
                "pady": 9,
                "final_padx": 20,
                "final_pady": 10,
                "descripcion": "Ajusta el total aca. Para productos usa el carrito.",
                "descripcion_font": font_subtitulo,
                "mostrar_descripcion": True,
                "titulo_font": ("Segoe UI", 16, "bold"),
            },
            "compacto": {
                "texto_ajuste": "Descuento / interes",
                "texto_finalizar": "Finalizar (F2)",
                "font": ("Segoe UI", 10, "bold"),
                "final_font": ("Segoe UI", 11, "bold"),
                "padx": 10,
                "pady": 7,
                "final_padx": 12,
                "final_pady": 8,
                "descripcion": "Ajusta el total o finaliza la venta.",
                "descripcion_font": ("Segoe UI", 9),
                "mostrar_descripcion": True,
                "titulo_font": ("Segoe UI", 15, "bold"),
            },
            "ultra": {
                "texto_ajuste": "Ajuste",
                "texto_finalizar": "Finalizar",
                "font": ("Segoe UI", 9, "bold"),
                "final_font": ("Segoe UI", 10, "bold"),
                "padx": 8,
                "pady": 5,
                "final_padx": 10,
                "final_pady": 6,
                "descripcion": "Ajuste y cierre rapido.",
                "descripcion_font": ("Segoe UI", 8),
                "mostrar_descripcion": False,
                "titulo_font": ("Segoe UI", 14, "bold"),
            },
        }
        estilo = estilos[modo]

        self.boton_ajuste.config(
            text=estilo["texto_ajuste"],
            font=estilo["font"],
            padx=estilo["padx"],
            pady=estilo["pady"],
        )
        self.boton_finalizar.config(
            text=estilo["texto_finalizar"],
            font=estilo["final_font"],
            padx=estilo["final_padx"],
            pady=estilo["final_pady"],
        )

        label_titulo = getattr(self, "label_acciones_titulo", None)
        if label_titulo and self._widget_existe(label_titulo):
            label_titulo.config(font=estilo["titulo_font"])

        if self.label_acciones_descripcion and self._widget_existe(self.label_acciones_descripcion):
            wraplength = max(int((ancho_disponible or 360)) - 40, 220)
            self.label_acciones_descripcion.config(
                text=estilo["descripcion"],
                font=estilo["descripcion_font"],
                wraplength=wraplength,
                justify="left",
            )

            try:
                manager = self.label_acciones_descripcion.winfo_manager()
            except tk.TclError:
                manager = ""

            if estilo["mostrar_descripcion"]:
                if not manager:
                    self.label_acciones_descripcion.pack(anchor="w", padx=16, before=self.botones_acciones_frame)
            elif manager:
                self.label_acciones_descripcion.pack_forget()

    def liberar_recursos(self):
        if getattr(self, "_layout_job", None):
            try:
                self.master.after_cancel(self._layout_job)
            except tk.TclError:
                pass
            self._layout_job = None

        self._cerrar_popup_ajuste()

        try:
            self.master.unbind("<Configure>")
        except tk.TclError:
            pass

        if getattr(self.master, "_pantalla_activa", None) is self:
            self.master._pantalla_activa = None

    def _salir_fullscreen(self, event=None):
        try:
            self.master.attributes("-fullscreen", False)
        except tk.TclError:
            pass

        try:
            self.master.state("normal")
        except tk.TclError:
            pass

        try:
            self.master.resizable(True, True)
            self.master.minsize(980, 640)
        except tk.TclError:
            pass

        try:
            ancho_actual = self.master.winfo_width()
            alto_actual = self.master.winfo_height()
            ancho_pantalla = self.master.winfo_screenwidth()
            alto_pantalla = self.master.winfo_screenheight()
        except tk.TclError:
            self._programar_layout_responsive()
            return "break"

        if ancho_actual < 1100 or alto_actual < 700:
            ancho = min(max(1320, int(ancho_pantalla * 0.82)), max(ancho_pantalla - 80, 980))
            alto = min(max(820, int(alto_pantalla * 0.82)), max(alto_pantalla - 80, 640))
            pos_x = max((ancho_pantalla - ancho) // 2, 10)
            pos_y = max((alto_pantalla - alto) // 2, 10)
            try:
                self.master.geometry(f"{ancho}x{alto}+{pos_x}+{pos_y}")
            except tk.TclError:
                pass

        self._programar_layout_responsive()
        return "break"

    def _aplicar_layout_acciones(self, ancho_disponible=None):
        widgets = [
            self.botones_acciones_frame,
            self.boton_ajuste,
            self.boton_finalizar,
        ]
        if not all(self._widget_existe(widget) for widget in widgets):
            return

        if ancho_disponible is None:
            try:
                self.botones_acciones_frame.update_idletasks()
                ancho_disponible = self.botones_acciones_frame.winfo_width()
            except tk.TclError:
                ancho_disponible = 0

        if not ancho_disponible:
            try:
                ancho_disponible = self.derecha_canvas.winfo_width() if self.derecha_canvas else self.derecha_frame.winfo_width()
            except tk.TclError:
                ancho_disponible = 0

        if not ancho_disponible:
            try:
                ancho_disponible = self.master.winfo_width()
            except tk.TclError:
                ancho_disponible = 0

        alto_disponible = 0
        try:
            if self.derecha_canvas:
                alto_disponible = self.derecha_canvas.winfo_height()
        except tk.TclError:
            alto_disponible = 0
        except AttributeError:
            alto_disponible = 0

        if not alto_disponible:
            try:
                alto_disponible = self.master.winfo_height()
            except tk.TclError:
                alto_disponible = 0
            except AttributeError:
                alto_disponible = 0

        self._aplicar_compactacion_acciones(ancho_disponible, alto_disponible)

        layout_acciones = "columna" if ancho_disponible < 560 else "doble"
        self._acciones_layout_actual = layout_acciones

        separacion = 10
        separacion_final = 10
        if self._acciones_modo_altura == "compacto":
            separacion = 6
            separacion_final = 8
        elif self._acciones_modo_altura == "ultra":
            separacion = 4
            separacion_final = 6

        try:
            self.botones_acciones_frame.grid_columnconfigure(0, weight=1)
            self.botones_acciones_frame.grid_columnconfigure(1, weight=1 if layout_acciones == "doble" else 0)
        except tk.TclError:
            return

        if self.label_acciones_descripcion and self._widget_existe(self.label_acciones_descripcion):
            wrap = max(int(ancho_disponible) - 40, 240)
            self.label_acciones_descripcion.config(wraplength=wrap)

        for boton in [self.boton_ajuste, self.boton_finalizar]:
            boton.grid_forget()

        if layout_acciones == "columna":
            self.boton_ajuste.grid(row=0, column=0, sticky="ew", pady=(0, separacion))
            self.boton_finalizar.grid(row=1, column=0, sticky="ew", pady=(separacion_final, 0))
            return

        self.boton_ajuste.grid(row=0, column=0, sticky="ew", padx=(0, separacion // 2))
        self.boton_finalizar.grid(row=0, column=1, sticky="ew", padx=(separacion // 2, 0))

    def _programar_layout_responsive(self, event=None):
        if event is not None and event.widget is not self.master:
            return
        if getattr(self.master, "_pantalla_activa", None) is not self:
            return
        if not self._widget_existe(self.izquierda_frame) or not self._widget_existe(self.derecha_frame):
            return

        if self._layout_job:
            try:
                self.master.after_cancel(self._layout_job)
            except tk.TclError:
                pass

        self._layout_job = self.master.after(60, self._aplicar_layout_responsive)

    def _aplicar_layout_responsive(self):
        self._layout_job = None
        if getattr(self.master, "_pantalla_activa", None) is not self:
            return
        if not self._widget_existe(self.izquierda_frame) or not self._widget_existe(self.derecha_frame):
            return

        ancho_actual = self.master.winfo_width() or self.master.winfo_screenwidth()
        alto_actual = self.master.winfo_height() or self.master.winfo_screenheight()
        self._aplicar_compactacion_general(ancho_actual, alto_actual)
        layout = "vertical" if ancho_actual < 1260 else "horizontal"
        modo_compacto = getattr(self, "_modo_compacto_general", "normal")
        separacion = 20
        separacion_vertical = 16
        if modo_compacto == "compacto":
            separacion = 14
            separacion_vertical = 12
        elif modo_compacto == "ultra":
            separacion = 10
            separacion_vertical = 10

        if layout == self._layout_actual:
            self._aplicar_layout_acciones()
            self._actualizar_scroll_panel_derecho()
            return

        self._layout_actual = layout
        self.izquierda_frame.pack_forget()
        self.derecha_frame.pack_forget()

        if layout == "vertical":
            self.izquierda_frame.pack(fill=tk.BOTH, expand=True)
            self.derecha_frame.pack(fill=tk.BOTH, expand=True, pady=(separacion_vertical, 0))
            self._aplicar_layout_acciones()
            self._actualizar_scroll_panel_derecho()
            return

        self.izquierda_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.derecha_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(separacion, 0))
        self._aplicar_layout_acciones()
        self._actualizar_scroll_panel_derecho()

    def calcular_totales_con_ajuste(self, tipo=None, modo=None, valor=None):
        subtotal = sum(p["cantidad"] * p["precio"] for p in self.carrito)

        tipo = self.ajuste_tipo_var.get() if tipo is None else tipo
        modo = self.ajuste_modo_var.get() if modo is None else modo
        valor_fuente = self.ajuste_valor_var.get() if valor is None else valor

        try:
            valor = float(valor_fuente or 0)
        except ValueError:
            valor = 0.0

        if valor < 0:
            valor = 0.0

        importe_aplicado = 0.0

        if tipo in ["descuento", "interes"] and valor > 0:
            if modo == "porcentaje":
                importe_aplicado = subtotal * (valor / 100)
            else:
                importe_aplicado = valor

            if tipo == "descuento":
                importe_aplicado = min(importe_aplicado, subtotal)

        total_final = subtotal
        if tipo == "descuento":
            total_final -= importe_aplicado
        elif tipo == "interes":
            total_final += importe_aplicado

        return {
            "subtotal": round(subtotal, 2),
            "tipo": tipo,
            "modo": modo,
            "valor": round(valor, 2),
            "importe_aplicado": round(importe_aplicado, 2),
            "total_final": round(total_final, 2)
        }

    def _texto_resumen_ajuste(self, datos):
        subtotal_txt = f"Subtotal: ${datos['subtotal']:.2f}"
        if datos["tipo"] in ["descuento", "interes"] and datos["importe_aplicado"] > 0:
            signo = "-" if datos["tipo"] == "descuento" else "+"
            etiqueta = "Descuento" if datos["tipo"] == "descuento" else "Interes"
            if datos["modo"] == "porcentaje":
                detalle = f"{etiqueta}: {signo}${datos['importe_aplicado']:.2f} ({datos['valor']:.2f}%)"
            else:
                detalle = f"{etiqueta}: {signo}${datos['importe_aplicado']:.2f}"
            return f"{subtotal_txt} | {detalle}"
        return f"{subtotal_txt} | Sin ajuste aplicado"

    def _actualizar_boton_ajuste(self, datos):
        if not self.boton_ajuste:
            return
        if datos["tipo"] in ["descuento", "interes"] and datos["importe_aplicado"] > 0:
            self.boton_ajuste.config(text="Editar descuento / interes")
            return
        self.boton_ajuste.config(text="Agregar descuento / interes")

    def _definir_botones_admin(self):
        botones = []

        if self.permisos.get("ver_productos"):
            botones.append(("Productos", self.abrir_popup_productos))
        if self.permisos.get("ver_ventas"):
            botones.append(("Ventas", self.abrir_popup_ventas))
        if self.permisos.get("ver_registros"):
            botones.append(("Registros", self.abrir_popup_registros))
        if self.permisos.get("ver_deudas"):
            botones.append(("Deudas", self.abrir_popup_deudas))
        if self.permisos.get("ver_debito"):
            botones.append(("Débito", self.abrir_popup_debito))
        if self.permisos.get("ver_clientes"):
            botones.append(("Clientes", self.abrir_popup_clientes))
        if self.permisos.get("ver_reportes"):
            botones.append(("Reportes", self.abrir_popup_reportes))
        if self.permisos.get("gestionar_empleados"):
            botones.append(("Empleados", self.abrir_popup_empleados))

        return botones

    def crear_panel_sin_caja(self, frame):
        panel = tk.Frame(frame, bg="#ffffff", bd=1, relief="ridge", padx=28, pady=28)
        panel.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        tk.Label(
            panel,
            text=f"{self.empleado['puesto']}: acceso limitado",
            bg="#ffffff",
            fg="#1f2937",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        if self.permisos.get("gestionar_productos"):
            descripcion = "Este perfil no puede vender, pero sí puede consultar y gestionar productos."
        else:
            descripcion = "Este perfil no puede vender. Solo puede consultar los productos disponibles."

        tk.Label(
            panel,
            text=descripcion,
            bg="#ffffff",
            fg="#4b5563",
            font=("Segoe UI", 12),
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(10, 22))

        botones = tk.Frame(panel, bg="#ffffff")
        botones.pack(anchor="w")

        if self.permisos.get("ver_productos"):
            tk.Button(
                botones,
                text="Ver productos",
                command=self.abrir_popup_productos,
                bg="#2563eb",
                fg="white",
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=16,
                pady=8,
            ).pack(side=tk.LEFT, padx=(0, 10))

        if self.permisos.get("ver_reportes"):
            tk.Button(
                botones,
                text="Ver reportes",
                command=self.abrir_popup_reportes,
                bg="#0f766e",
                fg="white",
                font=("Segoe UI", 11, "bold"),
                relief="flat",
                padx=16,
                pady=8,
            ).pack(side=tk.LEFT)

        if self.permisos.get("ver_productos"):
            self.master.after(120, self.abrir_popup_productos)

    def crear_barra_superior_completa(self, frame):
        self.barra_superior = tk.Frame(frame, bg="#102a43", pady=14, padx=20, bd=0)
        self.barra_superior.pack(fill=tk.X, pady=(0, 15))

        # Empleado activo (izquierda)
        bloque_titulo = tk.Frame(self.barra_superior, bg="#102a43")
        bloque_titulo.pack(side=tk.LEFT, padx=(0, 18))
        self.label_barra_titulo = tk.Label(
            bloque_titulo,
            text="Caja activa",
            font=("Segoe UI", 18, "bold"),
            bg="#102a43",
            fg="white",
        )
        self.label_barra_titulo.pack(anchor="w")
        self.label_barra_subtitulo = tk.Label(
            bloque_titulo,
            text=f"Empleado: {self.empleado['nombre']} | Puesto: {self.empleado['puesto']}",
            font=("Segoe UI", 10),
            bg="#102a43",
            fg="#d9e2ec",
        )
        self.label_barra_subtitulo.pack(anchor="w")

        # Botones administración (centro)
        self.botones_admin_frame = tk.Frame(self.barra_superior, bg="#102a43")
        self.botones_admin_frame.pack(side=tk.LEFT, expand=True)

        for texto, comando in self._definir_botones_admin():
            boton = tk.Button(
                self.botones_admin_frame, text=texto, command=comando,
                bg="#1f6aa5", fg="white", font=("Segoe UI", 10, "bold"),
                relief="flat", padx=14, pady=7, bd=0,
                activebackground="#17537f", activeforeground="white",
                cursor="hand2"
            )
            boton.pack(side=tk.LEFT, padx=5)
            self.botones_admin.append(boton)

        # Cerrar sesión (derecha)
        self.boton_cerrar_sesion = tk.Button(
            self.barra_superior,
            text="Cerrar sesión",
            command=self.cerrar_sesion_y_volver_al_login,
            bg=self.color_peligro,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=14,
            pady=8,
            bd=0,
            activebackground=self.color_peligro_hover,
            activeforeground="white",
            cursor="hand2",
        )
        self.boton_cerrar_sesion.pack(side=tk.RIGHT)

    def _crear_popup_sugerencias(self):
        if self.popup_sugerencias is not None:
            try:
                if self.popup_sugerencias.winfo_exists():
                    return
            except tk.TclError:
                self.popup_sugerencias = None

        self.popup_sugerencias = tk.Toplevel(self.master)
        self.popup_sugerencias.withdraw()
        self.popup_sugerencias.overrideredirect(True)  # sin bordes del sistema
        self.popup_sugerencias.configure(bg="white")
        self.popup_sugerencias.attributes("-topmost", True)

        frame = tk.Frame(self.popup_sugerencias, bg="white", bd=1, relief="solid")
        frame.pack(fill=tk.BOTH, expand=True)

        self.lista_sugerencias = tk.Listbox(
            frame,
            font=self.font_sugerencias,
            height=7,
            width=50,
            bg="white",
            fg="black",
            relief="flat",
            bd=0,
            activestyle="none"
        )
        self.lista_sugerencias.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.lista_sugerencias.bind("<<ListboxSelect>>", self.seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Double-Button-1>", self.seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Return>", self.seleccionar_sugerencia)

    def _posicionar_popup_sugerencias(self):
        if not self.popup_sugerencias or not self.lista_sugerencias:
            return
    
        try:
            x = self.entrada_id.winfo_rootx()
            y_entry = self.entrada_id.winfo_rooty()
            ancho = self.entrada_id.winfo_width()
        except tk.TclError:
            return
    
        alto = 190  # mismo alto que venías usando
    
        # 👇 clave: restar el alto en vez de sumarlo
        y = y_entry - alto - 2
    
        self.popup_sugerencias.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _focus_lista_sugerencias(self, event=None):
        if self.lista_sugerencias and self.popup_sugerencias:
            try:
                if self.popup_sugerencias.winfo_viewable() and self.lista_sugerencias.size() > 0:
                    self.lista_sugerencias.focus_set()
                    self.lista_sugerencias.selection_clear(0, tk.END)
                    self.lista_sugerencias.selection_set(0)
                    self.lista_sugerencias.activate(0)
                    return "break"
            except tk.TclError:
                pass

    def _on_focus_out_buscador(self, event=None):
        self.master.after(150, self._cerrar_si_no_hay_foco_en_sugerencias)

    def _cerrar_si_no_hay_foco_en_sugerencias(self):
        widget_con_foco = self.master.focus_get()
        if widget_con_foco not in [self.entrada_id, self.lista_sugerencias]:
            self._ocultar_sugerencias()

    def crear_entrada_producto(self, frame):
        tarjeta = self._crear_tarjeta(frame, pady=(0, 14))
        tarjeta.pack(**tarjeta._pack_config)
        self.tarjeta_entrada_producto = tarjeta
        sub_frame = tk.Frame(tarjeta, bg=self.color_tarjeta, padx=18, pady=16)
        sub_frame.pack(fill=tk.X)
        sub_frame.grid_columnconfigure(1, weight=1)
        self.entrada_producto_frame = sub_frame

        self.label_entrada_producto_titulo = tk.Label(
            sub_frame,
            text="Agregar producto",
            font=("Segoe UI", 16, "bold"),
            bg=self.color_tarjeta,
            fg=self.color_texto,
        )
        self.label_entrada_producto_titulo.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 4))
        tk.Label(
            sub_frame,
            text="Buscá por ID o nombre y cargá la cantidad antes de agregar al carrito.",
            font=self.font_subtitulo,
            bg=self.color_tarjeta,
            fg=self.color_secundario,
        ).grid(row=1, column=0, columnspan=5, sticky="w", pady=(0, 12))

        # --- ID o nombre del producto ---
        self.label_buscar_producto = tk.Label(sub_frame, text="Buscar producto:", font=("Segoe UI", 13, "bold"), bg=self.color_tarjeta, fg=self.color_texto)
        self.label_buscar_producto.grid(row=2, column=0, sticky="w", padx=(0, 8))

        self.entrada_id = tk.Entry(sub_frame, font=self.font_busqueda, relief="solid", bd=2, width=34, bg="white")
        self.entrada_id.bind("<Down>", self._focus_lista_sugerencias)
        self.entrada_id.bind("<FocusOut>", self._on_focus_out_buscador)
        self.entrada_id.grid(row=2, column=1, padx=(0, 20), sticky="ew", ipady=6)
        self.entrada_id.bind("<KeyRelease>", self.autocompletar_producto)



        # --- Cantidad ---
        self.label_cantidad_producto = tk.Label(sub_frame, text="Cantidad:", font=("Segoe UI", 13, "bold"), bg=self.color_tarjeta, fg=self.color_texto)
        self.label_cantidad_producto.grid(row=2, column=2, sticky="w", padx=(0, 8))

        self.entrada_cantidad = tk.Entry(sub_frame, font=("Segoe UI", 15, "bold"), relief="solid", bd=2, width=8, bg="white")
        self.entrada_cantidad.grid(row=2, column=3, padx=(0, 20), ipady=6)
        self.entrada_cantidad.insert(0, "1")  # Valor por defecto: 1

        # --- Botón para agregar al carrito ---
        self.boton_agregar_producto = tk.Button(sub_frame, text="Agregar", command=self.agregar_producto,
                                font=("Segoe UI", 13, "bold"), bg=self.color_exito, fg="white", relief="flat", padx=18, pady=10, bd=0, activebackground=self.color_exito_hover, activeforeground="white", cursor="hand2")
        self.boton_agregar_producto.grid(row=2, column=4)




    def crear_lista_productos(self, frame):
        # Frame que contiene carrito y stock bajo
        lista_y_stock_frame = tk.Frame(frame, bg=self.color_fondo)
        lista_y_stock_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # ----- COLUMNA IZQUIERDA: Carrito -----
        carrito_frame = self._crear_tarjeta(lista_y_stock_frame, pady=0)
        carrito_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.encabezado_carrito = tk.Frame(carrito_frame, bg=self.color_tarjeta, padx=16, pady=14)
        self.encabezado_carrito.pack(fill=tk.X)
        self.label_carrito_titulo = tk.Label(
            self.encabezado_carrito,
            text="Carrito actual",
            bg=self.color_tarjeta,
            fg=self.color_texto,
            font=("Segoe UI", 16, "bold"),
        )
        self.label_carrito_titulo.pack(anchor="w")
        self.label_resumen_carrito = tk.Label(
            self.encabezado_carrito,
            text="Aún no agregaste productos.",
            bg=self.color_tarjeta,
            fg=self.color_secundario,
            font=self.font_subtitulo,
        )
        self.label_resumen_carrito.pack(anchor="w", pady=(2, 0))
        self.label_ayuda_carrito = tk.Label(
            self.encabezado_carrito,
            text="Doble clic modifica | Supr elimina | Clic derecho abre acciones",
            bg=self.color_tarjeta,
            fg=self.color_secundario,
            font=("Segoe UI", 9),
        )
        self.label_ayuda_carrito.pack(anchor="w", pady=(2, 0))

        # Listbox con borde visual limpio
        lista_frame = tk.Frame(carrito_frame, bg=self.color_tarjeta, bd=0)
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))

        self.lista_productos = tk.Listbox(lista_frame, font=self.font_lista, height=15,
                                        bg="white", fg=self.color_texto, selectbackground="#dbeafe",
                                        selectforeground=self.color_texto,
                                        activestyle="none", relief="flat", bd=0)
        self.lista_productos.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.lista_productos.bind("<Double-Button-1>", self._editar_producto_desde_lista)
        self.lista_productos.bind("<Delete>", self._eliminar_producto_desde_lista)
        self.lista_productos.bind("<Button-3>", self._mostrar_menu_carrito)

        # Limpiar cualquier contenido previo por seguridad (puede prevenir "residuos")
        self.lista_productos.delete(0, tk.END)
        self.menu_carrito_acciones = tk.Menu(self.master, tearoff=0)
        self.menu_carrito_acciones.add_command(
            label="Modificar cantidad",
            command=self.cambiar_cantidad_seleccionada,
        )
        self.menu_carrito_acciones.add_command(
            label="Eliminar producto",
            command=self.eliminar_producto_seleccionado,
        )

        # ----- COLUMNA DERECHA: Stock bajo -----
        self.stock_bajo_frame = tk.Frame(lista_y_stock_frame, bg=self.color_fondo, width=300)
        self.stock_bajo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))

    def _seleccionar_producto_desde_evento_lista(self, event):
        if not self.carrito or not self._widget_existe(self.lista_productos):
            return False

        try:
            indice = int(self.lista_productos.nearest(event.y))
        except (tk.TclError, TypeError, ValueError, AttributeError):
            return False

        if indice < 0 or indice >= len(self.carrito):
            return False

        self.lista_productos.selection_clear(0, tk.END)
        self.lista_productos.selection_set(indice)
        self.lista_productos.activate(indice)
        return True

    def _editar_producto_desde_lista(self, event=None):
        if event is not None and not self._seleccionar_producto_desde_evento_lista(event):
            return "break"
        self.cambiar_cantidad_seleccionada()
        return "break"

    def _eliminar_producto_desde_lista(self, event=None):
        self.eliminar_producto_seleccionado()
        return "break"

    def _mostrar_menu_carrito(self, event):
        if not self.menu_carrito_acciones or not self._seleccionar_producto_desde_evento_lista(event):
            return "break"

        try:
            self.menu_carrito_acciones.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self.menu_carrito_acciones.grab_release()
            except tk.TclError:
                pass
        return "break"



    def crear_botones_y_finalizar(self, frame):
        # --- Acciones ---
        tarjeta = self._crear_tarjeta(frame, pady=(0, 0))
        tarjeta.pack(**tarjeta._pack_config)
        tk.Label(
            tarjeta,
            text="Acciones de venta",
            font=("Segoe UI", 16, "bold"),
            bg=self.color_tarjeta,
            fg=self.color_texto,
        ).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(
            tarjeta,
            text="Ajustá el total acá. Para productos usá las acciones del carrito.",
            font=self.font_subtitulo,
            bg=self.color_tarjeta,
            fg=self.color_secundario,
        ).pack(anchor="w", padx=16)

        botones_frame = tk.Frame(tarjeta, bg=self.color_tarjeta, padx=16, pady=14)
        botones_frame.pack(fill=tk.X)
        botones_frame.grid_columnconfigure(0, weight=1)
        botones_frame.grid_columnconfigure(1, weight=1)

        self.boton_ajuste = tk.Button(
            botones_frame,
            text="Agregar descuento / interes",
            command=self.abrir_popup_ajuste,
            bg=self.color_primario,
            fg="white",
            font=self.font_labels,
            relief="flat",
            padx=15,
            pady=9,
            bd=0,
            activebackground=self.color_primario_hover,
            activeforeground="white",
            cursor="hand2",
        )
        self.boton_ajuste.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        tk.Button(
            botones_frame,
            text="Finalizar venta (F2)",
            command=self.confirmar_venta,
            bg=self.color_exito,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            bd=0,
            activebackground=self.color_exito_hover,
            activeforeground="white",
            cursor="hand2",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self.label_acciones_descripcion = tarjeta.winfo_children()[1]
        self.label_acciones_descripcion.config(justify="left", wraplength=380)
        self.label_acciones_titulo = tarjeta.winfo_children()[0]
        self.botones_acciones_frame = botones_frame

        botones_por_texto = {
            widget.cget("text"): widget
            for widget in botones_frame.grid_slaves()
            if isinstance(widget, tk.Button)
        }
        self.boton_modificar = None
        self.boton_eliminar = None
        self.boton_finalizar = botones_por_texto.get("Finalizar venta (F2)")

        self._aplicar_layout_acciones()



    def crear_info_pago(self, frame):
        # --- Datos del cliente ---
        self.label_cliente_pago_titulo = tk.Label(frame, text="Cliente y forma de pago", font=("Segoe UI", 16, "bold"), bg=self.color_fondo, fg=self.color_texto)
        self.label_cliente_pago_titulo.pack(anchor="w", padx=10, pady=(0, 5))

        # DATOS DEL CLIENTE
        self.cliente_frame = tk.LabelFrame(frame, text="Datos del cliente", bg=self.color_tarjeta, fg=self.color_texto, font=self.font_labels, padx=12, pady=12, bd=1, relief="solid")

        self.label_dni = tk.Label(self.cliente_frame, text="DNI (opcional):", font=self.font_pequena, bg=self.color_tarjeta, fg="#555")
        self.label_dni.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.entry_dni = tk.Entry(self.cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f8fafc", width=20)
        self.entry_dni.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        self.entry_dni.bind("<KeyRelease>", self._on_cliente_editado)

        self.label_nombre = tk.Label(self.cliente_frame, text="Nombre (opcional):", font=self.font_pequena, bg=self.color_tarjeta, fg="#555")
        self.label_nombre.grid(row=0, column=1, sticky="w")
        self.entry_nombre = tk.Entry(self.cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f8fafc", width=25)
        self.entry_nombre.grid(row=1, column=1, padx=(0, 10), pady=(0, 10))
        self.entry_nombre.bind("<KeyRelease>", self._on_cliente_editado)

        self.lista_clientes_sugeridos = tk.Listbox(
            self.cliente_frame,
            font=self.font_pequena,
            height=4,
            bg="white",
            fg="black",
            relief="solid",
            bd=1,
        )
        self.lista_clientes_sugeridos.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 10))
        self.lista_clientes_sugeridos.bind("<<ListboxSelect>>", self.seleccionar_cliente_sugerido)
        self.lista_clientes_sugeridos.bind("<Double-Button-1>", self.seleccionar_cliente_sugerido)
        self.lista_clientes_sugeridos.grid_remove()

        # FORMA DE PAGO
        self.forma_frame = tk.LabelFrame(frame, text="Forma de pago", bg=self.color_tarjeta, fg=self.color_texto, font=self.font_labels, padx=12, pady=12, bd=1, relief="solid")
        self.forma_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        # Botones
        self.forma_pago_var = tk.StringVar(value="efectivo")
        formas = [("Efectivo", "efectivo"), ("Débito", "debito"), ("Deuda", "deuda")]

        self.botones_pago = {}
        for texto, valor in formas:
            color_activo, _ = self._colores_forma_pago(valor)
            btn = tk.Button(self.forma_frame, text=texto, font=self.font_pequena,
                            bg="#e5e7eb" if self.forma_pago_var.get() != valor else color_activo,
                            fg="#111827" if self.forma_pago_var.get() != valor else "white",
                            relief="solid", bd=1, padx=10, pady=5,
                            command=lambda v=valor: self.seleccionar_forma_pago(v))
            btn.pack(side=tk.LEFT, padx=5)
            self.botones_pago[valor] = btn

        # Campo "Con cuánto paga"
        self.fila_pago_frame = tk.Frame(self.forma_frame, bg=self.color_tarjeta)
        self.fila_pago_frame.pack(fill=tk.X, pady=(10, 0))
        self.label_pago = tk.Label(self.fila_pago_frame, text="Pago:", font=self.font_pequena, bg=self.color_tarjeta, fg="#555")
        self.label_pago.pack(anchor="w")
        self.entry_pago = tk.Entry(self.fila_pago_frame, font=("Segoe UI", 16, "bold"), relief="solid", bd=1, bg="#f8fafc")
        self.entry_pago.pack(fill=tk.X, pady=(4, 0), ipady=6)
        self.entry_pago.bind("<KeyRelease>", self.actualizar_vuelto)

        self.cliente_toggle_frame = tk.Frame(frame, bg=self.color_fondo)
        self.cliente_toggle_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.boton_cliente_toggle = tk.Button(
            self.cliente_toggle_frame,
            text="Agregar cliente opcional",
            command=self.toggle_panel_cliente,
            bg="#e5e7eb",
            fg="#111827",
            font=self.font_pequena,
            relief="flat",
            padx=12,
            pady=6,
            bd=0,
            activebackground="#d1d5db",
            activeforeground="#111827",
            cursor="hand2",
        )
        self.boton_cliente_toggle.pack(side=tk.LEFT)

        self.label_cliente_resumen = tk.Label(
            self.cliente_toggle_frame,
            text="",
            bg=self.color_fondo,
            fg=self.color_secundario,
            font=self.font_pequena,
            justify="left",
        )
        self.label_cliente_resumen.pack(side=tk.LEFT, padx=(12, 0))

        self._actualizar_panel_cliente()


    def _cliente_cargado(self):
        return bool(self.entry_dni.get().strip() or self.entry_nombre.get().strip())

    def _panel_cliente_visible(self):
        if not self._widget_existe(self.cliente_frame):
            return False
        try:
            return bool(self.cliente_frame.winfo_manager())
        except tk.TclError:
            return False

    def _mostrar_panel_cliente(self):
        if not self._widget_existe(self.cliente_frame):
            return
        if self._panel_cliente_visible():
            return
        self.cliente_frame.pack(fill=tk.X, pady=(0, 10), padx=10, after=self.cliente_toggle_frame)

    def _ocultar_panel_cliente(self):
        if not self._panel_cliente_visible():
            return
        self.cliente_frame.pack_forget()
        self._ocultar_sugerencias_cliente()

    def _texto_resumen_cliente(self):
        nombre = self.entry_nombre.get().strip()
        dni = self.entry_dni.get().strip()
        if not nombre and not dni:
            return ""
        if nombre and dni:
            return f"Cliente: {nombre} | DNI/ref: {dni}"
        if nombre:
            return f"Cliente: {nombre}"
        return f"DNI/ref: {dni}"

    def _cliente_requerido(self):
        return self.forma_pago_var.get() in ["deuda", "debito"]

    def toggle_panel_cliente(self):
        self._cliente_panel_expandido = not self._panel_cliente_visible()
        self._actualizar_panel_cliente()

    def _actualizar_panel_cliente(self, preservar_visibilidad=False):
        obligatorio = self._cliente_requerido()
        cliente_cargado = self._cliente_cargado()
        panel_visible = self._panel_cliente_visible()
        visible = self._cliente_panel_expandido or (obligatorio and not cliente_cargado)

        if preservar_visibilidad and panel_visible:
            visible = True

        if visible:
            self._mostrar_panel_cliente()
        else:
            self._ocultar_panel_cliente()

        if obligatorio:
            self.label_dni.config(text="DNI o referencia:")
            self.label_nombre.config(text="Nombre o alias:")
            self.entry_dni.config(bg="white")
            self.entry_nombre.config(bg="white")
        else:
            self.label_dni.config(text="DNI del cliente (opcional):")
            self.label_nombre.config(text="Nombre del cliente (opcional):")
            self.entry_dni.config(bg="#f8fafc")
            self.entry_nombre.config(bg="#f8fafc")

        if self.boton_cliente_toggle:
            if self._panel_cliente_visible():
                if obligatorio and not cliente_cargado:
                    texto_boton = "Completar cliente"
                elif obligatorio:
                    texto_boton = "Ocultar cliente"
                else:
                    texto_boton = "Ocultar cliente opcional"
            else:
                if obligatorio:
                    texto_boton = "Completar cliente" if not cliente_cargado else "Editar cliente"
                else:
                    texto_boton = "Editar cliente opcional" if cliente_cargado else "Agregar cliente opcional"
            self.boton_cliente_toggle.config(text=texto_boton)

        if self.label_cliente_resumen:
            if not self._panel_cliente_visible() and cliente_cargado:
                self.label_cliente_resumen.config(text=self._texto_resumen_cliente())
            elif not self._panel_cliente_visible() and obligatorio and not cliente_cargado:
                self.label_cliente_resumen.config(text="Cliente requerido para debito o deuda.")
            else:
                self.label_cliente_resumen.config(text="")

        self._actualizar_scroll_panel_derecho()

    def _on_cliente_editado(self, event=None):
        self.autocompletar_cliente(event)
        self._actualizar_panel_cliente(preservar_visibilidad=True)


    def _ocultar_sugerencias(self):
        if self.lista_sugerencias:
            self.lista_sugerencias.delete(0, tk.END)

        if self.popup_sugerencias is not None:
            try:
                if self.popup_sugerencias.winfo_exists():
                    self.popup_sugerencias.withdraw()
            except tk.TclError:
                self.popup_sugerencias = None

    def _extraer_id_desde_texto_producto(self, texto):
        candidato = texto.split(" - ", 1)[0].strip()
        if candidato.isdigit():
            return int(candidato)
        return None

    def _buscar_coincidencias_producto(self, texto):
        return buscar_productos_por_texto(texto)[:10]

    def _cantidad_por_defecto_producto(self, producto=None):
        if producto and producto_se_vende_por_kilo(producto=producto):
            return "0.250"
        return "1"

    def _restablecer_cantidad_producto(self, producto=None):
        self.entrada_cantidad.delete(0, tk.END)
        self.entrada_cantidad.insert(0, self._cantidad_por_defecto_producto(producto))

    def _texto_sugerencia_producto(self, producto):
        stock_txt = formatear_cantidad(producto.get("stock_actual", 0), producto=producto, con_unidad=True)
        return f"{producto['id']} - {producto['nombre']} ({describir_precio_producto(producto)} | stock {stock_txt})"

    def _texto_resumen_cantidades_carrito(self):
        unidades = 0
        kilos = 0.0

        for producto in self.carrito:
            if producto_se_vende_por_kilo(tipo_venta=producto.get("tipo_venta")):
                kilos += float(producto.get("cantidad", 0) or 0)
            else:
                unidades += int(float(producto.get("cantidad", 0) or 0))

        partes = []
        if unidades:
            partes.append(f"{unidades} u")
        if kilos:
            partes.append(f"{formatear_cantidad(kilos, tipo_venta='kilo')} kg")
        return " + ".join(partes) if partes else "0 u"

    def _texto_item_carrito(self, producto):
        cantidad_txt = formatear_cantidad(producto.get("cantidad", 0), tipo_venta=producto.get("tipo_venta"))
        unidad = producto.get("unidad_medida") or obtener_unidad_medida(tipo_venta=producto.get("tipo_venta"))
        subtotal = float(producto.get("cantidad", 0) or 0) * float(producto.get("precio", 0) or 0)

        if producto_se_vende_por_kilo(tipo_venta=producto.get("tipo_venta")):
            return f"{cantidad_txt} {unidad} de {producto['nombre']} - ${producto['precio']:.2f} / kg = ${subtotal:.2f}"

        return f"{cantidad_txt} {unidad} x {producto['nombre']} - ${producto['precio']:.2f} c/u = ${subtotal:.2f}"

    def _resolver_producto_desde_entrada(self):
        texto = self.entrada_id.get().strip()
        if not texto:
            return None

        if self.lista_sugerencias.curselection():
            seleccion = self.lista_sugerencias.get(self.lista_sugerencias.curselection()[0])
            prod_id = self._extraer_id_desde_texto_producto(seleccion)
            if prod_id is not None:
                return buscar_producto(prod_id)

        prod_id = self._extraer_id_desde_texto_producto(texto)
        if prod_id is not None:
            producto = buscar_producto(prod_id)
            if producto:
                return producto

        coincidencias = self._buscar_coincidencias_producto(texto)
        texto_normalizado = texto.lower()
        for producto in coincidencias:
            if str(producto.get("nombre", "")).strip().lower() == texto_normalizado:
                return producto

        if len(coincidencias) == 1:
            return coincidencias[0]

        return None

    def _limpiar_busqueda_producto(self):
        self.entrada_id.delete(0, tk.END)
        self._ocultar_sugerencias()

    def autocompletar_producto(self, event=None):
        texto = self.entrada_id.get().strip()
        if not texto:
            self._ocultar_sugerencias()
            return

        sugerencias = self._buscar_coincidencias_producto(texto)
        if not sugerencias:
            self._ocultar_sugerencias()
            return

        if self.popup_sugerencias is None or not self.popup_sugerencias.winfo_exists():
            self._crear_popup_sugerencias()

        self.lista_sugerencias.delete(0, tk.END)
        for prod in sugerencias:
            self.lista_sugerencias.insert(tk.END, self._texto_sugerencia_producto(prod))

        self._posicionar_popup_sugerencias()
        self.popup_sugerencias.deiconify()
        self.popup_sugerencias.lift()

    def seleccionar_sugerencia(self, event=None):
        if not self.lista_sugerencias or not self.lista_sugerencias.curselection():
            return

        seleccion = self.lista_sugerencias.get(self.lista_sugerencias.curselection()[0])
        self.entrada_id.delete(0, tk.END)
        self.entrada_id.insert(0, seleccion)

        producto = None
        prod_id = self._extraer_id_desde_texto_producto(seleccion)
        if prod_id is not None:
            producto = buscar_producto(prod_id)

        self._restablecer_cantidad_producto(producto)
        self._ocultar_sugerencias()
        self.entrada_cantidad.focus_set()

    def _ocultar_sugerencias_cliente(self):
        self.lista_clientes_sugeridos.delete(0, tk.END)
        self.lista_clientes_sugeridos.grid_remove()

    def _buscar_coincidencias_cliente(self, texto):
        return buscar_clientes_por_texto(texto)[:8]

    def autocompletar_cliente(self, event=None):
        if self.forma_pago_var.get() not in ["deuda", "debito"] and not self._panel_cliente_visible():
            self._ocultar_sugerencias_cliente()
            return

        texto = ""
        if event and event.widget is self.entry_dni:
            texto = self.entry_dni.get().strip()
        elif event and event.widget is self.entry_nombre:
            texto = self.entry_nombre.get().strip()
        else:
            texto = self.entry_nombre.get().strip() or self.entry_dni.get().strip()

        if not texto:
            self._ocultar_sugerencias_cliente()
            return

        sugerencias = self._buscar_coincidencias_cliente(texto)
        if not sugerencias:
            self._ocultar_sugerencias_cliente()
            return

        self.lista_clientes_sugeridos.delete(0, tk.END)
        for cliente in sugerencias:
            self.lista_clientes_sugeridos.insert(
                tk.END,
                f"{cliente.get('dni', '')} - {cliente.get('nombre', '')}",
            )
        self.lista_clientes_sugeridos.grid()

    def seleccionar_cliente_sugerido(self, event=None):
        if not self.lista_clientes_sugeridos.curselection():
            return

        seleccion = self.lista_clientes_sugeridos.get(self.lista_clientes_sugeridos.curselection()[0])
        dni, _, nombre = seleccion.partition(" - ")
        self.entry_dni.delete(0, tk.END)
        self.entry_dni.insert(0, dni.strip())
        self.entry_nombre.delete(0, tk.END)
        self.entry_nombre.insert(0, nombre.strip())
        self._ocultar_sugerencias_cliente()
        self._cliente_panel_expandido = False
        self._actualizar_panel_cliente()

    def _resolver_cliente_para_pago(self):
        dni = self.entry_dni.get().strip()
        nombre = self.entry_nombre.get().strip()

        if not dni and not nombre:
            return None

        return resolver_cliente_para_venta(
            dni=dni or None,
            nombre=nombre or None,
            crear_si_no_existe=True,
        )

    def _colores_forma_pago(self, forma):
        colores = {
            "efectivo": ("#2563eb", "#1d4ed8"),
            "debito": ("#7c3aed", "#6d28d9"),
            "deuda": ("#b45309", "#92400e"),
        }
        return colores.get(forma, (self.color_primario, self.color_primario_hover))


    def seleccionar_forma_pago(self, valor):
        self.forma_pago_var.set(valor)
        for v, btn in self.botones_pago.items():
            if v == valor:
                color, color_hover = self._colores_forma_pago(v)
                btn.config(bg=color, fg="white", activebackground=color_hover, activeforeground="white")
            else:
                btn.config(bg="#e5e7eb", fg="#111827", activebackground="#d1d5db", activeforeground="#111827")
        self.cambiar_forma_pago(valor)


    def crear_total_y_vuelto_responsive(self, frame):
        self.label_resumen_pago_titulo = tk.Label(
            frame,
            text="Resumen de pago",
            font=("Segoe UI", 16, "bold"),
            bg=self.color_fondo,
            fg=self.color_texto,
        )
        self.label_resumen_pago_titulo.pack(anchor="w", padx=10, pady=(10, 5))

        self.resumen_frame = tk.LabelFrame(
            frame,
            text="Totales",
            bg=self.color_tarjeta,
            fg=self.color_texto,
            font=self.font_labels,
            padx=12,
            pady=12,
            bd=1,
            relief="solid",
        )
        self.resumen_frame.pack(fill=tk.X, padx=10)

        self.total_label = tk.Label(
            self.resumen_frame,
            text="Total: $0.00",
            font=("Segoe UI", 28, "bold"),
            bg=self.color_tarjeta,
            fg=self.color_exito,
        )
        self.total_label.pack(anchor="w", pady=(0, 10))

        self.ajuste_info_label = tk.Label(
            self.resumen_frame,
            textvariable=self.ajuste_resumen_var,
            bg=self.color_tarjeta,
            fg="#555",
            font=("Segoe UI", 10),
            justify="left",
            wraplength=420,
        )
        self.ajuste_info_label.pack(anchor="w", pady=(0, 10))

        self.vuelto_label = tk.Label(
            self.resumen_frame,
            text="Vuelto: $0.00",
            font=("Segoe UI", 20),
            bg=self.color_tarjeta,
            fg=self.color_peligro,
        )
        self.vuelto_label.pack(anchor="w")


    def crear_total_y_vuelto(self, frame):
        # --- Resumen de pago ---
        tk.Label(frame, text="Resumen de pago", font=("Segoe UI", 16, "bold"), bg=self.color_fondo, fg=self.color_texto).pack(anchor="w", padx=10, pady=(10, 5))

        resumen_frame = tk.LabelFrame(frame, text="Totales", bg=self.color_tarjeta, fg=self.color_texto, font=self.font_labels, padx=12, pady=12, bd=1, relief="solid")
        resumen_frame.pack(fill=tk.X, padx=10)

        self.total_label = tk.Label(resumen_frame, text="Total: $0.00",
                            font=("Segoe UI", 28, "bold"), bg=self.color_tarjeta, fg=self.color_exito)
        self.total_label.pack(anchor="w", pady=(0, 10))

        ajuste_frame = tk.LabelFrame(
            resumen_frame,
            text="Descuento / Interés",
            bg=self.color_tarjeta,
            fg=self.color_texto,
            font=self.font_labels,
            padx=10,
            pady=10
        )
        ajuste_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ajuste_frame, text="Tipo:", bg=self.color_tarjeta, font=self.font_labels).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        combo_tipo = ttk.Combobox(
            ajuste_frame,
            textvariable=self.ajuste_tipo_var,
            values=["ninguno", "descuento", "interes"],
            state="readonly",
            width=12
        )
        combo_tipo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(ajuste_frame, text="Aplicar como:", bg=self.color_tarjeta, font=self.font_labels).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        combo_modo = ttk.Combobox(
            ajuste_frame,
            textvariable=self.ajuste_modo_var,
            values=["porcentaje", "monto"],
            state="readonly",
            width=12
        )
        combo_modo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(ajuste_frame, text="Valor:", bg=self.color_tarjeta, font=self.font_labels).grid(row=1, column=0, sticky="w", padx=5, pady=5)

        entry_ajuste = tk.Entry(
            ajuste_frame,
            textvariable=self.ajuste_valor_var,
            font=self.font_labels,
            relief="solid",
            bd=1,
            width=15
        )
        entry_ajuste.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.ajuste_info_label = tk.Label(
            ajuste_frame,
            text="Sin ajuste aplicado",
            bg=self.color_tarjeta,
            fg="#555",
            font=("Segoe UI", 10)
        )
        self.ajuste_info_label.grid(row=1, column=2, columnspan=2, sticky="w", padx=5, pady=5)

        combo_tipo.bind("<<ComboboxSelected>>", lambda e: self.actualizar_total())
        combo_modo.bind("<<ComboboxSelected>>", lambda e: self.actualizar_total())
        entry_ajuste.bind("<KeyRelease>", self.actualizar_total)

        self.vuelto_label = tk.Label(resumen_frame, text="Vuelto: $0.00",
                                    font=("Segoe UI", 20), bg=self.color_tarjeta, fg=self.color_peligro)
        self.vuelto_label.pack(anchor="w")



    def abrir_popup_ajuste(self):
        if self.ventana_ajuste is not None:
            try:
                if self.ventana_ajuste.winfo_exists():
                    self.ventana_ajuste.lift()
                    self.ventana_ajuste.focus_force()
                    return
            except tk.TclError:
                self.ventana_ajuste = None

        ventana = tk.Toplevel(self.master)
        ventana.title("Descuento o interes")
        ventana.geometry("430x300")
        ventana.configure(bg=self.color_tarjeta)
        ventana.resizable(False, False)
        ventana.transient(self.master)
        ventana.grab_set()
        ventana.protocol("WM_DELETE_WINDOW", self._cerrar_popup_ajuste)
        self.ventana_ajuste = ventana

        frame = tk.Frame(ventana, bg=self.color_tarjeta, padx=18, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            frame,
            text="Descuento o interes",
            bg=self.color_tarjeta,
            fg=self.color_texto,
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Label(
            frame,
            text="Elegi el tipo de ajuste y confirma para aplicarlo al total actual.",
            bg=self.color_tarjeta,
            fg=self.color_secundario,
            font=self.font_pequena,
            wraplength=360,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 14))

        tipo_var = tk.StringVar(value=self.ajuste_tipo_var.get())
        modo_var = tk.StringVar(value=self.ajuste_modo_var.get())
        valor_var = tk.StringVar(value=self.ajuste_valor_var.get())
        preview_var = tk.StringVar()

        tk.Label(frame, text="Tipo:", bg=self.color_tarjeta, font=self.font_labels).grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=5
        )
        combo_tipo = ttk.Combobox(
            frame,
            textvariable=tipo_var,
            values=["ninguno", "descuento", "interes"],
            state="readonly",
            width=18,
        )
        combo_tipo.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(frame, text="Aplicar como:", bg=self.color_tarjeta, font=self.font_labels).grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=5
        )
        combo_modo = ttk.Combobox(
            frame,
            textvariable=modo_var,
            values=["porcentaje", "monto"],
            state="readonly",
            width=18,
        )
        combo_modo.grid(row=3, column=1, sticky="ew", pady=5)

        tk.Label(frame, text="Valor:", bg=self.color_tarjeta, font=self.font_labels).grid(
            row=4, column=0, sticky="w", padx=(0, 10), pady=5
        )
        entry_valor = tk.Entry(
            frame,
            textvariable=valor_var,
            font=self.font_labels,
            relief="solid",
            bd=1,
        )
        entry_valor.grid(row=4, column=1, sticky="ew", pady=5)

        preview_label = tk.Label(
            frame,
            textvariable=preview_var,
            bg=self.color_tarjeta,
            fg="#555",
            font=("Segoe UI", 10),
            wraplength=360,
            justify="left",
        )
        preview_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 12))

        def actualizar_preview(event=None):
            datos = self.calcular_totales_con_ajuste(
                tipo=tipo_var.get(),
                modo=modo_var.get(),
                valor=valor_var.get(),
            )
            preview_var.set(self._texto_resumen_ajuste(datos))
            if tipo_var.get() == "ninguno":
                combo_modo.state(["disabled"])
                entry_valor.configure(state="disabled")
            else:
                combo_modo.state(["!disabled"])
                entry_valor.configure(state="normal")

        combo_tipo.bind("<<ComboboxSelected>>", actualizar_preview)
        combo_modo.bind("<<ComboboxSelected>>", actualizar_preview)
        entry_valor.bind("<KeyRelease>", actualizar_preview)
        actualizar_preview()

        botones = tk.Frame(frame, bg=self.color_tarjeta)
        botones.grid(row=6, column=0, columnspan=2, sticky="e")

        tk.Button(
            botones,
            text="Limpiar",
            command=lambda: self._limpiar_popup_ajuste(tipo_var, modo_var, valor_var, actualizar_preview),
            bg="#e5e7eb",
            fg="#111827",
            font=self.font_pequena,
            relief="flat",
            padx=14,
            pady=7,
            bd=0,
            activebackground="#d1d5db",
            activeforeground="#111827",
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            botones,
            text="Cancelar",
            command=self._cerrar_popup_ajuste,
            bg="#e5e7eb",
            fg="#111827",
            font=self.font_pequena,
            relief="flat",
            padx=14,
            pady=7,
            bd=0,
            activebackground="#d1d5db",
            activeforeground="#111827",
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            botones,
            text="Aplicar",
            command=lambda: self._aplicar_ajuste_desde_popup(
                tipo_var.get(),
                modo_var.get(),
                valor_var.get(),
            ),
            bg=self.color_exito,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=16,
            pady=7,
            bd=0,
            activebackground=self.color_exito_hover,
            activeforeground="white",
            cursor="hand2",
        ).pack(side=tk.LEFT)

    def _limpiar_popup_ajuste(self, tipo_var, modo_var, valor_var, actualizar_preview):
        tipo_var.set("ninguno")
        modo_var.set("porcentaje")
        valor_var.set("")
        actualizar_preview()

    def _aplicar_ajuste_desde_popup(self, tipo, modo, valor):
        if tipo == "ninguno":
            modo = "porcentaje"
            valor = ""

        self.ajuste_tipo_var.set(tipo)
        self.ajuste_modo_var.set(modo)
        self.ajuste_valor_var.set((valor or "").strip())
        self.actualizar_total()
        self._cerrar_popup_ajuste()

    def _cerrar_popup_ajuste(self):
        ventana = self.ventana_ajuste
        self.ventana_ajuste = None
        if not ventana:
            return
        try:
            ventana.grab_release()
        except tk.TclError:
            pass
        try:
            if ventana.winfo_exists():
                ventana.destroy()
        except tk.TclError:
            pass

    def mostrar_productos_stock_bajo(self, frame):
        stock_frame = tk.LabelFrame(self.stock_bajo_frame, text="Stock bajo",
                            bg=self.color_tarjeta, fg=self.color_texto, font=self.font_labels, bd=1, relief="solid")
        stock_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_stock_bajo = ttk.Treeview(stock_frame, columns=("ID", "Nombre", "Stock"), show="headings", height=10, style="Caja.Treeview")
        self.tree_stock_bajo.heading("ID", text="ID")
        self.tree_stock_bajo.heading("Nombre", text="Nombre")
        self.tree_stock_bajo.heading("Stock", text="Stock")
        self.tree_stock_bajo.column("ID", width=50, anchor="center")
        self.tree_stock_bajo.column("Nombre", width=150, anchor="w")
        self.tree_stock_bajo.column("Stock", width=90, anchor="center")
        self.tree_stock_bajo.pack(fill=tk.BOTH, expand=True)

        productos_bajo = listar_productos_con_stock_bajo()[:10]
        for p in productos_bajo:
            self.tree_stock_bajo.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["nombre"],
                    formatear_cantidad(p.get("stock_actual", 0), producto=p, con_unidad=True),
                ),
            )


    def cambiar_forma_pago(self, forma):
        self.forma_pago_var.set(forma)

        # Cambiar estilos de botones
        for v, btn in self.botones_pago.items():
            if v == forma:
                color, color_hover = self._colores_forma_pago(v)
                btn.config(bg=color, fg="white", activebackground=color_hover, activeforeground="white")
            else:
                btn.config(bg="#e5e7eb", fg="#111827", activebackground="#d1d5db", activeforeground="#111827")

        self._cliente_panel_expandido = False
        self._ocultar_sugerencias_cliente()

        if forma == "efectivo":
            # Mostrar campo de pago y vuelto
            self.fila_pago_frame.pack(fill=tk.X, pady=(10, 0))
            self.entry_pago.configure(state="normal")
            if not self.vuelto_label.winfo_ismapped():
                self.vuelto_label.pack(anchor="w")
            self.actualizar_vuelto()

        else:
            # Ocultar campo de pago y vuelto
            self.fila_pago_frame.pack_forget()
            self.vuelto_label.pack_forget()
            self.entry_pago.delete(0, tk.END)

        self._actualizar_panel_cliente()


    # Resto de métodos sin cambios...
    def actualizar_stock_bajo(self):
        productos_bajo_stock = listar_productos_con_stock_bajo()
        self.tree_stock_bajo.delete(*self.tree_stock_bajo.get_children())
        for producto in productos_bajo_stock[:10]:
            self.tree_stock_bajo.insert(
                "",
                tk.END,
                values=(
                    producto["id"],
                    producto["nombre"],
                    formatear_cantidad(producto.get("stock_actual", 0), producto=producto, con_unidad=True),
                ),
            )

    def agregar_producto(self, event=None):
        if not self.permisos.get("usar_caja"):
            return

        # Verifica desde qué widget vino el Enter
        if event:
            if event.widget not in [self.entrada_id, self.entrada_cantidad]:
                return  # No hacer nada si Enter se presionó fuera de estos dos campos

        producto = self._resolver_producto_desde_entrada()
        if not producto:
            messagebox.showerror(
                "Error",
                "No se pudo identificar el producto. Buscalo por ID o nombre y, si hace falta, elegilo de la lista.",
            )
            return

        try:
            cantidad = parsear_cantidad_para_producto(
                self.entrada_cantidad.get().strip(),
                producto=producto,
            )
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            self._restablecer_cantidad_producto(producto)
            return

        prod_id = int(producto["id"])

        for p in self.carrito:
            if p["id"] == prod_id:
                p["cantidad"] = parsear_cantidad_para_producto(
                    float(p.get("cantidad", 0) or 0) + float(cantidad),
                    producto=producto,
                )
                self.actualizar_lista()
                self.actualizar_total()
                self._limpiar_busqueda_producto()
                self._restablecer_cantidad_producto()
                return

        self.carrito.append({
            "id": prod_id,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": cantidad,
            "tipo_venta": producto.get("tipo_venta", "unidad"),
            "unidad_medida": obtener_unidad_medida(producto=producto),
        })

        self.actualizar_lista()
        self.actualizar_total()
        self._limpiar_busqueda_producto()
        self._restablecer_cantidad_producto()


    def actualizar_lista(self):
        self.lista_productos.delete(0, tk.END)
        if not self.carrito:
            if self.label_resumen_carrito:
                self.label_resumen_carrito.config(text="Aún no agregaste productos.")
            self.lista_productos.insert(tk.END, "No hay productos cargados en el carrito.")
            return

        if self.label_resumen_carrito:
            self.label_resumen_carrito.config(
                text=f"{len(self.carrito)} productos distintos | {self._texto_resumen_cantidades_carrito()} cargados"
            )
        for p in self.carrito:
            self.lista_productos.insert(tk.END, self._texto_item_carrito(p))

    def _actualizar_total_responsive(self, event=None):
        datos = self.calcular_totales_con_ajuste()
        self.total_label.config(text=f"Total: ${datos['total_final']:.2f}")
        self.ajuste_resumen_var.set(self._texto_resumen_ajuste(datos))
        self._actualizar_boton_ajuste(datos)
        self.actualizar_vuelto()

    def actualizar_total(self, event=None):
        datos = self.calcular_totales_con_ajuste()

        self.total_label.config(
            text=f"Total: ${datos['total_final']:.2f}"
        )

        if self.ajuste_info_label:
            if datos["tipo"] in ["descuento", "interes"] and datos["importe_aplicado"] > 0:
                signo = "-" if datos["tipo"] == "descuento" else "+"
                etiqueta_tipo = "Descuento" if datos["tipo"] == "descuento" else "Interés"

                if datos["modo"] == "porcentaje":
                    detalle = f"{etiqueta_tipo}: {signo}${datos['importe_aplicado']:.2f} ({datos['valor']:.2f}%)"
                else:
                    detalle = f"{etiqueta_tipo}: {signo}${datos['importe_aplicado']:.2f}"

                self.ajuste_info_label.config(
                    text=f"Subtotal: ${datos['subtotal']:.2f} | {detalle}"
                )
            else:
                self.ajuste_info_label.config(
                    text=f"Subtotal: ${datos['subtotal']:.2f} | Sin ajuste aplicado"
                )

        self.actualizar_vuelto()

    def actualizar_vuelto(self, event=None):
        try:
            pago = float(self.entry_pago.get())
        except ValueError:
            self.vuelto_label.config(text="Vuelto: $0.00")
            return

        datos = self.calcular_totales_con_ajuste()
        total = datos["total_final"]

        vuelto = pago - total
        self.vuelto_label.config(
            text=f"Vuelto: ${vuelto:.2f}" if vuelto >= 0 else "Vuelto: $0.00"
        )

    def cambiar_cantidad_seleccionada(self):
        seleccion = self.lista_productos.curselection()
        if not seleccion:
            return
        index = seleccion[0]
        if index >= len(self.carrito):
            return
        producto = self.carrito[index]
        if producto_se_vende_por_kilo(tipo_venta=producto.get("tipo_venta")):
            nueva_cantidad = simpledialog.askstring(
                "Modificar cantidad",
                f"Cantidad en kg para {producto['nombre']}",
                initialvalue=formatear_cantidad(producto.get("cantidad", 0), tipo_venta=producto.get("tipo_venta")),
            )
            if nueva_cantidad is None:
                return
            try:
                self.carrito[index]["cantidad"] = parsear_cantidad_para_producto(
                    nueva_cantidad,
                    tipo_venta=producto.get("tipo_venta"),
                )
            except ValueError as error:
                messagebox.showerror("Error", str(error))
                return
        else:
            nueva_cantidad = simpledialog.askinteger(
                "Modificar cantidad",
                f"Cantidad para {producto['nombre']}",
                initialvalue=int(float(producto.get("cantidad", 0) or 0)),
            )
            if nueva_cantidad is None:
                return
            if nueva_cantidad <= 0:
                del self.carrito[index]
            else:
                self.carrito[index]["cantidad"] = nueva_cantidad

        self.actualizar_lista()
        self.actualizar_total()

    def eliminar_producto_seleccionado(self):
        seleccion = self.lista_productos.curselection()
        if seleccion and seleccion[0] < len(self.carrito):
            del self.carrito[seleccion[0]]
            self.actualizar_lista()
            self.actualizar_total()

    def _limpiar_despues_de_venta_responsive(self):
        self.carrito.clear()
        self.lista_productos.delete(0, tk.END)
        self.actualizar_stock_bajo()
        self.forma_pago_var.set("efectivo")
        self.seleccionar_forma_pago("efectivo")
        self.total_label.config(text="Total: $0.00")
        self.vuelto_label.config(text="Vuelto: $0.00")
        self.entry_pago.delete(0, tk.END)
        self.entry_dni.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self._cliente_panel_expandido = False
        self._ocultar_sugerencias_cliente()
        self.ajuste_tipo_var.set("ninguno")
        self.ajuste_modo_var.set("porcentaje")
        self.ajuste_valor_var.set("")
        self._cerrar_popup_ajuste()
        self._actualizar_panel_cliente()
        self.actualizar_total()

    def limpiar_despues_de_venta(self):
        self.carrito.clear()
        self.lista_productos.delete(0, tk.END)
        self.actualizar_stock_bajo()
        self.forma_pago_var.set("efectivo")
        self.seleccionar_forma_pago("efectivo")
        self.total_label.config(text="Total: $0.00")
        self.vuelto_label.config(text="Vuelto: $0.00")
        self.entry_pago.delete(0, tk.END)
        self.entry_dni.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self._cliente_panel_expandido = False
        self._ocultar_sugerencias_cliente()
        self.ajuste_tipo_var.set("ninguno")
        self.ajuste_modo_var.set("porcentaje")
        self.ajuste_valor_var.set("")
        
        if self.ajuste_info_label:
            self.ajuste_info_label.config(text="Sin ajuste aplicado")
        self._actualizar_panel_cliente()


    def confirmar_venta(self):
        if not self.permisos.get("usar_caja"):
            return

        if not self.carrito:
            messagebox.showerror("Error", "No hay productos en la venta.")
            return

        datos = self.calcular_totales_con_ajuste()
        total_final = datos["total_final"]

        try:
            pago = float(self.entry_pago.get() or 0)
        except ValueError:
            pago = 0

        forma = self.forma_pago_var.get()
        nombre = self.entry_nombre.get().strip()
        dni = self.entry_dni.get().strip()

        if forma in ["deuda", "debito"]:
            cliente = self._resolver_cliente_para_pago()
            if not cliente:
                self._cliente_panel_expandido = True
                self._actualizar_panel_cliente()
                messagebox.showerror(
                    "Error",
                    "Para deuda o débito ingresá al menos un nombre, alias, DNI o referencia del cliente.",
                )
                return

            dni = cliente.get("dni", "")
            nombre = cliente.get("nombre", "")
            self.entry_dni.delete(0, tk.END)
            self.entry_dni.insert(0, dni)
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.insert(0, nombre)
            self._cliente_panel_expandido = False
            self._actualizar_panel_cliente()

        if forma not in ["deuda", "debito"] and pago < total_final:
            messagebox.showerror("Error", "El pago es insuficiente.")
            return

        ajuste = {
            "tipo": datos["tipo"],
            "modo": datos["modo"],
            "valor": datos["valor"],
            "importe_aplicado": datos["importe_aplicado"]
        }

        ok = registrar_venta(
            self.carrito,
            forma,
            dni or None,
            nombre or None,
            ajuste=ajuste
        )

        if not ok:
            messagebox.showerror("Error", "No se pudo registrar la venta.")
            return

        self.vuelto_label.config(
            text=f"Vuelto: ${pago - total_final:.2f}" if forma not in ["deuda", "debito"] else "Vuelto: $0.00"
        )

        self.carrito = []
        self.limpiar_despues_de_venta()
        messagebox.showinfo("Venta confirmada", "La venta se realizó con éxito.")

    def cerrar_sesion_y_volver_al_login(self):
        cerrar_sesion()
        self.ir_a_login(self.master)

    # --- POPUPS DE ADMINISTRACIÓN ---
    def abrir_popup_productos(self):
        PantallaProductos(self.master, solo_lectura=not self.permisos.get("gestionar_productos"))

    def abrir_popup_ventas(self):
        PantallaVentas(self.master)

    def abrir_popup_registros(self):
        PantallaRegistros(self.master)

    def abrir_popup_deudas(self):
        PantallaDeudas(self.master)

    def abrir_popup_debito(self):
        PantallaDebitos(self.master)

    def abrir_popup_clientes(self):
        PantallaClientes(self.master)

    def abrir_popup_reportes(self):
        PantallaReportes(self.master)

    def abrir_popup_empleados(self):
        PantallaEmpleados(self.master)

    def crear_popup(self, titulo):
        popup = tk.Toplevel(self.master)
        popup.title(titulo)
        popup.geometry("800x600")
