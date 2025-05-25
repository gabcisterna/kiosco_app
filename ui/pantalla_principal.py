import tkinter as tk
from tkinter import messagebox, simpledialog, font, ttk
from modules.empleados import obtener_empleado_activo
from modules.login import cerrar_sesion
from modules.productos import buscar_producto, listar_productos_con_stock_bajo, buscar_productos_por_nombre
from modules.ventas import registrar_venta
from ui.pantalla_productos import PantallaProductos
from ui.pantalla_ventas import PantallaVentas
from ui.pantalla_deudas import PantallaDeudas
from ui.pantalla_registros import PantallaRegistros
from ui.pantalla_debito import PantallaDebitos
from ui.pantalla_clientes import PantallaClientes
from ui.pantalla_empleados import PantallaEmpleados

class PantallaCaja:
    def __init__(self, master, ir_a_login):
        self.master = master
        self.ir_a_login = ir_a_login
        self.master.title("Caja - Supermercado")
        self.master.configure(bg="#f0f4f8")
        self.master.attributes('-fullscreen', True)
        self.master.bind("<Escape>", lambda e: self.master.attributes("-fullscreen", False))

        self.carrito = []
        self.empleado = obtener_empleado_activo()

        # Fuentes
        self.font_lista = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_labels = font.Font(family="Segoe UI", size=12)
        self.font_pequena = font.Font(family="Segoe UI", size=10)

        main_frame = tk.Frame(master, bg="#f0f4f8", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.crear_botones_admin(main_frame)
        self.crear_top_bar(main_frame)
        self.crear_entrada_producto(main_frame)
        self.crear_lista_productos(main_frame)
        self.crear_botones_lista(main_frame)
        self.crear_total_y_vuelto(main_frame)
        self.crear_info_pago(main_frame)
        self.crear_boton_finalizar(main_frame)
        self.mostrar_productos_stock_bajo(main_frame)

        self.cambiar_forma_pago(self.forma_pago_var.get())
        self.master.bind("<Return>", self.agregar_producto)
        self.master.bind("<F2>", lambda e: self.confirmar_venta())


    def crear_botones_admin(self, frame):
        admin_frame = tk.Frame(frame, bg="#dce6f0", pady=10, bd=1, relief="ridge")
        admin_frame.pack(fill=tk.X, pady=(0, 15))

        botones = []

        if self.empleado["puesto"] == "Dueño":
            botones = [
                ("Productos", self.abrir_popup_productos),
                ("Ventas", self.abrir_popup_ventas),
                ("Registros", self.abrir_popup_registros),
                ("Deudas", self.abrir_popup_deudas),
                ("Débito", self.abrir_popup_debito),
                ("Clientes", self.abrir_popup_clientes),
                ("Empleados", self.abrir_popup_empleados)
            ]
        elif self.empleado["puesto"] == "Encargado":
            botones = [
                ("Productos", self.abrir_popup_productos),
                ("Ventas", self.abrir_popup_ventas),
                ("Registros", self.abrir_popup_registros),
                ("Deudas", self.abrir_popup_deudas),
                ("Débito", self.abrir_popup_debito),
                ("Clientes", self.abrir_popup_clientes)
            ]

        for texto, comando in botones:
            tk.Button(
                admin_frame, text=texto, command=comando,
                bg="#4a90e2", fg="white", font=self.font_labels,
                relief="flat", padx=15, pady=7
            ).pack(side=tk.LEFT, padx=8)

    def crear_top_bar(self, frame):
        top_frame = tk.Frame(frame, bg="#f0f4f8")
        top_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(top_frame, text=f"Empleado activo: {self.empleado['nombre']}",
                 font=self.font_labels, bg="#f0f4f8", fg="#333").pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(top_frame, text="Cerrar sesión", command=self.cerrar_sesion_y_volver_al_login,
                  bg="#e94e4e", fg="white", font=self.font_labels, relief="flat", padx=12, pady=7).pack(side=tk.RIGHT)

    def crear_entrada_producto(self, frame):
        entrada_frame = tk.Frame(frame, bg="#f0f4f8")
        entrada_frame.pack(pady=(0, 15), fill=tk.X)

        tk.Label(entrada_frame, text="ID o nombre del producto:", font=self.font_labels, bg="#f0f4f8", fg="#555").pack(side=tk.LEFT)

        self.entrada_id = tk.Entry(entrada_frame, width=30, font=self.font_labels, relief="solid", bd=1)
        self.entrada_id.pack(side=tk.LEFT, padx=10)
        self.entrada_id.bind("<KeyRelease>", self.autocompletar_producto)
        self.entrada_id.bind("<Return>", self.agregar_producto)

        # Lista desplegable para autocompletar
        self.lista_sugerencias = tk.Listbox(entrada_frame, font=self.font_pequena, height=5, relief="solid", bd=1)
        self.lista_sugerencias.pack_forget()
        self.lista_sugerencias.bind("<<ListboxSelect>>", self.seleccionar_sugerencia)

        tk.Label(entrada_frame, text="Cantidad:", font=self.font_labels, bg="#f0f4f8", fg="#555").pack(side=tk.LEFT)
        self.entrada_cantidad = tk.Entry(entrada_frame, width=5, font=self.font_labels, relief="solid", bd=1)
        self.entrada_cantidad.insert(0, "1")
        self.entrada_cantidad.pack(side=tk.LEFT, padx=10)

        


    def crear_lista_productos(self, frame):
        lista_y_stock_frame = tk.Frame(frame, bg="#f0f4f8")
        lista_y_stock_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Frame para la lista de productos agregados
        lista_frame = tk.Frame(lista_y_stock_frame, bg="#f0f4f8")
        lista_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lista_productos = tk.Listbox(lista_frame, font=self.font_lista, height=15,
                                        bg="white", fg="#222", selectbackground="#4a90e2",
                                        activestyle="none", relief="solid", bd=1)
        self.lista_productos.pack(fill=tk.BOTH, expand=True)

        # Frame para productos con stock bajo
        self.stock_bajo_frame = tk.Frame(lista_y_stock_frame, bg="#f0f4f8", width=300)
        self.stock_bajo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(15, 0))


    def crear_botones_lista(self, frame):
        botones_frame = tk.Frame(frame, bg="#f0f4f8")
        botones_frame.pack(pady=(0, 15))
        tk.Button(botones_frame, text="Modificar cantidad", command=self.cambiar_cantidad_seleccionada,
                  bg="#ffa500", fg="white", font=self.font_labels, relief="flat", padx=15, pady=7).pack(side=tk.LEFT, padx=8)
        tk.Button(botones_frame, text="Eliminar producto", command=self.eliminar_producto_seleccionado,
                  bg="#e94e4e", fg="white", font=self.font_labels, relief="flat", padx=15, pady=7).pack(side=tk.LEFT, padx=8)

    def crear_info_pago(self, frame):
        info_pago_frame = tk.LabelFrame(frame, text="Información de pago", bg="#ffffff", fg="#333", font=self.font_labels, padx=10, pady=10)
        info_pago_frame.pack(fill=tk.X, pady=(10, 20), padx=10)

        # Subframe para entradas de datos del cliente
        datos_cliente_frame = tk.Frame(info_pago_frame, bg="#ffffff")
        datos_cliente_frame.grid(row=0, column=0, sticky="w", padx=10)

        # DNI
        self.label_dni = tk.Label(datos_cliente_frame, text="DNI del cliente (opcional):", font=self.font_pequena, bg="#ffffff", fg="#555")
        self.label_dni.grid(row=0, column=0, sticky="w")
        self.entry_dni = tk.Entry(datos_cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f0f4f8", width=20)
        self.entry_dni.grid(row=1, column=0, padx=(0, 20), pady=(0, 10))

        # Nombre
        self.label_nombre = tk.Label(datos_cliente_frame, text="Nombre del cliente:", font=self.font_pequena, bg="#ffffff", fg="#555")
        self.label_nombre.grid(row=0, column=1, sticky="w")
        self.entry_nombre = tk.Entry(datos_cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f0f4f8", width=25)
        self.entry_nombre.grid(row=1, column=1, padx=(0, 20), pady=(0, 10))

        # Pago en efectivo
        self.label_pago = tk.Label(datos_cliente_frame, text="Con cuánto paga:", font=self.font_pequena, bg="#ffffff", fg="#555")
        self.label_pago.grid(row=0, column=2, sticky="w")
        self.entry_pago = tk.Entry(datos_cliente_frame, font=self.font_labels, relief="solid", bd=1, bg="#f0f4f8", width=15)
        self.entry_pago.grid(row=1, column=2, padx=(0, 20), pady=(0, 10))
        self.entry_pago.bind("<KeyRelease>", self.actualizar_vuelto)

        # Forma de pago
        forma_pago_frame = tk.Frame(info_pago_frame, bg="#ffffff")
        forma_pago_frame.grid(row=1, column=0, sticky="w", pady=(10, 0))

        tk.Label(forma_pago_frame, text="Forma de pago:", font=self.font_pequena, bg="#ffffff", fg="#555").pack(side=tk.LEFT)

        self.forma_pago_var = tk.StringVar(value="efectivo")
        formas = [("Efectivo", "efectivo"), ("Débito", "debito"), ("Deuda", "deuda")]

        self.botones_pago = {}
        for texto, valor in formas:
            btn = tk.Button(forma_pago_frame, text=texto, font=self.font_pequena,
                            bg="#e0e0e0" if self.forma_pago_var.get() != valor else "#4a90e2",
                            fg="black" if self.forma_pago_var.get() != valor else "white",
                            relief="solid", bd=1, padx=10, pady=5,
                            command=lambda v=valor: self.seleccionar_forma_pago(v))
            btn.pack(side=tk.LEFT, padx=5)
            self.botones_pago[valor] = btn

    def autocompletar_producto(self, event=None):
        texto = self.entrada_id.get().strip()
        self.lista_sugerencias.pack_forget()

        if texto.isnumeric() or texto == "":
            return  # Si es un ID o vacío, no sugerimos

        sugerencias = buscar_productos_por_nombre(texto)
        if sugerencias:
            self.lista_sugerencias.delete(0, tk.END)
            for prod in sugerencias[:10]:
                self.lista_sugerencias.insert(tk.END, f"{prod['id']} - {prod['nombre']}")
            self.lista_sugerencias.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.lista_sugerencias.pack_forget()


    def seleccionar_sugerencia(self, event):
        if not self.lista_sugerencias.curselection():
            return

        seleccion = self.lista_sugerencias.get(self.lista_sugerencias.curselection())
        prod_id = seleccion.split(" - ")[0]
        self.entrada_id.delete(0, tk.END)
        self.entrada_id.insert(0, prod_id)
        self.lista_sugerencias.pack_forget()
        self.entrada_cantidad.focus_set()

    def seleccionar_forma_pago(self, valor):
        self.forma_pago_var.set(valor)
        for v, btn in self.botones_pago.items():
            if v == valor:
                btn.config(bg="#4a90e2", fg="white")
            else:
                btn.config(bg="#e0e0e0", fg="black")
        self.cambiar_forma_pago(valor)


    def crear_total_y_vuelto(self, frame):
        self.totales_frame = tk.Frame(frame, bg="#f0f4f8")
        self.totales_frame.pack(fill=tk.X, pady=(0, 10))

        self.total_label = tk.Label(self.totales_frame, text="Total: $0.00",
                                    font=("Segoe UI", 18, "bold"), bg="#f0f4f8", fg="#2e7d32")
        self.total_label.pack(side=tk.LEFT, padx=(10, 30))

        self.vuelto_label = tk.Label(self.totales_frame, text="Vuelto: $0.00",
                                    font=("Segoe UI", 16), bg="#f0f4f8", fg="#c62828")
        self.vuelto_label.pack(side=tk.LEFT)


    def crear_boton_finalizar(self, frame):
        self.btn_venta = tk.Button(frame, text="F2 Para Finalizar venta", command=self.confirmar_venta,
                                   bg="#388e3c", fg="white", font=("Segoe UI", 18, "bold"), relief="flat", padx=20, pady=15)
        self.btn_venta.pack(fill=tk.X)

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
        if forma in ["deuda", "debito"]:
            self.entry_pago.grid_remove()
            self.label_pago.grid_remove()
            self.vuelto_label.pack_forget()
            self.label_dni.config(text="DNI del cliente (obligatorio):")
            self.label_nombre.config(text="Nombre del cliente (obligatorio):")
            self.entry_dni.config(bg="white")
            self.entry_nombre.config(bg="white")
        else:
            self.label_pago.grid()
            self.entry_pago.grid()
            if not self.vuelto_label.winfo_ismapped():
                self.vuelto_label.pack(side=tk.LEFT)
            self.label_dni.config(text="DNI del cliente (opcional):")
            self.label_nombre.config(text="Nombre del cliente (opcional):")
            self.entry_dni.config(bg="#f0f4f8")
            self.entry_nombre.config(bg="#f0f4f8")



    # Resto de métodos sin cambios...
    def actualizar_stock_bajo(self):
        productos_bajo_stock = listar_productos_con_stock_bajo()
        self.tree_stock_bajo.delete(*self.tree_stock_bajo.get_children())
        for producto in productos_bajo_stock[:10]:
            self.tree_stock_bajo.insert("", tk.END, values=(producto["id"], producto["nombre"], producto["stock_actual"]))

    def agregar_producto(self, event=None):
        id_texto = self.entrada_id.get().strip()
        cant_texto = self.entrada_cantidad.get().strip()
        if not id_texto.isdigit() or not cant_texto.isdigit():
            messagebox.showerror("Error", "ID y cantidad deben ser numéricos")
            return
        prod_id = int(id_texto)
        cantidad = int(cant_texto)
        if cantidad <= 0:
            messagebox.showerror("Error", "La cantidad debe ser mayor a cero")
            return
        producto = buscar_producto(prod_id)
        if not producto:
            messagebox.showerror("Error", f"No se encontró producto con ID {prod_id}")
            return
        for p in self.carrito:
            if p["id"] == prod_id:
                p["cantidad"] += cantidad
                self.actualizar_lista()
                self.actualizar_total()
                self.entrada_id.delete(0, tk.END)
                return
        self.carrito.append({"id": prod_id, "nombre": producto["nombre"], "precio": producto["precio"], "cantidad": cantidad})
        self.actualizar_lista()
        self.actualizar_total()
        self.entrada_id.delete(0, tk.END)
        self.entrada_cantidad.delete(0, tk.END)
        self.entrada_cantidad.insert(0, "1")

    def actualizar_lista(self):
        self.lista_productos.delete(0, tk.END)
        for p in self.carrito:
            subtotal = p["cantidad"] * p["precio"]
            texto = f"{p['cantidad']} x {p['nombre']} - ${p['precio']:.2f} c/u = ${subtotal:.2f}"
            self.lista_productos.insert(tk.END, texto)

    def actualizar_total(self):
        total = sum(p["cantidad"] * p["precio"] for p in self.carrito)
        self.total_label.config(text=f"Total: ${total:.2f}")
        self.actualizar_vuelto()

    def actualizar_vuelto(self, event=None):
        try:
            pago = float(self.entry_pago.get())
        except ValueError:
            self.vuelto_label.config(text="Vuelto: $0.00")
            return
        total = sum(p["cantidad"] * p["precio"] for p in self.carrito)
        vuelto = pago - total
        self.vuelto_label.config(text=f"Vuelto: ${vuelto:.2f}" if vuelto >= 0 else "Vuelto: $0.00")

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
        self.total_label.config(text="Total: $0.00")
        self.vuelto_label.config(text="Vuelto: $0.00")
        self.actualizar_stock_bajo()
        self.forma_pago_var.set("efectivo")
        self.seleccionar_forma_pago("efectivo")
        self.entry_pago.delete(0, tk.END)
        self.entry_dni.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)


    def confirmar_venta(self):
        if not self.carrito:
            messagebox.showerror("Error", "No hay productos en la venta.")
            return
        total = sum(p["cantidad"] * p["precio"] for p in self.carrito)
        pago = float(self.entry_pago.get() or 0)
        forma = self.forma_pago_var.get()
        nombre = self.entry_nombre.get().strip()
        dni = self.entry_dni.get().strip()

        if forma in ["deuda", "debito"] and (not nombre or not dni):
            messagebox.showerror("Error", "DNI y nombre son obligatorios para deuda.")
            return
        if forma not in ["deuda", "debito"] and pago < total:
            messagebox.showerror("Error", "El pago es insuficiente.")
            return


        registrar_venta(self.carrito, forma, dni or None, nombre or None)
        self.vuelto_label.config(text=f"Vuelto: ${pago - total:.2f}" if forma not in ["deuda", "debito"] else "Vuelto: $0.00")
        self.carrito = []
        self.limpiar_despues_de_venta()

        messagebox.showinfo("Venta confirmada", "La venta se realizó con éxito.")


    def cerrar_sesion_y_volver_al_login(self):
        cerrar_sesion()
        self.master.destroy()
        nuevo_root = tk.Tk()
        self.ir_a_login(nuevo_root)

    # --- POPUPS DE ADMINISTRACIÓN ---
    def abrir_popup_productos(self):
        PantallaProductos(self.master)

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

    def abrir_popup_empleados(self):
        PantallaEmpleados(self.master)

    def crear_popup(self, titulo):
        popup = tk.Toplevel(self.master)
        popup.title(titulo)
        popup.geometry("800x600")
