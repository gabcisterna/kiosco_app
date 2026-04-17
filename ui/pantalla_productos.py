import tkinter as tk
from tkinter import messagebox, ttk

from modules.productos import (
    TIPO_VENTA_KILO,
    TIPO_VENTA_UNIDAD,
    actualizar_producto,
    agregar_producto,
    buscar_producto,
    buscar_productos_por_texto,
    cargar_productos,
    describir_precio_producto,
    eliminar_producto,
    formatear_cantidad,
    listar_productos_con_stock_bajo,
    normalizar_tipo_venta,
)


class PantallaProductos:
    OPCIONES_TIPO = {
        "Por unidad": TIPO_VENTA_UNIDAD,
        "Por kilo": TIPO_VENTA_KILO,
    }

    def __init__(self, master, solo_lectura=False):
        self.solo_lectura = bool(solo_lectura)
        self.master = tk.Toplevel(master)
        self.master.title("Consulta de Productos" if self.solo_lectura else "Gestion de Productos")
        self.master.geometry("980x680")
        self.master.configure(bg="#f5f5f5")

        self.filtro_var = tk.StringVar(value="Mostrar todos")

        top_frame = tk.Frame(self.master, bg="#f5f5f5")
        top_frame.pack(pady=12, fill=tk.X, padx=20)

        tk.Label(
            top_frame,
            text="Buscar por ID o nombre:",
            bg="#f5f5f5",
            font=("Segoe UI", 11, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.entry_buscar = tk.Entry(
            top_frame,
            font=("Segoe UI", 13),
            relief="solid",
            bd=2,
            bg="white",
            width=36,
        )
        self.entry_buscar.pack(side=tk.LEFT, padx=(0, 12), ipady=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.buscar_producto_dinamico())

        opciones = [
            "Mostrar todos",
            "Stock bajo",
            "Precio mas alto",
            "Precio mas bajo",
        ]
        self.filtro_menu = ttk.Combobox(
            top_frame,
            values=opciones,
            textvariable=self.filtro_var,
            state="readonly",
            width=18,
        )
        self.filtro_menu.pack(side=tk.LEFT)
        self.filtro_menu.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        self.tree = ttk.Treeview(
            self.master,
            columns=("ID", "Nombre", "Tipo", "Precio", "Stock"),
            show="headings",
            height=18,
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Precio", text="Precio")
        self.tree.heading("Stock", text="Stock")
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("Nombre", width=360)
        self.tree.column("Tipo", width=120, anchor=tk.CENTER)
        self.tree.column("Precio", width=150, anchor=tk.CENTER)
        self.tree.column("Stock", width=140, anchor=tk.CENTER)
        self.tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        if self.solo_lectura:
            tk.Label(
                self.master,
                text="Modo solo lectura: podes consultar productos, pero no modificarlos.",
                bg="#f5f5f5",
                fg="#666",
                font=("Segoe UI", 10),
            ).pack(anchor="w", padx=22)
        else:
            boton_frame = tk.Frame(self.master, bg="#f5f5f5")
            boton_frame.pack(pady=10)

            estilo_boton = {
                "font": ("Segoe UI", 10, "bold"),
                "width": 12,
                "bg": "#4CAF50",
                "fg": "white",
                "activebackground": "#45a049",
                "bd": 0,
            }

            tk.Button(
                boton_frame,
                text="Agregar",
                command=self.agregar_producto_ui,
                **estilo_boton,
            ).pack(side=tk.LEFT, padx=10)
            tk.Button(
                boton_frame,
                text="Editar",
                command=self.editar_producto_ui,
                **estilo_boton,
            ).pack(side=tk.LEFT, padx=10)
            tk.Button(
                boton_frame,
                text="Eliminar",
                command=self.eliminar_producto_ui,
                **estilo_boton,
            ).pack(side=tk.LEFT, padx=10)

        self.mostrar_productos()

    def _tipo_label(self, tipo_venta):
        return "Por kilo" if normalizar_tipo_venta(tipo_venta) == TIPO_VENTA_KILO else "Por unidad"

    def _tipo_desde_label(self, texto):
        return self.OPCIONES_TIPO.get(texto, TIPO_VENTA_UNIDAD)

    def _limpiar_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _obtener_productos_base(self):
        filtro = self.filtro_var.get()
        if filtro == "Stock bajo":
            productos = listar_productos_con_stock_bajo()
        else:
            productos = cargar_productos()

        productos = list(productos)

        if filtro == "Precio mas alto":
            productos.sort(key=lambda p: float(p.get("precio", 0)), reverse=True)
        elif filtro == "Precio mas bajo":
            productos.sort(key=lambda p: float(p.get("precio", 0)))
        else:
            productos.sort(key=lambda p: (str(p.get("nombre", "")).lower(), str(p.get("id", ""))))

        return productos

    def _insertar_producto(self, producto):
        self.tree.insert(
            "",
            tk.END,
            iid=producto["id"],
            values=(
                producto["id"],
                producto["nombre"],
                self._tipo_label(producto.get("tipo_venta")),
                describir_precio_producto(producto),
                formatear_cantidad(producto.get("stock_actual", 0), producto=producto, con_unidad=True),
            ),
        )

    def _mostrar_en_tree(self, productos):
        self._limpiar_tree()
        for producto in productos:
            self._insertar_producto(producto)

    def mostrar_productos(self):
        self._mostrar_en_tree(self._obtener_productos_base())

    def buscar_producto_dinamico(self):
        texto = self.entry_buscar.get().strip()
        if not texto:
            self.mostrar_productos()
            return

        ids_permitidos = {str(producto["id"]) for producto in self._obtener_productos_base()}
        productos = [
            producto
            for producto in buscar_productos_por_texto(texto)
            if str(producto["id"]) in ids_permitidos
        ]
        self._mostrar_en_tree(productos)

    def actualizar_lista(self):
        if self.entry_buscar.get().strip():
            self.buscar_producto_dinamico()
        else:
            self.mostrar_productos()

    def _parsear_cantidad_form(self, texto, tipo_venta, campo):
        texto = str(texto or "").strip().replace(",", ".")
        if not texto:
            raise ValueError(f"{campo}: completa el valor.")

        try:
            valor = float(texto)
        except ValueError as exc:
            raise ValueError(f"{campo}: ingresa un numero valido.") from exc

        if valor < 0:
            raise ValueError(f"{campo}: no puede ser negativo.")

        if normalizar_tipo_venta(tipo_venta) == TIPO_VENTA_UNIDAD:
            if not valor.is_integer():
                raise ValueError(f"{campo}: para productos por unidad usa un numero entero.")
            return int(valor)

        return round(valor, 3)

    def _abrir_form_producto(self, producto=None):
        es_edicion = producto is not None
        win = tk.Toplevel(self.master)
        win.title(f"Editar producto #{producto['id']}" if es_edicion else "Agregar producto")
        win.configure(bg="#f5f5f5")
        win.resizable(False, False)
        win.transient(self.master)
        win.grab_set()

        container = tk.Frame(win, bg="#f5f5f5")
        container.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)

        titulo = tk.Label(
            container,
            text=f"Editar producto #{producto['id']}" if es_edicion else "Agregar producto",
            bg="#f5f5f5",
            font=("Segoe UI", 12, "bold"),
        )
        titulo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        id_var = tk.StringVar(value="" if not es_edicion else str(producto.get("id", "")))
        nombre_var = tk.StringVar(value="" if not es_edicion else producto.get("nombre", ""))
        tipo_var = tk.StringVar(value=self._tipo_label((producto or {}).get("tipo_venta")))
        precio_var = tk.StringVar(value="" if not es_edicion else str(producto.get("precio", 0)))
        stock_actual_var = tk.StringVar(value="" if not es_edicion else str(producto.get("stock_actual", 0)))
        stock_minimo_var = tk.StringVar(value="" if not es_edicion else str(producto.get("stock_minimo", 0)))
        ayuda_var = tk.StringVar(value="")

        def label(text, row_index):
            tk.Label(container, text=text, bg="#f5f5f5", font=("Segoe UI", 10)).grid(
                row=row_index,
                column=0,
                sticky="w",
                pady=6,
            )

        def entry(var, row_index):
            campo = ttk.Entry(container, textvariable=var, width=35)
            campo.grid(row=row_index, column=1, sticky="w", pady=6)
            return campo

        fila = 1
        label("ID:", fila)
        e_id = entry(id_var, fila)
        fila += 1

        label("Nombre:", fila)
        e_nombre = entry(nombre_var, fila)
        fila += 1

        label("Tipo de venta:", fila)
        combo_tipo = ttk.Combobox(
            container,
            values=list(self.OPCIONES_TIPO.keys()),
            textvariable=tipo_var,
            state="readonly",
            width=32,
        )
        combo_tipo.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        precio_label = tk.Label(container, text="", bg="#f5f5f5", font=("Segoe UI", 10))
        precio_label.grid(row=fila, column=0, sticky="w", pady=6)
        e_precio = entry(precio_var, fila)
        fila += 1

        stock_label = tk.Label(container, text="", bg="#f5f5f5", font=("Segoe UI", 10))
        stock_label.grid(row=fila, column=0, sticky="w", pady=6)
        e_stock = entry(stock_actual_var, fila)
        fila += 1

        minimo_label = tk.Label(container, text="", bg="#f5f5f5", font=("Segoe UI", 10))
        minimo_label.grid(row=fila, column=0, sticky="w", pady=6)
        e_min = entry(stock_minimo_var, fila)
        fila += 1

        tk.Label(
            container,
            textvariable=ayuda_var,
            bg="#f5f5f5",
            fg="#5b6470",
            font=("Segoe UI", 9),
            justify="left",
            wraplength=340,
        ).grid(row=fila, column=0, columnspan=2, sticky="w", pady=(0, 10))
        fila += 1

        botones = tk.Frame(container, bg="#f5f5f5")
        botones.grid(row=fila, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def actualizar_textos(event=None):
            tipo = self._tipo_desde_label(tipo_var.get())
            if tipo == TIPO_VENTA_KILO:
                precio_label.config(text="Precio por kilo:")
                stock_label.config(text="Stock actual (kg):")
                minimo_label.config(text="Stock minimo (kg):")
                ayuda_var.set("Usa decimales para kilos. Ejemplos: 0.250, 0.5, 1.750.")
            else:
                precio_label.config(text="Precio por unidad:")
                stock_label.config(text="Stock actual (u):")
                minimo_label.config(text="Stock minimo (u):")
                ayuda_var.set("Para productos por unidad, stock actual y minimo deben ser enteros.")

        def guardar():
            tipo_venta = self._tipo_desde_label(tipo_var.get())
            nombre = nombre_var.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacio.", parent=win)
                return

            id_txt = id_var.get().strip()
            if not id_txt.isdigit():
                messagebox.showerror("Error", "El ID debe ser un numero entero.", parent=win)
                return

            producto_id = int(id_txt)
            producto_id_original = int(producto["id"]) if es_edicion else None
            producto_existente = buscar_producto(producto_id)
            if producto_existente and (not es_edicion or producto_id != producto_id_original):
                messagebox.showerror(
                    "Error",
                    f"Ya existe un producto con ID {producto_id}.",
                    parent=win,
                )
                return

            try:
                precio = float(precio_var.get().strip().replace(",", "."))
                stock_actual = self._parsear_cantidad_form(stock_actual_var.get(), tipo_venta, "Stock actual")
                stock_minimo = self._parsear_cantidad_form(stock_minimo_var.get(), tipo_venta, "Stock minimo")
            except ValueError as error:
                messagebox.showerror("Error", str(error), parent=win)
                return

            if precio < 0:
                messagebox.showerror("Error", "El precio no puede ser negativo.", parent=win)
                return

            nuevos_datos = {
                "id": producto_id,
                "nombre": nombre,
                "precio": precio,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
                "tipo_venta": tipo_venta,
            }

            if es_edicion:
                ok = actualizar_producto(producto_id_original, nuevos_datos)
                mensaje_ok = "Producto actualizado correctamente"
            else:
                ok = agregar_producto({"id": producto_id, **nuevos_datos})
                mensaje_ok = "Producto agregado correctamente"

            if ok:
                messagebox.showinfo("Exito", mensaje_ok, parent=win)
                win.destroy()
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo guardar el producto", parent=win)

        def cancelar():
            win.destroy()

        tk.Button(
            botones,
            text="Guardar",
            command=guardar,
            font=("Segoe UI", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            bd=0,
            width=12,
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            botones,
            text="Cancelar",
            command=cancelar,
            font=("Segoe UI", 10, "bold"),
            bg="#9e9e9e",
            fg="white",
            activebackground="#8d8d8d",
            bd=0,
            width=12,
        ).pack(side=tk.LEFT)

        actualizar_textos()
        combo_tipo.bind("<<ComboboxSelected>>", actualizar_textos)

        e_id.focus_set()
        e_id.bind("<Return>", lambda event: (e_nombre.focus_set(), "break")[1])

        win.bind("<Return>", lambda e: guardar())
        win.bind("<Escape>", lambda e: cancelar())

    def agregar_producto_ui(self):
        if self.solo_lectura:
            messagebox.showwarning("Solo lectura", "Este usuario solo puede consultar productos.")
            return
        self._abrir_form_producto()

    def editar_producto_ui(self):
        if self.solo_lectura:
            messagebox.showwarning("Solo lectura", "Este usuario solo puede consultar productos.")
            return

        seleccionado = self.tree.focus()
        if not seleccionado:
            messagebox.showwarning("Atencion", "Selecciona un producto para editar.")
            return

        producto_id = int(seleccionado)
        producto = buscar_producto(producto_id)
        if not producto:
            messagebox.showerror("Error", "No se encontro el producto.")
            return

        self._abrir_form_producto(producto=producto)

    def eliminar_producto_ui(self):
        if self.solo_lectura:
            messagebox.showwarning("Solo lectura", "Este usuario solo puede consultar productos.")
            return

        seleccionado = self.tree.focus()
        if not seleccionado:
            return

        producto_id = int(seleccionado)
        confirmar = messagebox.askyesno("Confirmar", "Desea eliminar el producto?")
        if confirmar and eliminar_producto(producto_id):
            messagebox.showinfo("Exito", "Producto eliminado correctamente")
            self.actualizar_lista()
        elif not confirmar:
            return
        else:
            messagebox.showerror("Error", "No se pudo eliminar el producto")
