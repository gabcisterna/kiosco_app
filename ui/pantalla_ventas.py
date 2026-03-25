import tkinter as tk
from tkinter import ttk
from datetime import datetime
from modules.ventas import cargar_ventas
from modules.clientes import buscar_cliente
from modules.empleados import buscar_empleado


class PantallaVentas:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestión de Ventas")
        self.master.geometry("1000x600")
        self.master.configure(bg="#f0f0f0")

        self.busqueda_var = tk.StringVar()
        self.orden_var = tk.StringVar(value="Fecha descendente")
        self.filtro_var = tk.StringVar(value="Todas las ventas")

        top_frame = tk.Frame(self.master, bg="#f0f0f0")
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(
            top_frame,
            text="Buscar (ID empleado o nombre cliente):",
            bg="#f0f0f0",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)

        self.entry_buscar = tk.Entry(
            top_frame,
            textvariable=self.busqueda_var,
            font=("Segoe UI", 10)
        )
        self.entry_buscar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.actualizar_lista())

        opciones_orden = [
            "Fecha descendente",
            "Fecha ascendente",
            "Total descendente",
            "Total ascendente"
        ]
        self.combo_orden = ttk.Combobox(
            top_frame,
            values=opciones_orden,
            state="readonly",
            textvariable=self.orden_var,
            width=20
        )
        self.combo_orden.pack(side=tk.LEFT, padx=10)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        opciones_filtro = ["Todas las ventas", "Por empleado activo"]
        self.combo_filtro = ttk.Combobox(
            top_frame,
            values=opciones_filtro,
            state="readonly",
            textvariable=self.filtro_var,
            width=20
        )
        self.combo_filtro.pack(side=tk.LEFT, padx=10)
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        columns = ("fecha", "empleado", "cliente", "detalle", "total", "pago")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings", height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree.heading("fecha", text="Fecha/Hora")
        self.tree.heading("empleado", text="Empleado")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("detalle", text="Detalle")
        self.tree.heading("total", text="Total")
        self.tree.heading("pago", text="Forma de Pago")

        for col in columns:
            self.tree.column(col, anchor="center")

        self.tree.column("fecha", width=110, anchor="center")
        self.tree.column("empleado", width=120, anchor="center")
        self.tree.column("cliente", width=140, anchor="center")
        self.tree.column("detalle", width=420, anchor="w")
        self.tree.column("total", width=100, anchor="center")
        self.tree.column("pago", width=110, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.actualizar_lista()

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())

        ventas = cargar_ventas()
        busqueda = self.busqueda_var.get().strip().lower()
        orden = self.orden_var.get()
        filtro = self.filtro_var.get()

        if busqueda:
            ventas_filtradas = []
            for v in ventas:
                emp = buscar_empleado(v["empleado_id"])
                cliente = buscar_cliente(v.get("cliente_dni"))

                nombre_cliente = cliente["nombre"].lower() if cliente else ""
                id_empleado_str = str(v["empleado_id"])
                nombre_empleado = emp["nombre"].lower() if emp else ""

                if (
                    busqueda in id_empleado_str
                    or busqueda in nombre_cliente
                    or busqueda in nombre_empleado
                ):
                    ventas_filtradas.append(v)

            ventas = ventas_filtradas

        if filtro == "Por empleado activo":
            pass

        reverse = "descendente" in orden

        if "Fecha" in orden:
            ventas.sort(
                key=lambda v: datetime.strptime(v["fecha"], "%Y-%m-%d %H:%M:%S"),
                reverse=reverse
            )
        elif "Total" in orden:
            ventas.sort(key=lambda v: v.get("total", 0), reverse=reverse)

        for v in ventas:
            fecha_dt = datetime.strptime(v["fecha"], "%Y-%m-%d %H:%M:%S")
            fecha_hora = fecha_dt.strftime("%d-%b %H:%M")

            emp = buscar_empleado(v["empleado_id"])
            nombre_emp = emp["nombre"] if emp else "Desconocido"

            cliente = buscar_cliente(v.get("cliente_dni"))
            nombre_cliente = cliente["nombre"] if cliente else "Sin cliente"

            productos_txt = ", ".join(
                f"{p.get('cantidad', 0)}x {p.get('nombre', 'Producto')}"
                for p in v.get("productos", [])
            )

            ajuste = v.get("ajuste", {})
            tipo = ajuste.get("tipo")
            modo = ajuste.get("modo")
            valor = ajuste.get("valor", 0)
            importe = ajuste.get("importe_aplicado", 0)

            ajuste_txt = ""
            if tipo in ["descuento", "interes"] and importe:
                nombre_tipo = "Desc." if tipo == "descuento" else "Interés"
                if modo == "porcentaje":
                    ajuste_txt = f" | {nombre_tipo}: {valor}% (${importe:.2f})"
                else:
                    ajuste_txt = f" | {nombre_tipo}: ${importe:.2f}"

            detalle_txt = productos_txt
            if "subtotal" in v:
                detalle_txt += f" | Subtotal: ${v['subtotal']:.2f}"
            detalle_txt += ajuste_txt

            self.tree.insert(
                "",
                tk.END,
                values=(
                    fecha_hora,
                    nombre_emp,
                    nombre_cliente,
                    detalle_txt,
                    f"${v['total']:.2f}",
                    v["forma_pago"]
                )
            )