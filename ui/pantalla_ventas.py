import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

from modules.clientes import buscar_cliente
from modules.empleados import buscar_empleado, obtener_empleado_activo
from modules.ventas import cargar_ventas


class PantallaVentas:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestion de Ventas")
        self.master.geometry("1120x650")
        self.master.configure(bg="#f0f0f0")

        self.busqueda_var = tk.StringVar()
        self.orden_var = tk.StringVar(value="Fecha descendente")
        self.filtro_var = tk.StringVar(value="Todas las ventas")
        self.ventas_por_item = {}

        top_frame = tk.Frame(self.master, bg="#f0f0f0")
        top_frame.pack(pady=10, padx=12, fill=tk.X)

        tk.Label(
            top_frame,
            text="Buscar (empleado, cliente, DNI, pago o fecha):",
            bg="#f0f0f0",
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=5)

        self.entry_buscar = tk.Entry(
            top_frame,
            textvariable=self.busqueda_var,
            font=("Segoe UI", 11),
            width=42,
        )
        self.entry_buscar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda event: self.actualizar_lista())

        opciones_orden = [
            "Fecha descendente",
            "Fecha ascendente",
            "Total descendente",
            "Total ascendente",
        ]
        self.combo_orden = ttk.Combobox(
            top_frame,
            values=opciones_orden,
            state="readonly",
            textvariable=self.orden_var,
            width=20,
        )
        self.combo_orden.pack(side=tk.LEFT, padx=10)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda event: self.actualizar_lista())

        opciones_filtro = ["Todas las ventas", "Por empleado activo"]
        self.combo_filtro = ttk.Combobox(
            top_frame,
            values=opciones_filtro,
            state="readonly",
            textvariable=self.filtro_var,
            width=20,
        )
        self.combo_filtro.pack(side=tk.LEFT, padx=10)
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda event: self.actualizar_lista())

        tk.Label(
            self.master,
            text="Doble click en una venta para ver el detalle completo.",
            bg="#f0f0f0",
            fg="#555",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18)

        columns = ("fecha", "empleado", "cliente", "detalle", "total", "pago")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings", height=22)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        self.tree.bind("<Double-1>", self.abrir_detalle_venta)

        self.tree.heading("fecha", text="Fecha/Hora")
        self.tree.heading("empleado", text="Empleado")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("detalle", text="Detalle")
        self.tree.heading("total", text="Total")
        self.tree.heading("pago", text="Forma de pago")

        self.tree.column("fecha", width=130, anchor="center")
        self.tree.column("empleado", width=150, anchor="center")
        self.tree.column("cliente", width=170, anchor="center")
        self.tree.column("detalle", width=470, anchor="w")
        self.tree.column("total", width=110, anchor="center")
        self.tree.column("pago", width=120, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.actualizar_lista()

    def _cliente_desde_venta(self, venta):
        cliente_dni = venta.get("cliente_dni")
        if not cliente_dni:
            return None
        return buscar_cliente(cliente_dni)

    def _empleado_desde_venta(self, venta):
        return buscar_empleado(venta["empleado_id"])

    def _coincide_busqueda(self, venta, busqueda):
        empleado = self._empleado_desde_venta(venta)
        cliente = self._cliente_desde_venta(venta)

        campos = [
            str(venta.get("empleado_id", "")),
            venta.get("fecha", ""),
            venta.get("forma_pago", ""),
            str(venta.get("cliente_dni", "")),
            empleado.get("nombre", "") if empleado else "",
            cliente.get("nombre", "") if cliente else "",
        ]

        for producto in venta.get("productos", []):
            campos.append(producto.get("nombre", ""))
            campos.append(str(producto.get("id", "")))

        texto_busqueda = " ".join(campo.lower() for campo in campos if campo)
        return busqueda in texto_busqueda

    def _detalle_resumido(self, venta):
        productos_txt = ", ".join(
            f"{producto.get('cantidad', 0)}x {producto.get('nombre', 'Producto')}"
            for producto in venta.get("productos", [])
        )

        ajuste = venta.get("ajuste", {})
        tipo = ajuste.get("tipo")
        modo = ajuste.get("modo")
        valor = ajuste.get("valor", 0)
        importe = ajuste.get("importe_aplicado", 0)

        ajuste_txt = ""
        if tipo in ["descuento", "interes"] and importe:
            nombre_tipo = "Desc." if tipo == "descuento" else "Interes"
            if modo == "porcentaje":
                ajuste_txt = f" | {nombre_tipo}: {valor}% (${importe:.2f})"
            else:
                ajuste_txt = f" | {nombre_tipo}: ${importe:.2f}"

        detalle_txt = productos_txt
        if "subtotal" in venta:
            detalle_txt += f" | Subtotal: ${venta['subtotal']:.2f}"
        detalle_txt += ajuste_txt
        return detalle_txt

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        self.ventas_por_item.clear()

        ventas = cargar_ventas()
        busqueda = self.busqueda_var.get().strip().lower()
        orden = self.orden_var.get()
        filtro = self.filtro_var.get()

        if busqueda:
            ventas = [venta for venta in ventas if self._coincide_busqueda(venta, busqueda)]

        if filtro == "Por empleado activo":
            empleado_activo = obtener_empleado_activo()
            if empleado_activo:
                ventas = [venta for venta in ventas if str(venta.get("empleado_id")) == str(empleado_activo.get("id"))]
            else:
                ventas = []

        reverse = "descendente" in orden
        if "Fecha" in orden:
            ventas.sort(
                key=lambda venta: datetime.strptime(venta["fecha"], "%Y-%m-%d %H:%M:%S"),
                reverse=reverse,
            )
        elif "Total" in orden:
            ventas.sort(key=lambda venta: venta.get("total", 0), reverse=reverse)

        for indice, venta in enumerate(ventas):
            fecha_dt = datetime.strptime(venta["fecha"], "%Y-%m-%d %H:%M:%S")
            fecha_hora = fecha_dt.strftime("%d-%b %H:%M")

            empleado = self._empleado_desde_venta(venta)
            nombre_empleado = empleado["nombre"] if empleado else "Desconocido"

            cliente = self._cliente_desde_venta(venta)
            nombre_cliente = cliente["nombre"] if cliente else "Sin cliente"

            item_id = f"venta_{indice}"
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(
                    fecha_hora,
                    nombre_empleado,
                    nombre_cliente,
                    self._detalle_resumido(venta),
                    f"${venta['total']:.2f}",
                    venta["forma_pago"],
                ),
            )
            self.ventas_por_item[item_id] = venta

    def abrir_detalle_venta(self, event=None):
        item_id = self.tree.focus()
        if not item_id:
            return

        venta = self.ventas_por_item.get(item_id)
        if not venta:
            return

        empleado = self._empleado_desde_venta(venta)
        cliente = self._cliente_desde_venta(venta)
        ajuste = venta.get("ajuste", {})

        lineas = [
            f"Fecha: {venta.get('fecha', '')}",
            f"Empleado: {empleado['nombre'] if empleado else 'Desconocido'}",
            f"Cliente: {cliente['nombre'] if cliente else 'Sin cliente'}",
            f"DNI cliente: {venta.get('cliente_dni') or '-'}",
            f"Forma de pago: {venta.get('forma_pago', '')}",
            "",
            "Productos:",
        ]

        for producto in venta.get("productos", []):
            lineas.append(
                f"- {producto.get('cantidad', 0)} x {producto.get('nombre', 'Producto')} "
                f"| ID {producto.get('id', '-')}"
            )
            lineas.append(
                f"  Precio unitario: ${producto.get('precio_unitario', 0):.2f} | "
                f"Subtotal: ${producto.get('subtotal', 0):.2f}"
            )

        lineas.extend(
            [
                "",
                f"Subtotal: ${venta.get('subtotal', 0):.2f}",
                f"Ajuste: {ajuste.get('tipo') or 'ninguno'}",
                f"Modo de ajuste: {ajuste.get('modo') or '-'}",
                f"Valor de ajuste: {ajuste.get('valor', 0):.2f}",
                f"Importe aplicado: ${ajuste.get('importe_aplicado', 0):.2f}",
                f"Total final: ${venta.get('total', 0):.2f}",
            ]
        )

        self._mostrar_popup_detalle("Detalle de venta", "\n".join(lineas))

    def _mostrar_popup_detalle(self, titulo, contenido):
        ventana = tk.Toplevel(self.master)
        ventana.title(titulo)
        ventana.geometry("760x560")
        ventana.configure(bg="#f7f7f7")
        ventana.transient(self.master)

        tk.Label(
            ventana,
            text=titulo,
            font=("Segoe UI", 14, "bold"),
            bg="#f7f7f7",
            fg="#222",
        ).pack(anchor="w", padx=16, pady=(14, 6))

        texto = scrolledtext.ScrolledText(
            ventana,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="white",
            fg="#222",
            relief="solid",
            bd=1,
        )
        texto.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        texto.insert("1.0", contenido)
        texto.configure(state="disabled")
