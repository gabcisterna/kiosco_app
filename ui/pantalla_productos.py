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
        try:
            nuevo = {
                "id": int(simpledialog.askstring("Agregar", "ID del producto:")),
                "nombre": simpledialog.askstring("Agregar", "Nombre:"),
                "precio": float(simpledialog.askstring("Agregar", "Precio:")),
                "stock_actual": int(simpledialog.askstring("Agregar", "Stock actual:")),
                "stock_minimo": int(simpledialog.askstring("Agregar", "Stock mínimo:")),
            }
        except:
            messagebox.showerror("Error", "Datos inválidos")
            return

        if agregar_producto(nuevo):
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
            self.actualizar_lista()
        else:
            messagebox.showerror("Error", "No se pudo agregar el producto")

    def editar_producto_ui(self):
        seleccionado = self.tree.focus()
        if not seleccionado:
            return
        producto_id = int(seleccionado)
        producto = buscar_producto(producto_id)
        if not producto:
            return

        try:
            nuevos_datos = {
                "nombre": simpledialog.askstring("Editar", "Nuevo nombre:", initialvalue=producto["nombre"]),
                "precio": float(simpledialog.askstring("Editar", "Nuevo precio:", initialvalue=producto["precio"])),
                "stock_actual": int(simpledialog.askstring("Editar", "Nuevo stock:", initialvalue=producto["stock_actual"])),
                "stock_minimo": int(simpledialog.askstring("Editar", "Nuevo stock mínimo:", initialvalue=producto.get("stock_minimo", 0))),
            }
        except:
            messagebox.showerror("Error", "Datos inválidos")
            return

        if actualizar_producto(producto_id, nuevos_datos):
            messagebox.showinfo("Éxito", "Producto actualizado correctamente")
            self.actualizar_lista()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el producto")

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
