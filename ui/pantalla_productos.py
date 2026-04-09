import tkinter as tk
from tkinter import messagebox, ttk

from modules.productos import (
    actualizar_producto,
    agregar_producto,
    buscar_producto,
    buscar_productos_por_texto,
    cargar_productos,
    eliminar_producto,
    listar_productos_con_stock_bajo,
)


class PantallaProductos:
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
            columns=("ID", "Nombre", "Precio", "Stock"),
            show="headings",
            height=18,
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Precio", text="Precio")
        self.tree.heading("Stock", text="Stock")
        self.tree.column("ID", width=90, anchor=tk.CENTER)
        self.tree.column("Nombre", width=420)
        self.tree.column("Precio", width=140, anchor=tk.CENTER)
        self.tree.column("Stock", width=120, anchor=tk.CENTER)
        self.tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        if self.solo_lectura:
            tk.Label(
                self.master,
                text="Modo solo lectura: podés consultar productos, pero no modificarlos.",
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
                f"${float(producto['precio']):.2f}",
                producto["stock_actual"],
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

    def agregar_producto_ui(self):
        if self.solo_lectura:
            messagebox.showwarning("Solo lectura", "Este usuario solo puede consultar productos.")
            return

        win = tk.Toplevel(self.master)
        win.title("Agregar producto")
        win.configure(bg="#f5f5f5")
        win.resizable(False, False)
        win.transient(self.master)
        win.grab_set()

        container = tk.Frame(win, bg="#f5f5f5")
        container.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)

        titulo = tk.Label(
            container,
            text="Agregar producto",
            bg="#f5f5f5",
            font=("Segoe UI", 12, "bold"),
        )
        titulo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        id_var = tk.StringVar(value="")
        nombre_var = tk.StringVar(value="")
        precio_var = tk.StringVar(value="")
        stock_actual_var = tk.StringVar(value="")
        stock_minimo_var = tk.StringVar(value="")

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

        label("ID:", 1)
        e_id = entry(id_var, 1)

        label("Nombre:", 2)
        e_nombre = entry(nombre_var, 2)

        label("Precio:", 3)
        e_precio = entry(precio_var, 3)

        label("Stock actual:", 4)
        e_stock = entry(stock_actual_var, 4)

        label("Stock minimo:", 5)
        e_min = entry(stock_minimo_var, 5)

        botones = tk.Frame(container, bg="#f5f5f5")
        botones.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def guardar():
            id_txt = id_var.get().strip()
            nombre = nombre_var.get().strip()

            if not id_txt.isdigit():
                messagebox.showerror("Error", "El ID debe ser un numero entero.", parent=win)
                return
            producto_id = int(id_txt)

            if not nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacio.", parent=win)
                return

            try:
                precio = float(precio_var.get().strip().replace(",", "."))
                stock_actual = int(stock_actual_var.get().strip())
                stock_minimo = int(stock_minimo_var.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Revisa precio y stock; deben ser numericos.",
                    parent=win,
                )
                return

            if precio < 0 or stock_actual < 0 or stock_minimo < 0:
                messagebox.showerror(
                    "Error",
                    "Precio y stocks no pueden ser negativos.",
                    parent=win,
                )
                return

            if buscar_producto(producto_id):
                messagebox.showerror(
                    "Error",
                    f"Ya existe un producto con ID {producto_id}.",
                    parent=win,
                )
                return

            nuevo = {
                "id": producto_id,
                "nombre": nombre,
                "precio": precio,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
            }

            if agregar_producto(nuevo):
                messagebox.showinfo("Exito", "Producto agregado correctamente", parent=win)
                win.destroy()
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo agregar el producto", parent=win)

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

        e_id.focus_set()

        def avanzar_desde_id(event=None):
            e_nombre.focus_set()
            e_nombre.icursor(tk.END)
            return "break"

        def bloquear_enter(event=None):
            return "break"

        e_id.bind("<Return>", avanzar_desde_id)
        e_nombre.bind("<Return>", bloquear_enter)
        e_precio.bind("<Return>", bloquear_enter)
        e_stock.bind("<Return>", bloquear_enter)
        e_min.bind("<Return>", bloquear_enter)
        win.bind("<Escape>", lambda e: cancelar())

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

        self.abrir_form_edicion(producto_id, producto)

    def abrir_form_edicion(self, producto_id: int, producto: dict):
        win = tk.Toplevel(self.master)
        win.title(f"Editar producto #{producto_id}")
        win.configure(bg="#f5f5f5")
        win.resizable(False, False)
        win.transient(self.master)
        win.grab_set()

        container = tk.Frame(win, bg="#f5f5f5")
        container.pack(padx=20, pady=15, fill=tk.BOTH, expand=True)

        titulo = tk.Label(
            container,
            text=f"Editar producto #{producto_id}",
            bg="#f5f5f5",
            font=("Segoe UI", 12, "bold"),
        )
        titulo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        nombre_var = tk.StringVar(value=producto.get("nombre", ""))
        precio_var = tk.StringVar(value=str(producto.get("precio", 0)))
        stock_actual_var = tk.StringVar(value=str(producto.get("stock_actual", 0)))
        stock_minimo_var = tk.StringVar(value=str(producto.get("stock_minimo", 0)))

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

        label("Nombre:", 1)
        e_nombre = entry(nombre_var, 1)

        label("Precio:", 2)
        e_precio = entry(precio_var, 2)

        label("Stock actual:", 3)
        e_stock = entry(stock_actual_var, 3)

        label("Stock minimo:", 4)
        e_min = entry(stock_minimo_var, 4)

        botones = tk.Frame(container, bg="#f5f5f5")
        botones.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def guardar():
            nombre = nombre_var.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacio.", parent=win)
                return

            try:
                precio = float(precio_var.get().replace(",", "."))
                stock_actual = int(stock_actual_var.get())
                stock_minimo = int(stock_minimo_var.get())
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Revisa precio y stock; deben ser numericos.",
                    parent=win,
                )
                return

            if precio < 0 or stock_actual < 0 or stock_minimo < 0:
                messagebox.showerror(
                    "Error",
                    "Precio y stocks no pueden ser negativos.",
                    parent=win,
                )
                return

            nuevos_datos = {
                "nombre": nombre,
                "precio": precio,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
            }

            if actualizar_producto(producto_id, nuevos_datos):
                messagebox.showinfo("Exito", "Producto actualizado correctamente", parent=win)
                win.destroy()
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el producto", parent=win)

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

        e_nombre.focus_set()
        win.bind("<Return>", lambda e: guardar())
        win.bind("<Escape>", lambda e: cancelar())

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
