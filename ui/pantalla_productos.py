import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from modules.productos import (
    buscar_producto,
    listar_productos_con_stock_bajo,
    agregar_producto,
    actualizar_producto,
    eliminar_producto,
    listar_productos
)

class PantallaProductos:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestión de Productos")
        self.master.geometry("800x600")
        self.master.configure(bg="#f5f5f5")

        self.filtro_var = tk.StringVar(value="Mostrar todos")

        # Buscador y filtros
        top_frame = tk.Frame(self.master, bg="#f5f5f5")
        top_frame.pack(pady=10, fill=tk.X, padx=20)

        tk.Label(top_frame, text="Buscar por ID:", bg="#f5f5f5", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_buscar = ttk.Entry(top_frame)
        self.entry_buscar.pack(side=tk.LEFT, padx=(0, 10), ipadx=30)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.buscar_producto_dinamico())

        opciones = [
            "Mostrar todos",
            "Stock bajo",
            "Precio más alto",
            "Precio más bajo"
        ]
        self.filtro_menu = ttk.Combobox(top_frame, values=opciones, textvariable=self.filtro_var, state="readonly")
        self.filtro_menu.pack(side=tk.LEFT)
        self.filtro_menu.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        # Lista de productos con estilo Treeview
        self.tree = ttk.Treeview(self.master, columns=("Nombre", "Precio", "Stock"), show="headings", height=15)
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Precio", text="Precio")
        self.tree.heading("Stock", text="Stock")
        self.tree.column("Nombre", width=300)
        self.tree.column("Precio", width=100, anchor=tk.CENTER)
        self.tree.column("Stock", width=100, anchor=tk.CENTER)
        self.tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Botones de acción
        boton_frame = tk.Frame(self.master, bg="#f5f5f5")
        boton_frame.pack(pady=10)

        estilo_boton = {
            "font": ("Segoe UI", 10, "bold"),
            "width": 12,
            "bg": "#4CAF50",
            "fg": "white",
            "activebackground": "#45a049",
            "bd": 0
        }

        tk.Button(boton_frame, text="Agregar", command=self.agregar_producto_ui, **estilo_boton).pack(side=tk.LEFT, padx=10)
        tk.Button(boton_frame, text="Editar", command=self.editar_producto_ui, **estilo_boton).pack(side=tk.LEFT, padx=10)
        tk.Button(boton_frame, text="Eliminar", command=self.eliminar_producto_ui, **estilo_boton).pack(side=tk.LEFT, padx=10)

        self.mostrar_productos()

    def mostrar_productos(self):
        filtro = self.filtro_var.get()
        for item in self.tree.get_children():
            self.tree.delete(item)

        if filtro == "Stock bajo":
            productos = listar_productos_con_stock_bajo()
        else:
            productos = listar_productos()

        if filtro == "Precio más alto":
            productos.sort(key=lambda p: p["precio"], reverse=True)
        elif filtro == "Precio más bajo":
            productos.sort(key=lambda p: p["precio"])
        else:
            productos.sort(key=lambda p: p["nombre"].lower())

        for producto in productos:
            self.tree.insert("", tk.END, iid=producto["id"], values=(
                producto["nombre"],
                f"${producto['precio']:.2f}",
                producto["stock_actual"]
            ))

    def buscar_producto_dinamico(self):
        texto = self.entry_buscar.get().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)

        if texto == "":
            self.mostrar_productos()
            return

        if not texto.isdigit():
            return

        producto = buscar_producto(int(texto))
        if producto:
            self.tree.insert("", tk.END, iid=producto["id"], values=(
                producto["nombre"],
                f"${producto['precio']:.2f}",
                producto["stock_actual"]
            ))

    def actualizar_lista(self):
        texto = self.entry_buscar.get().strip()
        if texto == "":
            self.mostrar_productos()
        else:
            self.buscar_producto_dinamico()

    def agregar_producto_ui(self):
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
            font=("Segoe UI", 12, "bold")
        )
        titulo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
    
        # Vars del formulario
        id_var = tk.StringVar(value="")
        nombre_var = tk.StringVar(value="")
        precio_var = tk.StringVar(value="")
        stock_actual_var = tk.StringVar(value="")
        stock_minimo_var = tk.StringVar(value="")
    
        # Helpers UI
        def label(text, r):
            tk.Label(container, text=text, bg="#f5f5f5", font=("Segoe UI", 10)).grid(
                row=r, column=0, sticky="w", pady=6
            )
    
        def entry(var, r):
            e = ttk.Entry(container, textvariable=var, width=35)
            e.grid(row=r, column=1, sticky="w", pady=6)
            return e
    
        label("ID:", 1)
        e_id = entry(id_var, 1)
    
        label("Nombre:", 2)
        e_nombre = entry(nombre_var, 2)
    
        label("Precio:", 3)
        e_precio = entry(precio_var, 3)
    
        label("Stock actual:", 4)
        e_stock = entry(stock_actual_var, 4)
    
        label("Stock mínimo:", 5)
        e_min = entry(stock_minimo_var, 5)
    
        botones = tk.Frame(container, bg="#f5f5f5")
        botones.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
    
        def guardar():
            # Validaciones
            id_txt = id_var.get().strip()
            nombre = nombre_var.get().strip()
    
            if not id_txt.isdigit():
                messagebox.showerror("Error", "El ID debe ser un número entero.", parent=win)
                return
            producto_id = int(id_txt)
    
            if not nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacío.", parent=win)
                return
    
            try:
                precio = float(precio_var.get().strip().replace(",", "."))
                stock_actual = int(stock_actual_var.get().strip())
                stock_minimo = int(stock_minimo_var.get().strip())
            except:
                messagebox.showerror("Error", "Revisá precio/stock (deben ser numéricos).", parent=win)
                return
    
            if precio < 0 or stock_actual < 0 or stock_minimo < 0:
                messagebox.showerror("Error", "Precio y stocks no pueden ser negativos.", parent=win)
                return
    
            # Validar que el ID no exista
            if buscar_producto(producto_id):
                messagebox.showerror("Error", f"Ya existe un producto con ID {producto_id}.", parent=win)
                return
    
            nuevo = {
                "id": producto_id,
                "nombre": nombre,
                "precio": precio,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
            }
    
            if agregar_producto(nuevo):
                messagebox.showinfo("Éxito", "Producto agregado correctamente", parent=win)
                win.destroy()
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo agregar el producto", parent=win)
    
        def cancelar():
            win.destroy()
    
        btn_guardar = tk.Button(
            botones, text="Guardar", command=guardar,
            font=("Segoe UI", 10, "bold"),
            bg="#4CAF50", fg="white",
            activebackground="#45a049",
            bd=0, width=12
        )
        btn_guardar.pack(side=tk.LEFT, padx=8)
    
        btn_cancelar = tk.Button(
            botones, text="Cancelar", command=cancelar,
            font=("Segoe UI", 10, "bold"),
            bg="#9e9e9e", fg="white",
            activebackground="#8d8d8d",
            bd=0, width=12
        )
        btn_cancelar.pack(side=tk.LEFT)
    
        # UX
        e_id.focus_set()
        win.bind("<Return>", lambda e: guardar())
        win.bind("<Escape>", lambda e: cancelar())

    def editar_producto_ui(self):
        seleccionado = self.tree.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Seleccioná un producto para editar.")
            return

        producto_id = int(seleccionado)
        producto = buscar_producto(producto_id)
        if not producto:
            messagebox.showerror("Error", "No se encontró el producto.")
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
            font=("Segoe UI", 12, "bold")
        )
        titulo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Vars del formulario (precargadas)
        nombre_var = tk.StringVar(value=producto.get("nombre", ""))
        precio_var = tk.StringVar(value=str(producto.get("precio", 0)))
        stock_actual_var = tk.StringVar(value=str(producto.get("stock_actual", 0)))
        stock_minimo_var = tk.StringVar(value=str(producto.get("stock_minimo", 0)))

        # Helpers UI
        def label(text, r):
            tk.Label(container, text=text, bg="#f5f5f5", font=("Segoe UI", 10)).grid(
                row=r, column=0, sticky="w", pady=6
            )

        def entry(var, r):
            e = ttk.Entry(container, textvariable=var, width=35)
            e.grid(row=r, column=1, sticky="w", pady=6)
            return e

        label("Nombre:", 1)
        e_nombre = entry(nombre_var, 1)

        label("Precio:", 2)
        e_precio = entry(precio_var, 2)

        label("Stock actual:", 3)
        e_stock = entry(stock_actual_var, 3)

        label("Stock mínimo:", 4)
        e_min = entry(stock_minimo_var, 4)

        # Botones
        botones = tk.Frame(container, bg="#f5f5f5")
        botones.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def guardar():
            # Validaciones simples
            nombre = nombre_var.get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre no puede estar vacío.", parent=win)
                return

            try:
                precio = float(precio_var.get().replace(",", "."))
                stock_actual = int(stock_actual_var.get())
                stock_minimo = int(stock_minimo_var.get())
            except:
                messagebox.showerror("Error", "Revisá precio/stock (deben ser numéricos).", parent=win)
                return

            if precio < 0 or stock_actual < 0 or stock_minimo < 0:
                messagebox.showerror("Error", "Precio y stocks no pueden ser negativos.", parent=win)
                return

            nuevos_datos = {
                "nombre": nombre,
                "precio": precio,
                "stock_actual": stock_actual,
                "stock_minimo": stock_minimo,
            }

            if actualizar_producto(producto_id, nuevos_datos):
                messagebox.showinfo("Éxito", "Producto actualizado correctamente", parent=win)
                win.destroy()
                self.actualizar_lista()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el producto", parent=win)

        def cancelar():
            win.destroy()

        btn_guardar = tk.Button(
            botones, text="Guardar", command=guardar,
            font=("Segoe UI", 10, "bold"),
            bg="#4CAF50", fg="white",
            activebackground="#45a049",
            bd=0, width=12
        )
        btn_guardar.pack(side=tk.LEFT, padx=8)

        btn_cancelar = tk.Button(
            botones, text="Cancelar", command=cancelar,
            font=("Segoe UI", 10, "bold"),
            bg="#9e9e9e", fg="white",
            activebackground="#8d8d8d",
            bd=0, width=12
        )
        btn_cancelar.pack(side=tk.LEFT)

        # UX: foco + Enter para guardar + Esc para cancelar
        e_nombre.focus_set()
        win.bind("<Return>", lambda e: guardar())
        win.bind("<Escape>", lambda e: cancelar())

    def eliminar_producto_ui(self):
        seleccionado = self.tree.focus()
        if not seleccionado:
            return
        producto_id = int(seleccionado)
        confirmar = messagebox.askyesno("Confirmar", "¿Desea eliminar el producto?")
        if confirmar and eliminar_producto(producto_id):
            messagebox.showinfo("Éxito", "Producto eliminado correctamente")
            self.actualizar_lista()
        elif not confirmar:
            pass
        else:
            messagebox.showerror("Error", "No se pudo eliminar el producto")
