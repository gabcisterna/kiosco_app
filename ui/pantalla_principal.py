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
        self.master.title("Caja - Supermercado")
        self.master.configure(bg="#f0f4f8")
        self.master.attributes('-fullscreen', True)
        self.master.bind("<Escape>", lambda e: self.master.attributes("-fullscreen", False))
        self.master.bind("<Return>", self.agregar_producto)
        self.master.bind("<F2>", lambda event: self.confirmar_venta())
        self.ajuste_tipo_var = tk.StringVar(value="ninguno")       # ninguno / descuento / interes
        self.ajuste_modo_var = tk.StringVar(value="porcentaje")    # porcentaje / monto
        self.ajuste_valor_var = tk.StringVar(value="")
        self.ajuste_info_label = None


        self.carrito = []
        self.empleado = obtener_empleado_activo()
        self.permisos = obtener_permisos_empleado(self.empleado)

        # Fuentes
        self.font_lista = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_labels = font.Font(family="Segoe UI", size=12)
        self.font_pequena = font.Font(family="Segoe UI", size=10)
        self.font_busqueda = font.Font(family="Segoe UI", size=17, weight="bold")
        self.font_sugerencias = font.Font(family="Segoe UI", size=12)

        main_frame = tk.Frame(master, bg="#f0f4f8", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.crear_barra_superior_completa(main_frame)

        if not self.permisos.get("usar_caja"):
            self.crear_panel_sin_caja(main_frame)
            return

        # Dividir en dos columnas
        self.izquierda_frame = tk.Frame(main_frame, bg="#f0f4f8")
        self.izquierda_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.derecha_frame = tk.Frame(main_frame, bg="#f0f4f8")
        self.derecha_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        # Parte izquierda
        self.crear_lista_productos(self.izquierda_frame)
        self.crear_entrada_producto(self.izquierda_frame)
        self.mostrar_productos_stock_bajo(self.izquierda_frame)
        # Eliminamos la creación de botones aquí:
        # self.crear_botones_y_finalizar(self.izquierda_frame)

        # Parte derecha
        self.crear_info_pago(self.derecha_frame)
        self.crear_total_y_vuelto(self.derecha_frame)

        # Ahora los botones van en la derecha, debajo del total y vuelto:
        self.crear_botones_y_finalizar(self.derecha_frame)

    def calcular_totales_con_ajuste(self):
        subtotal = sum(p["cantidad"] * p["precio"] for p in self.carrito)

        tipo = self.ajuste_tipo_var.get()
        modo = self.ajuste_modo_var.get()

        try:
            valor = float(self.ajuste_valor_var.get() or 0)
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
        barra_superior = tk.Frame(frame, bg="#dce6f0", pady=10, padx=20, bd=1, relief="ridge")
        barra_superior.pack(fill=tk.X, pady=(0, 15))

        # Empleado activo (izquierda)
        tk.Label(barra_superior, text=f"Empleado activo: {self.empleado['nombre']} | Puesto: {self.empleado['puesto']}",
                font=self.font_labels, bg="#dce6f0", fg="#333").pack(side=tk.LEFT)

        # Botones administración (centro)
        botones_frame = tk.Frame(barra_superior, bg="#dce6f0")
        botones_frame.pack(side=tk.LEFT, expand=True)

        for texto, comando in self._definir_botones_admin():
            tk.Button(
                botones_frame, text=texto, command=comando,
                bg="#4a90e2", fg="white", font=self.font_labels,
                relief="flat", padx=15, pady=7
            ).pack(side=tk.LEFT, padx=5)

        # Cerrar sesión (derecha)
        tk.Button(barra_superior, text="Cerrar sesión", command=self.cerrar_sesion_y_volver_al_login,
                bg="#e94e4e", fg="white", font=self.font_labels,
                relief="flat", padx=12, pady=7).pack(side=tk.RIGHT)


    def crear_entrada_producto(self, frame):
        sub_frame = tk.Frame(frame, bg="#f0f4f8")
        sub_frame.pack(pady=(10, 15), fill=tk.X)
        sub_frame.grid_columnconfigure(1, weight=1)

        # --- ID o nombre del producto ---
        tk.Label(sub_frame, text="Buscar producto:", font=("Segoe UI", 13, "bold"), bg="#f0f4f8", fg="#333").grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.entrada_id = tk.Entry(sub_frame, font=self.font_busqueda, relief="solid", bd=2, width=34, bg="white")
        self.entrada_id.grid(row=0, column=1, padx=(0, 20), sticky="ew", ipady=6)
        self.entrada_id.bind("<KeyRelease>", self.autocompletar_producto)

        # Lista de sugerencias (se crea pero se oculta hasta que haya sugerencias)
        self.lista_sugerencias = tk.Listbox(sub_frame, font=self.font_sugerencias, height=7, width=44, bg="white", fg="black", relief="solid", bd=1)
        self.lista_sugerencias.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(4, 5))
        self.lista_sugerencias.bind("<<ListboxSelect>>", self.seleccionar_sugerencia)
        self.lista_sugerencias.bind("<Double-Button-1>", self.seleccionar_sugerencia)
        self.lista_sugerencias.grid_remove()  # Oculta inicialmente

        # --- Cantidad ---
        tk.Label(sub_frame, text="Cantidad:", font=("Segoe UI", 13, "bold"), bg="#f0f4f8", fg="#333").grid(row=0, column=2, sticky="w", padx=(0, 8))

        self.entrada_cantidad = tk.Entry(sub_frame, font=("Segoe UI", 15, "bold"), relief="solid", bd=2, width=8, bg="white")
        self.entrada_cantidad.grid(row=0, column=3, padx=(0, 20), ipady=6)
        self.entrada_cantidad.insert(0, "1")  # Valor por defecto: 1

        # --- Botón para agregar al carrito ---
        btn_agregar = tk.Button(sub_frame, text="Agregar", command=self.agregar_producto,
                                font=("Segoe UI", 13, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=16, pady=8)
        btn_agregar.grid(row=0, column=4)




    def crear_lista_productos(self, frame):
        # Frame que contiene carrito y stock bajo
        lista_y_stock_frame = tk.Frame(frame, bg="#f0f4f8")
        lista_y_stock_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # ----- COLUMNA IZQUIERDA: Carrito -----
        carrito_frame = tk.Frame(lista_y_stock_frame, bg="#f0f4f8")
        carrito_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Título como en stock bajo
        tk.Label(carrito_frame, text="Productos en el carrito", bg="#f0f4f8",
                fg="#333", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=5, pady=(0, 5))

        # Listbox con borde visual limpio
        lista_frame = tk.Frame(carrito_frame, bg="#f0f4f8", bd=1, relief="solid")
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        self.lista_productos = tk.Listbox(lista_frame, font=self.font_lista, height=15,
                                        bg="white", fg="#222", selectbackground="#4a90e2",
                                        activestyle="none", relief="flat", bd=0)
        self.lista_productos.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Limpiar cualquier contenido previo por seguridad (puede prevenir "residuos")
        self.lista_productos.delete(0, tk.END)

        # ----- COLUMNA DERECHA: Stock bajo -----
        self.stock_bajo_frame = tk.Frame(lista_y_stock_frame, bg="#f0f4f8", width=300)
        self.stock_bajo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))



    def crear_botones_y_finalizar(self, frame):
        # --- Acciones ---
        tk.Label(frame, text="Acciones", font=("Segoe UI", 16, "bold"), bg="#f0f4f8", fg="#333").pack(anchor="w", padx=10, pady=(10, 5))

        botones_frame = tk.Frame(frame, bg="#f0f4f8")
        botones_frame.pack(pady=(10, 10))

        tk.Button(botones_frame, text="Modificar cantidad", command=self.cambiar_cantidad_seleccionada,
                bg="#ffa500", fg="white", font=self.font_labels, relief="flat", padx=15, pady=7).pack(side=tk.LEFT, padx=5)

        tk.Button(botones_frame, text="Eliminar producto", command=self.eliminar_producto_seleccionado,
                bg="#e94e4e", fg="white", font=self.font_labels, relief="flat", padx=15, pady=7).pack(side=tk.LEFT, padx=5)

        tk.Button(botones_frame, text="🛒 FINALIZAR VENTA (F2)", command=self.confirmar_venta,
                bg="#2e7d32", fg="white", font=self.font_labels, relief="flat", padx=15, pady=7).pack(side=tk.LEFT, padx=5)



    def crear_info_pago(self, frame):
        # --- Datos del cliente ---
        tk.Label(frame, text="Datos del cliente", font=("Segoe UI", 16, "bold"), bg="#f0f4f8", fg="#333").pack(anchor="w", padx=10, pady=(0, 5))

        # DATOS DEL CLIENTE
        cliente_frame = tk.LabelFrame(frame, text="Datos del cliente", bg="#ffffff", fg="#333", font=self.font_labels, padx=10, pady=10)
        cliente_frame.pack(fill=tk.X, pady=(10, 10), padx=10)

        self.label_dni = tk.Label(cliente_frame, text="DNI (opcional):", font=self.font_pequena, bg="#ffffff", fg="#555")
        self.label_dni.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.entry_dni = tk.Entry(cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f0f4f8", width=20)
        self.entry_dni.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))
        self.entry_dni.bind("<KeyRelease>", self.autocompletar_cliente)

        self.label_nombre = tk.Label(cliente_frame, text="Nombre (opcional):", font=self.font_pequena, bg="#ffffff", fg="#555")
        self.label_nombre.grid(row=0, column=1, sticky="w")
        self.entry_nombre = tk.Entry(cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f0f4f8", width=25)
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
        forma_frame = tk.LabelFrame(frame, text="Forma de pago", bg="#ffffff", fg="#333", font=self.font_labels, padx=10, pady=10)
        forma_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        # Botones
        self.forma_pago_var = tk.StringVar(value="efectivo")
        formas = [("Efectivo", "efectivo"), ("Débito", "debito"), ("Deuda", "deuda")]

        self.botones_pago = {}
        for texto, valor in formas:
            btn = tk.Button(forma_frame, text=texto, font=self.font_pequena,
                            bg="#e0e0e0" if self.forma_pago_var.get() != valor else "#4a90e2",
                            fg="black" if self.forma_pago_var.get() != valor else "white",
                            relief="solid", bd=1, padx=10, pady=5,
                            command=lambda v=valor: self.seleccionar_forma_pago(v))
            btn.pack(side=tk.LEFT, padx=5)
            self.botones_pago[valor] = btn

        # Campo "Con cuánto paga"
        self.label_pago = tk.Label(forma_frame, text="Con cuánto paga:", font=self.font_pequena, bg="#ffffff", fg="#555")
        self.label_pago.pack(side=tk.LEFT, padx=(20, 5))
        self.entry_pago = tk.Entry(forma_frame, font=self.font_labels, relief="solid", bd=1, bg="#f0f4f8", width=10)
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


    def seleccionar_forma_pago(self, valor):
        self.forma_pago_var.set(valor)
        for v, btn in self.botones_pago.items():
            if v == valor:
                btn.config(bg="#4a90e2", fg="white")
            else:
                btn.config(bg="#e0e0e0", fg="black")
        self.cambiar_forma_pago(valor)


    def crear_total_y_vuelto(self, frame):
        # --- Resumen de pago ---
        tk.Label(frame, text="Resumen de pago", font=("Segoe UI", 16, "bold"), bg="#f0f4f8", fg="#333").pack(anchor="w", padx=10, pady=(10, 5))

        resumen_frame = tk.LabelFrame(frame, text="Resumen de pago", bg="#ffffff", fg="#333", font=self.font_labels, padx=10, pady=10)
        resumen_frame.pack(fill=tk.X, padx=10)

        self.total_label = tk.Label(resumen_frame, text="Total: $0.00",
                            font=("Segoe UI", 24, "bold"), bg="#ffffff", fg="#2e7d32")
        self.total_label.pack(anchor="w", pady=(0, 10))

        ajuste_frame = tk.LabelFrame(
            resumen_frame,
            text="Descuento / Interés",
            bg="#ffffff",
            fg="#333",
            font=self.font_labels,
            padx=10,
            pady=10
        )
        ajuste_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(ajuste_frame, text="Tipo:", bg="#ffffff", font=self.font_labels).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        combo_tipo = ttk.Combobox(
            ajuste_frame,
            textvariable=self.ajuste_tipo_var,
            values=["ninguno", "descuento", "interes"],
            state="readonly",
            width=12
        )
        combo_tipo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(ajuste_frame, text="Aplicar como:", bg="#ffffff", font=self.font_labels).grid(row=0, column=2, sticky="w", padx=5, pady=5)

        combo_modo = ttk.Combobox(
            ajuste_frame,
            textvariable=self.ajuste_modo_var,
            values=["porcentaje", "monto"],
            state="readonly",
            width=12
        )
        combo_modo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(ajuste_frame, text="Valor:", bg="#ffffff", font=self.font_labels).grid(row=1, column=0, sticky="w", padx=5, pady=5)

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
            bg="#ffffff",
            fg="#555",
            font=("Segoe UI", 10)
        )
        self.ajuste_info_label.grid(row=1, column=2, columnspan=2, sticky="w", padx=5, pady=5)

        combo_tipo.bind("<<ComboboxSelected>>", lambda e: self.actualizar_total())
        combo_modo.bind("<<ComboboxSelected>>", lambda e: self.actualizar_total())
        entry_ajuste.bind("<KeyRelease>", self.actualizar_total)

        self.vuelto_label = tk.Label(resumen_frame, text="Vuelto: $0.00",
                                    font=("Segoe UI", 20), bg="#ffffff", fg="#c62828")
        self.vuelto_label.pack(anchor="w")



    def mostrar_productos_stock_bajo(self, frame):
        stock_frame = tk.LabelFrame(self.stock_bajo_frame, text="Stock bajo",
                            bg="#f0f4f8", font=self.font_labels)
        stock_frame.pack(fill=tk.BOTH, expand=True)

        self.tree_stock_bajo = ttk.Treeview(stock_frame, columns=("ID", "Nombre", "Stock"), show="headings", height=10)
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
                btn.config(bg="#4a90e2", fg="white")
            else:
                btn.config(bg="#e0e0e0", fg="black")

        if forma == "efectivo":
            # Mostrar campo de pago y vuelto
            self.label_pago.pack(side=tk.LEFT, padx=(20, 5))
            self.entry_pago.pack(side=tk.LEFT)
            self.entry_pago.configure(state="normal")
            self.label_dni.config(text="DNI del cliente (opcional):")
            self.label_nombre.config(text="Nombre del cliente (opcional):")
            self.entry_dni.config(bg="#f0f4f8")
            self.entry_nombre.config(bg="#f0f4f8")
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
        for p in self.carrito:
            subtotal = p["cantidad"] * p["precio"]
            texto = f"{p['cantidad']} x {p['nombre']} - ${p['precio']:.2f} c/u = ${subtotal:.2f}"
            self.lista_productos.insert(tk.END, texto)

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
        self.master.destroy()
        nuevo_root = tk.Tk()
        self.ir_a_login(nuevo_root)
        nuevo_root.mainloop()

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
