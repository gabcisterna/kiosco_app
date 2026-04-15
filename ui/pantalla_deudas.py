import tkinter as tk
from tkinter import messagebox, ttk

from modules.deudas import cargar_deudas, pagar_productos_deuda
from modules.productos import (
    EPSILON_CANTIDAD,
    buscar_producto,
    formatear_cantidad,
    obtener_unidad_medida,
    parsear_cantidad_para_producto,
    producto_se_vende_por_kilo,
)

COLOR_FONDO = "#f4f6f7"
COLOR_BLANCO = "#ffffff"
COLOR_BOTON = "#4CAF50"
COLOR_ENTRADA = "#ffffff"
FUENTE_TEXTO = ("Segoe UI", 10)
FUENTE_TITULO = ("Segoe UI", 11, "bold")


class PantallaDeudas:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestion de Deudas")
        self.master.geometry("980x660")
        self.master.configure(bg=COLOR_FONDO)

        self.busqueda_var = tk.StringVar()
        self.orden_var = tk.StringVar(value="Monto descendente")
        self.cliente_seleccionado_frame = None

        tk.Label(
            self.master,
            text="Deudas pendientes",
            bg=COLOR_FONDO,
            fg="#1f2937",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            self.master,
            text="Busca clientes rapido y selecciona una deuda para registrar pagos por producto.",
            bg=COLOR_FONDO,
            fg="#5b6470",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=20)

        top_frame = tk.Frame(self.master, bg=COLOR_FONDO)
        top_frame.pack(pady=10, fill=tk.X, padx=20)

        tk.Label(
            top_frame,
            text="Buscar por nombre, DNI o referencia:",
            bg=COLOR_FONDO,
            font=FUENTE_TITULO,
        ).pack(side=tk.LEFT)

        self.entry_buscar = tk.Entry(
            top_frame,
            textvariable=self.busqueda_var,
            font=FUENTE_TEXTO,
            width=32,
            bg=COLOR_ENTRADA,
            relief="solid",
            bd=1,
        )
        self.entry_buscar.pack(side=tk.LEFT, padx=10, ipady=4)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.actualizar_lista())

        opciones_orden = ["Monto descendente", "Monto ascendente"]
        self.combo_orden = ttk.Combobox(
            top_frame,
            values=opciones_orden,
            state="readonly",
            textvariable=self.orden_var,
            width=20,
            font=FUENTE_TEXTO,
        )
        self.combo_orden.pack(side=tk.RIGHT)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        frame_scroll = tk.Frame(self.master, bg=COLOR_FONDO)
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(frame_scroll, bg=COLOR_FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        self.inner_frame = tk.Frame(canvas, bg=COLOR_FONDO)

        self.inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = tk.Frame(self.master, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        self.btn_pagar = tk.Button(
            btn_frame,
            text="Pagar deuda seleccionada",
            font=("Segoe UI", 10, "bold"),
            bg="#16a34a",
            fg="white",
            height=2,
            width=24,
            command=self.pagar_deuda_dialog,
            relief="flat",
            cursor="hand2",
            activebackground="#15803d",
        )
        self.btn_pagar.pack()

        self.actualizar_lista()

    def _tipo_venta_item(self, item):
        producto_actual = buscar_producto(item["id"])
        return item.get("tipo_venta") or (producto_actual or {}).get("tipo_venta")

    def _unidad_item(self, item):
        return item.get("unidad_medida") or obtener_unidad_medida(tipo_venta=self._tipo_venta_item(item))

    def _cantidad_pendiente(self, item):
        total = float(item.get("cantidad_total", item.get("cantidad", 0)) or 0)
        pagado = float(item.get("cantidad_pagada", 0) or 0)
        return max(total - pagado, 0.0)

    def _texto_cantidad_item(self, item, cantidad):
        return formatear_cantidad(cantidad, tipo_venta=self._tipo_venta_item(item), con_unidad=True)

    def _texto_precio_actual(self, precio_actual, item):
        sufijo = " / kg" if producto_se_vende_por_kilo(tipo_venta=self._tipo_venta_item(item)) else " c/u"
        return f"${precio_actual:.2f}{sufijo}"

    def actualizar_lista(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        deudas = cargar_deudas()
        busqueda = self.busqueda_var.get().strip().lower()

        if busqueda:
            deudas = [
                deuda
                for deuda in deudas
                if busqueda in str(deuda.get("dni", "")).lower()
                or busqueda in str(deuda.get("nombre", "")).lower()
            ]

        reverse = self.orden_var.get() == "Monto descendente"
        deudas.sort(key=lambda deuda: float(deuda.get("monto", 0) or 0), reverse=reverse)

        if not deudas:
            tk.Label(
                self.inner_frame,
                text="No hay deudas para mostrar.",
                font=FUENTE_TITULO,
                bg=COLOR_FONDO,
                fg="gray",
            ).pack(pady=20)
            return

        for deuda in deudas:
            frame_cliente = tk.Frame(self.inner_frame, bg=COLOR_BLANCO, bd=1, relief="solid")
            frame_cliente.pack(fill="x", padx=10, pady=5)

            nombre = deuda.get("nombre", "(Sin nombre)")
            monto = float(deuda.get("monto", 0) or 0)
            productos = deuda.get("productos", [])

            header = f"DNI: {deuda['dni']} | Nombre: {nombre} | Deuda actual: ${monto:.2f}"

            label_header = tk.Label(
                frame_cliente,
                text=header,
                font=("Segoe UI", 11, "bold"),
                bg=COLOR_BLANCO,
                anchor="w",
            )
            label_header.pack(fill="x", padx=12, pady=(8, 6))
            label_header.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))

            if productos:
                for producto_deuda in productos:
                    producto_actual = buscar_producto(producto_deuda["id"])
                    precio_actual = float(producto_actual["precio"]) if producto_actual else 0.0
                    cantidad_pendiente = self._cantidad_pendiente(producto_deuda)
                    subtotal_actual = cantidad_pendiente * precio_actual

                    texto_prod = (
                        f"- {self._texto_cantidad_item(producto_deuda, cantidad_pendiente)} de {producto_deuda['nombre']} "
                        f"(precio actual {self._texto_precio_actual(precio_actual, producto_deuda)}) = ${subtotal_actual:.2f}"
                    )

                    label_prod = tk.Label(
                        frame_cliente,
                        text=texto_prod,
                        font=FUENTE_TEXTO,
                        bg=COLOR_BLANCO,
                        anchor="w",
                    )
                    label_prod.pack(fill="x", padx=20, pady=(0, 2))
                    label_prod.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))
            else:
                label_sin = tk.Label(
                    frame_cliente,
                    text="(Sin productos pendientes)",
                    font=FUENTE_TEXTO,
                    bg=COLOR_BLANCO,
                    fg="gray",
                    anchor="w",
                )
                label_sin.pack(fill="x", padx=20)
                label_sin.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))

    def seleccionar_cliente(self, frame):
        if self.cliente_seleccionado_frame:
            self.cliente_seleccionado_frame.config(bg=COLOR_BLANCO)
            for widget in self.cliente_seleccionado_frame.winfo_children():
                try:
                    widget.config(bg=COLOR_BLANCO)
                except Exception:
                    pass

        self.cliente_seleccionado_frame = frame
        frame.config(bg="#d0eaff")
        for widget in frame.winfo_children():
            try:
                widget.config(bg="#d0eaff")
            except Exception:
                pass

    def pagar_deuda_dialog(self):
        frame = self.cliente_seleccionado_frame

        if not frame:
            messagebox.showwarning("Atencion", "Selecciona un cliente con deuda haciendo clic en el.")
            return

        header_label = frame.winfo_children()[0]
        texto = header_label.cget("text")
        dni = texto.split("DNI:")[1].split("|")[0].strip()

        deuda = next((item for item in cargar_deudas() if item["dni"] == dni), None)
        if not deuda:
            messagebox.showerror("Error", "No se encontro la deuda del cliente.")
            return

        pago_window = tk.Toplevel(self.master)
        pago_window.title(f"Pagar deuda - DNI {dni}")
        pago_window.geometry("620x440")
        pago_window.configure(bg=COLOR_FONDO)
        pago_window.grab_set()

        tk.Label(
            pago_window,
            text=f"Selecciona que productos se pagan - DNI {dni}",
            bg=COLOR_FONDO,
            font=FUENTE_TITULO,
        ).pack(pady=(15, 10))

        items_vars = []

        body = tk.Frame(pago_window, bg=COLOR_FONDO)
        body.pack(fill="both", expand=True, padx=15, pady=10)

        for producto_deuda in deuda.get("productos", []):
            producto_actual = buscar_producto(producto_deuda["id"])
            precio_actual = float(producto_actual["precio"]) if producto_actual else 0.0
            cantidad_pendiente = self._cantidad_pendiente(producto_deuda)

            if cantidad_pendiente <= EPSILON_CANTIDAD:
                continue

            fila = tk.Frame(body, bg=COLOR_FONDO)
            fila.pack(fill="x", pady=4)

            seleccion_var = tk.BooleanVar(value=False)
            cantidad_var = tk.StringVar(
                value=formatear_cantidad(cantidad_pendiente, tipo_venta=self._tipo_venta_item(producto_deuda))
            )

            tk.Checkbutton(
                fila,
                variable=seleccion_var,
                bg=COLOR_FONDO,
                activebackground=COLOR_FONDO,
            ).pack(side="left")

            texto_prod = (
                f"{producto_deuda['nombre']} | Pendiente: {self._texto_cantidad_item(producto_deuda, cantidad_pendiente)} | "
                f"Precio actual: {self._texto_precio_actual(precio_actual, producto_deuda)}"
            )
            tk.Label(
                fila,
                text=texto_prod,
                bg=COLOR_FONDO,
                font=FUENTE_TEXTO,
            ).pack(side="left", padx=5)

            tk.Label(
                fila,
                text="Cant.:",
                bg=COLOR_FONDO,
                font=FUENTE_TEXTO,
            ).pack(side="left", padx=(10, 2))

            tk.Entry(
                fila,
                textvariable=cantidad_var,
                width=8,
                font=FUENTE_TEXTO,
            ).pack(side="left")

            items_vars.append(
                {
                    "id": producto_deuda["id"],
                    "nombre": producto_deuda["nombre"],
                    "pendiente": cantidad_pendiente,
                    "tipo_venta": self._tipo_venta_item(producto_deuda),
                    "seleccion": seleccion_var,
                    "cantidad_var": cantidad_var,
                }
            )

        def confirmar_pago():
            items_a_pagar = []

            for item in items_vars:
                if not item["seleccion"].get():
                    continue

                try:
                    cantidad = parsear_cantidad_para_producto(
                        item["cantidad_var"].get(),
                        tipo_venta=item.get("tipo_venta"),
                    )
                except ValueError:
                    messagebox.showerror("Error", f"Cantidad invalida para {item['nombre']}.", parent=pago_window)
                    return

                if float(cantidad) > float(item["pendiente"]) + EPSILON_CANTIDAD:
                    messagebox.showerror(
                        "Error",
                        (
                            f"No podes pagar {formatear_cantidad(cantidad, tipo_venta=item.get('tipo_venta'), con_unidad=True)} "
                            f"de {item['nombre']}. Pendiente: "
                            f"{formatear_cantidad(item['pendiente'], tipo_venta=item.get('tipo_venta'), con_unidad=True)}."
                        ),
                        parent=pago_window,
                    )
                    return

                items_a_pagar.append(
                    {
                        "id": item["id"],
                        "cantidad": cantidad,
                    }
                )

            if not items_a_pagar:
                messagebox.showwarning("Atencion", "Selecciona al menos un producto para pagar.", parent=pago_window)
                return

            ok, mensaje = pagar_productos_deuda(dni, items_a_pagar)

            if ok:
                messagebox.showinfo("Exito", mensaje, parent=pago_window)
                try:
                    pago_window.destroy()
                except Exception:
                    pass
                try:
                    self.master.destroy()
                except Exception:
                    pass
            else:
                messagebox.showerror("Error", mensaje, parent=pago_window)

        tk.Button(
            pago_window,
            text="Confirmar pago",
            command=confirmar_pago,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_BOTON,
            fg="white",
            relief="flat",
            width=18,
            height=2,
            activebackground="#45a049",
        ).pack(pady=15)
