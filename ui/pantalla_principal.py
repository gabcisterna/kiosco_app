import tkinter as tk
from tkinter import messagebox, simpledialog, font, ttk
from modules.clientes import buscar_clientes_por_texto, resolver_cliente_para_venta
from modules.empleados import obtener_empleado_activo, obtener_permisos_empleado
from modules.login import cerrar_sesion
from modules.productos import (
    buscar_producto,
    buscar_productos_por_texto,
    listar_productos_con_stock_bajo,
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
        self.master.attributes('-fullscreen', True)
        self.master.bind("<Escape>", lambda e: self.master.attributes("-fullscreen", False))
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

        self.carrito = []
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

        # Parte izquierda
        self.crear_lista_productos(self.izquierda_frame)
        self.crear_entrada_producto(self.izquierda_frame)
        self.mostrar_productos_stock_bajo(self.izquierda_frame)
        # Eliminamos la creación de botones aquí:
        # self.crear_botones_y_finalizar(self.izquierda_frame)

        # Parte derecha
        self.crear_info_pago(self.derecha_frame)
        self.crear_total_y_vuelto_responsive(self.derecha_frame)

        # Ahora los botones van en la derecha, debajo del total y vuelto:
        self.crear_botones_y_finalizar(self.derecha_frame)
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

    def _widget_existe(self, widget):
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False

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
        layout = "vertical" if ancho_actual < 1480 else "horizontal"

        if layout == self._layout_actual:
            return

        self._layout_actual = layout
        self.izquierda_frame.pack_forget()
        self.derecha_frame.pack_forget()

        if layout == "vertical":
            self.izquierda_frame.pack(fill=tk.BOTH, expand=True)
            self.derecha_frame.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
            return

        self.izquierda_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.derecha_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

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
        barra_superior = tk.Frame(frame, bg="#102a43", pady=14, padx=20, bd=0)
        barra_superior.pack(fill=tk.X, pady=(0, 15))

        # Empleado activo (izquierda)
        bloque_titulo = tk.Frame(barra_superior, bg="#102a43")
        bloque_titulo.pack(side=tk.LEFT, padx=(0, 18))
        tk.Label(
            bloque_titulo,
            text="Caja activa",
            font=("Segoe UI", 18, "bold"),
            bg="#102a43",
            fg="white",
        ).pack(anchor="w")
        tk.Label(
            bloque_titulo,
            text=f"Empleado: {self.empleado['nombre']} | Puesto: {self.empleado['puesto']}",
            font=("Segoe UI", 10),
            bg="#102a43",
            fg="#d9e2ec",
        ).pack(anchor="w")

        # Botones administración (centro)
        botones_frame = tk.Frame(barra_superior, bg="#102a43")
        botones_frame.pack(side=tk.LEFT, expand=True)

        for texto, comando in self._definir_botones_admin():
            tk.Button(
                botones_frame, text=texto, command=comando,
                bg="#1f6aa5", fg="white", font=("Segoe UI", 10, "bold"),
                relief="flat", padx=14, pady=7, bd=0,
                activebackground="#17537f", activeforeground="white",
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

        # Cerrar sesión (derecha)
        tk.Button(
            barra_superior,
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
        ).pack(side=tk.RIGHT)


    def crear_entrada_producto(self, frame):
        tarjeta = self._crear_tarjeta(frame, pady=(0, 14))
        tarjeta.pack(**tarjeta._pack_config)
        sub_frame = tk.Frame(tarjeta, bg=self.color_tarjeta, padx=18, pady=16)
        sub_frame.pack(fill=tk.X)
        sub_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            sub_frame,
            text="Agregar producto",
            font=("Segoe UI", 16, "bold"),
            bg=self.color_tarjeta,
            fg=self.color_texto,
        ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 4))
        tk.Label(
            sub_frame,
            text="Buscá por ID o nombre y cargá la cantidad antes de agregar al carrito.",
            font=self.font_subtitulo,
            bg=self.color_tarjeta,
            fg=self.color_secundario,
        ).grid(row=1, column=0, columnspan=5, sticky="w", pady=(0, 12))

        # --- ID o nombre del producto ---
        tk.Label(sub_frame, text="Buscar producto:", font=("Segoe UI", 13, "bold"), bg=self.color_tarjeta, fg=self.color_texto).grid(row=2, column=0, sticky="w", padx=(0, 8))

        self.entrada_id = tk.Entry(sub_frame, font=self.font_busqueda, relief="solid", bd=2, width=34, bg="white")
        self.entrada_id.grid(row=2, column=1, padx=(0, 20), sticky="ew", ipady=6)
        self.entrada_id.bind("<KeyRelease>", self.autocompletar_producto)

        # Lista de sugerencias (se crea pero se oculta hasta que haya sugerencias)
        self.lista_sugerencias = tk.Listbox(sub_frame, font=self.font_sugerencias, height=7, width=44, bg="white", fg="black", relief="solid", bd=1)
        self.lista_sugerencias.grid(row=3, column=1, sticky="ew", padx=(0, 20), pady=(4, 5))
        self.lista_sugerencias.bind("<<ListboxSelect>>", self.seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Double-Button-1>", self.seleccionar_sugerencia)
        self.lista_sugerencias.grid_remove()  # Oculta inicialmente

        # --- Cantidad ---
        tk.Label(sub_frame, text="Cantidad:", font=("Segoe UI", 13, "bold"), bg=self.color_tarjeta, fg=self.color_texto).grid(row=2, column=2, sticky="w", padx=(0, 8))

        self.entrada_cantidad = tk.Entry(sub_frame, font=("Segoe UI", 15, "bold"), relief="solid", bd=2, width=8, bg="white")
        self.entrada_cantidad.grid(row=2, column=3, padx=(0, 20), ipady=6)
        self.entrada_cantidad.insert(0, "1")  # Valor por defecto: 1

        # --- Botón para agregar al carrito ---
        btn_agregar = tk.Button(sub_frame, text="Agregar", command=self.agregar_producto,
                                font=("Segoe UI", 13, "bold"), bg=self.color_exito, fg="white", relief="flat", padx=18, pady=10, bd=0, activebackground=self.color_exito_hover, activeforeground="white", cursor="hand2")
        btn_agregar.grid(row=2, column=4)




    def crear_lista_productos(self, frame):
        # Frame que contiene carrito y stock bajo
        lista_y_stock_frame = tk.Frame(frame, bg=self.color_fondo)
        lista_y_stock_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # ----- COLUMNA IZQUIERDA: Carrito -----
        carrito_frame = self._crear_tarjeta(lista_y_stock_frame, pady=0)
        carrito_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        encabezado_carrito = tk.Frame(carrito_frame, bg=self.color_tarjeta, padx=16, pady=14)
        encabezado_carrito.pack(fill=tk.X)
        tk.Label(
            encabezado_carrito,
            text="Carrito actual",
            bg=self.color_tarjeta,
            fg=self.color_texto,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        self.label_resumen_carrito = tk.Label(
            encabezado_carrito,
            text="Aún no agregaste productos.",
            bg=self.color_tarjeta,
            fg=self.color_secundario,
            font=self.font_subtitulo,
        )
        self.label_resumen_carrito.pack(anchor="w", pady=(2, 0))

        # Listbox con borde visual limpio
        lista_frame = tk.Frame(carrito_frame, bg=self.color_tarjeta, bd=0)
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))

        self.lista_productos = tk.Listbox(lista_frame, font=self.font_lista, height=15,
                                        bg="white", fg=self.color_texto, selectbackground="#dbeafe",
                                        selectforeground=self.color_texto,
                                        activestyle="none", relief="flat", bd=0)
        self.lista_productos.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Limpiar cualquier contenido previo por seguridad (puede prevenir "residuos")
        self.lista_productos.delete(0, tk.END)

        # ----- COLUMNA DERECHA: Stock bajo -----
        self.stock_bajo_frame = tk.Frame(lista_y_stock_frame, bg=self.color_fondo, width=300)
        self.stock_bajo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))



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
            text="Ajustá el carrito o finalizá la operación desde acá.",
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
            text="Modificar cantidad",
            command=self.cambiar_cantidad_seleccionada,
            bg=self.color_alerta,
            fg="white",
            font=self.font_labels,
            relief="flat",
            padx=15,
            pady=9,
            bd=0,
            activebackground=self.color_alerta_hover,
            activeforeground="white",
            cursor="hand2",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6))

        tk.Button(
            botones_frame,
            text="Eliminar producto",
            command=self.eliminar_producto_seleccionado,
            bg=self.color_peligro,
            fg="white",
            font=self.font_labels,
            relief="flat",
            padx=15,
            pady=9,
            bd=0,
            activebackground=self.color_peligro_hover,
            activeforeground="white",
            cursor="hand2",
        ).grid(row=1, column=1, sticky="ew", padx=(6, 0))

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
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))



    def crear_info_pago(self, frame):
        # --- Datos del cliente ---
        tk.Label(frame, text="Cliente y forma de pago", font=("Segoe UI", 16, "bold"), bg=self.color_fondo, fg=self.color_texto).pack(anchor="w", padx=10, pady=(0, 5))

        # DATOS DEL CLIENTE
        cliente_frame = tk.LabelFrame(frame, text="Datos del cliente", bg=self.color_tarjeta, fg=self.color_texto, font=self.font_labels, padx=12, pady=12, bd=1, relief="solid")
        cliente_frame.pack(fill=tk.X, pady=(10, 10), padx=10)

        self.label_dni = tk.Label(cliente_frame, text="DNI (opcional):", font=self.font_pequena, bg=self.color_tarjeta, fg="#555")
        self.label_dni.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.entry_dni = tk.Entry(cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f8fafc", width=20)
        self.entry_dni.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        self.entry_dni.bind("<KeyRelease>", self.autocompletar_cliente)

        self.label_nombre = tk.Label(cliente_frame, text="Nombre (opcional):", font=self.font_pequena, bg=self.color_tarjeta, fg="#555")
        self.label_nombre.grid(row=0, column=1, sticky="w")
        self.entry_nombre = tk.Entry(cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f8fafc", width=25)
        self.entry_nombre.grid(row=1, column=1, padx=(0, 10), pady=(0, 10))
        self.entry_nombre.bind("<KeyRelease>", self.autocompletar_cliente)

        self.lista_clientes_sugeridos = tk.Listbox(
            cliente_frame,
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
        forma_frame = tk.LabelFrame(frame, text="Forma de pago", bg=self.color_tarjeta, fg=self.color_texto, font=self.font_labels, padx=12, pady=12, bd=1, relief="solid")
        forma_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        # Botones
        self.forma_pago_var = tk.StringVar(value="efectivo")
        formas = [("Efectivo", "efectivo"), ("Débito", "debito"), ("Deuda", "deuda")]

        self.botones_pago = {}
        for texto, valor in formas:
            color_activo, _ = self._colores_forma_pago(valor)
            btn = tk.Button(forma_frame, text=texto, font=self.font_pequena,
                            bg="#e5e7eb" if self.forma_pago_var.get() != valor else color_activo,
                            fg="#111827" if self.forma_pago_var.get() != valor else "white",
                            relief="solid", bd=1, padx=10, pady=5,
                            command=lambda v=valor: self.seleccionar_forma_pago(v))
            btn.pack(side=tk.LEFT, padx=5)
            self.botones_pago[valor] = btn

        # Campo "Con cuánto paga"
        self.label_pago = tk.Label(forma_frame, text="Con cuánto paga:", font=self.font_pequena, bg=self.color_tarjeta, fg="#555")
        self.label_pago.pack(side=tk.LEFT, padx=(20, 5))
        self.entry_pago = tk.Entry(forma_frame, font=self.font_labels, relief="solid", bd=1, bg="#f8fafc", width=10)
        self.entry_pago.pack(side=tk.LEFT)
        self.entry_pago.bind("<KeyRelease>", self.actualizar_vuelto)


    def _ocultar_sugerencias(self):
        self.lista_sugerencias.delete(0, tk.END)
        self.lista_sugerencias.grid_remove()

    def _extraer_id_desde_texto_producto(self, texto):
        candidato = texto.split(" - ", 1)[0].strip()
        if candidato.isdigit():
            return int(candidato)
        return None

    def _buscar_coincidencias_producto(self, texto):
        return buscar_productos_por_texto(texto)[:10]

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

        self.lista_sugerencias.delete(0, tk.END)
        for prod in sugerencias:
            self.lista_sugerencias.insert(tk.END, f"{prod['id']} - {prod['nombre']}")
        self.lista_sugerencias.grid()

    def seleccionar_sugerencia(self, event):
        if not self.lista_sugerencias.curselection():
            return

        seleccion = self.lista_sugerencias.get(self.lista_sugerencias.curselection()[0])
        self.entrada_id.delete(0, tk.END)
        self.entrada_id.insert(0, seleccion)
        self._ocultar_sugerencias()
        self.entrada_cantidad.focus_set()

    def _ocultar_sugerencias_cliente(self):
        self.lista_clientes_sugeridos.delete(0, tk.END)
        self.lista_clientes_sugeridos.grid_remove()

    def _buscar_coincidencias_cliente(self, texto):
        return buscar_clientes_por_texto(texto)[:8]

    def autocompletar_cliente(self, event=None):
        if self.forma_pago_var.get() not in ["deuda", "debito"]:
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
        tk.Label(
            frame,
            text="Resumen de pago",
            font=("Segoe UI", 16, "bold"),
            bg=self.color_fondo,
            fg=self.color_texto,
        ).pack(anchor="w", padx=10, pady=(10, 5))

        resumen_frame = tk.LabelFrame(
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
        resumen_frame.pack(fill=tk.X, padx=10)

        self.total_label = tk.Label(
            resumen_frame,
            text="Total: $0.00",
            font=("Segoe UI", 28, "bold"),
            bg=self.color_tarjeta,
            fg=self.color_exito,
        )
        self.total_label.pack(anchor="w", pady=(0, 10))

        self.ajuste_info_label = tk.Label(
            resumen_frame,
            textvariable=self.ajuste_resumen_var,
            bg=self.color_tarjeta,
            fg="#555",
            font=("Segoe UI", 10),
            justify="left",
            wraplength=420,
        )
        self.ajuste_info_label.pack(anchor="w", pady=(0, 10))

        self.vuelto_label = tk.Label(
            resumen_frame,
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
        self.tree_stock_bajo.column("Stock", width=70, anchor="center")
        self.tree_stock_bajo.pack(fill=tk.BOTH, expand=True)

        productos_bajo = listar_productos_con_stock_bajo()[:10]
        for p in productos_bajo:
            self.tree_stock_bajo.insert("", "end", values=(p["id"], p["nombre"], p["stock_actual"]))


    def cambiar_forma_pago(self, forma):
        self.forma_pago_var.set(forma)

        # Cambiar estilos de botones
        for v, btn in self.botones_pago.items():
            if v == forma:
                color, color_hover = self._colores_forma_pago(v)
                btn.config(bg=color, fg="white", activebackground=color_hover, activeforeground="white")
            else:
                btn.config(bg="#e5e7eb", fg="#111827", activebackground="#d1d5db", activeforeground="#111827")

        if forma == "efectivo":
            # Mostrar campo de pago y vuelto
            self.label_pago.pack(side=tk.LEFT, padx=(20, 5))
            self.entry_pago.pack(side=tk.LEFT)
            self.entry_pago.configure(state="normal")
            self.label_dni.config(text="DNI del cliente (opcional):")
            self.label_nombre.config(text="Nombre del cliente (opcional):")
            self.entry_dni.config(bg="#f8fafc")
            self.entry_nombre.config(bg="#f8fafc")
            self._ocultar_sugerencias_cliente()
            if not self.vuelto_label.winfo_ismapped():
                self.vuelto_label.pack(anchor="w")
            self.actualizar_vuelto()

        else:
            # Ocultar campo de pago y vuelto
            self.label_dni.config(text="DNI o referencia (opcional):")
            self.label_nombre.config(text="Nombre o alias (opcional):")
            self.entry_dni.config(bg="white")
            self.entry_nombre.config(bg="white")
            self.label_pago.pack_forget()
            self.entry_pago.pack_forget()
            self.vuelto_label.pack_forget()
            self.entry_pago.delete(0, tk.END)


    # Resto de métodos sin cambios...
    def actualizar_stock_bajo(self):
        productos_bajo_stock = listar_productos_con_stock_bajo()
        self.tree_stock_bajo.delete(*self.tree_stock_bajo.get_children())
        for producto in productos_bajo_stock[:10]:
            self.tree_stock_bajo.insert("", tk.END, values=(producto["id"], producto["nombre"], producto["stock_actual"]))

    def agregar_producto(self, event=None):
        if not self.permisos.get("usar_caja"):
            return

        # Verifica desde qué widget vino el Enter
        if event:
            if event.widget not in [self.entrada_id, self.entrada_cantidad]:
                return  # No hacer nada si Enter se presionó fuera de estos dos campos

        cant_texto = self.entrada_cantidad.get().strip()

        if not cant_texto.isdigit():
            messagebox.showerror("Error", "La cantidad debe ser numerica")
            return

        cantidad = int(cant_texto)

        if cantidad <= 0:
            messagebox.showerror("Error", "La cantidad debe ser mayor a cero")
            return

        producto = self._resolver_producto_desde_entrada()
        if not producto:
            messagebox.showerror(
                "Error",
                "No se pudo identificar el producto. Buscalo por ID o nombre y, si hace falta, elegilo de la lista.",
            )
            return
        prod_id = int(producto["id"])

        for p in self.carrito:
            if p["id"] == prod_id:
                p["cantidad"] += cantidad
                self.actualizar_lista()
                self.actualizar_total()
                self._limpiar_busqueda_producto()
                self.entrada_cantidad.delete(0, tk.END)
                self.entrada_cantidad.insert(0, "1")
                return

        self.carrito.append({
            "id": prod_id,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": cantidad
        })

        self.actualizar_lista()
        self.actualizar_total()
        self._limpiar_busqueda_producto()
        self.entrada_cantidad.delete(0, tk.END)
        self.entrada_cantidad.insert(0, "1")


    def actualizar_lista(self):
        self.lista_productos.delete(0, tk.END)
        if not self.carrito:
            if self.label_resumen_carrito:
                self.label_resumen_carrito.config(text="Aún no agregaste productos.")
            self.lista_productos.insert(tk.END, "No hay productos cargados en el carrito.")
            return

        total_unidades = sum(producto["cantidad"] for producto in self.carrito)
        if self.label_resumen_carrito:
            self.label_resumen_carrito.config(
                text=f"{len(self.carrito)} productos distintos | {total_unidades} unidades cargadas"
            )
        for p in self.carrito:
            subtotal = p["cantidad"] * p["precio"]
            texto = f"{p['cantidad']} x {p['nombre']} - ${p['precio']:.2f} c/u = ${subtotal:.2f}"
            self.lista_productos.insert(tk.END, texto)

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
        producto = self.carrito[index]
        nueva_cantidad = simpledialog.askinteger("Modificar cantidad", f"Cantidad para {producto['nombre']}", initialvalue=producto["cantidad"])
        if nueva_cantidad is not None:
            if nueva_cantidad <= 0:
                del self.carrito[index]
            else:
                self.carrito[index]["cantidad"] = nueva_cantidad
            self.actualizar_lista()
            self.actualizar_total()

    def eliminar_producto_seleccionado(self):
        seleccion = self.lista_productos.curselection()
        if seleccion:
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
        self._ocultar_sugerencias_cliente()
        self.ajuste_tipo_var.set("ninguno")
        self.ajuste_modo_var.set("porcentaje")
        self.ajuste_valor_var.set("")
        self._cerrar_popup_ajuste()
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
        self._ocultar_sugerencias_cliente()
        self.ajuste_tipo_var.set("ninguno")
        self.ajuste_modo_var.set("porcentaje")
        self.ajuste_valor_var.set("")
        
        if self.ajuste_info_label:
            self.ajuste_info_label.config(text="Sin ajuste aplicado")


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
