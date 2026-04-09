import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, ttk

from modules.reportes import (
    excel_disponible,
    exportar_reporte_ventas,
    generar_reporte_ventas,
    listar_tipos_reporte,
)


class PantallaReportes:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Reportes de Ventas")
        self.master.geometry("1220x760")
        self.master.configure(bg="#eef2f7")

        self.tipo_var = tk.StringVar(value="Diario")
        self.fecha_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.resumen_labels = {}
        self.reporte_actual = None

        self._crear_controles()
        self._crear_resumen()
        self._crear_tablas()
        self._crear_insights()
        self.actualizar_reporte()

    def _crear_controles(self):
        top_frame = tk.Frame(self.master, bg="#eef2f7")
        top_frame.pack(fill=tk.X, padx=18, pady=(16, 10))

        tk.Label(
            top_frame,
            text="Tipo de reporte:",
            bg="#eef2f7",
            font=("Segoe UI", 11, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        combo_tipo = ttk.Combobox(
            top_frame,
            values=listar_tipos_reporte(),
            textvariable=self.tipo_var,
            state="readonly",
            width=16,
        )
        combo_tipo.pack(side=tk.LEFT, padx=(0, 14))
        combo_tipo.bind("<<ComboboxSelected>>", lambda event: self.actualizar_reporte())

        tk.Label(
            top_frame,
            text="Fecha base (YYYY-MM-DD):",
            bg="#eef2f7",
            font=("Segoe UI", 11, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.entry_fecha = tk.Entry(
            top_frame,
            textvariable=self.fecha_var,
            font=("Segoe UI", 11),
            width=14,
            relief="solid",
            bd=1,
        )
        self.entry_fecha.pack(side=tk.LEFT, padx=(0, 10), ipady=3)
        self.entry_fecha.bind("<Return>", lambda event: self.actualizar_reporte())

        tk.Button(
            top_frame,
            text="Actualizar",
            command=self.actualizar_reporte,
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=14,
            pady=6,
        ).pack(side=tk.LEFT)

        tk.Button(
            top_frame,
            text="Exportar",
            command=self.exportar_reporte,
            bg="#0f766e",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=14,
            pady=6,
        ).pack(side=tk.LEFT, padx=(10, 0))

    def _crear_resumen(self):
        resumen_frame = tk.LabelFrame(
            self.master,
            text="Resumen general",
            bg="#ffffff",
            fg="#222",
            font=("Segoe UI", 12, "bold"),
            padx=14,
            pady=12,
        )
        resumen_frame.pack(fill=tk.X, padx=18, pady=(0, 12))

        campos = [
            ("Periodo", "periodo"),
            ("Ventas", "ventas"),
            ("Facturado", "facturado"),
            ("Ticket promedio", "ticket"),
            ("Unidades", "unidades"),
            ("Productos distintos", "productos"),
        ]

        for indice, (titulo, clave) in enumerate(campos):
            columna = indice % 3
            fila = (indice // 3) * 2

            tk.Label(
                resumen_frame,
                text=titulo,
                bg="#ffffff",
                fg="#555",
                font=("Segoe UI", 10),
            ).grid(row=fila, column=columna, sticky="w", padx=18, pady=(0, 2))

            label_valor = tk.Label(
                resumen_frame,
                text="-",
                bg="#ffffff",
                fg="#111",
                font=("Segoe UI", 14, "bold"),
            )
            label_valor.grid(row=fila + 1, column=columna, sticky="w", padx=18, pady=(0, 10))
            self.resumen_labels[clave] = label_valor

    def _crear_tablas(self):
        tablas_superiores = tk.Frame(self.master, bg="#eef2f7")
        tablas_superiores.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        frame_productos = tk.LabelFrame(
            tablas_superiores,
            text="Productos más vendidos",
            bg="#ffffff",
            fg="#222",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        frame_productos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.tree_productos = ttk.Treeview(
            frame_productos,
            columns=("producto", "cantidad", "facturado", "apariciones"),
            show="headings",
            height=12,
        )
        self.tree_productos.heading("producto", text="Producto")
        self.tree_productos.heading("cantidad", text="Cantidad")
        self.tree_productos.heading("facturado", text="Facturado")
        self.tree_productos.heading("apariciones", text="Tickets")
        self.tree_productos.column("producto", width=260)
        self.tree_productos.column("cantidad", width=90, anchor="center")
        self.tree_productos.column("facturado", width=110, anchor="center")
        self.tree_productos.column("apariciones", width=80, anchor="center")
        self.tree_productos.pack(fill=tk.BOTH, expand=True)

        frame_pagos = tk.LabelFrame(
            tablas_superiores,
            text="Formas de pago",
            bg="#ffffff",
            fg="#222",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        frame_pagos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        self.tree_pagos = ttk.Treeview(
            frame_pagos,
            columns=("forma", "operaciones", "monto"),
            show="headings",
            height=12,
        )
        self.tree_pagos.heading("forma", text="Forma")
        self.tree_pagos.heading("operaciones", text="Operaciones")
        self.tree_pagos.heading("monto", text="Monto")
        self.tree_pagos.column("forma", width=170)
        self.tree_pagos.column("operaciones", width=100, anchor="center")
        self.tree_pagos.column("monto", width=120, anchor="center")
        self.tree_pagos.pack(fill=tk.BOTH, expand=True)

        frame_inferior = tk.Frame(self.master, bg="#eef2f7")
        frame_inferior.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 16))

        frame_empleados = tk.LabelFrame(
            frame_inferior,
            text="Desempeño por empleado",
            bg="#ffffff",
            fg="#222",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        frame_empleados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.tree_empleados = ttk.Treeview(
            frame_empleados,
            columns=("empleado", "ventas", "unidades", "total"),
            show="headings",
            height=10,
        )
        self.tree_empleados.heading("empleado", text="Empleado")
        self.tree_empleados.heading("ventas", text="Ventas")
        self.tree_empleados.heading("unidades", text="Unidades")
        self.tree_empleados.heading("total", text="Facturado")
        self.tree_empleados.column("empleado", width=220)
        self.tree_empleados.column("ventas", width=90, anchor="center")
        self.tree_empleados.column("unidades", width=90, anchor="center")
        self.tree_empleados.column("total", width=120, anchor="center")
        self.tree_empleados.pack(fill=tk.BOTH, expand=True)

    def _crear_insights(self):
        frame_insights = tk.LabelFrame(
            self.master,
            text="Highlights",
            bg="#ffffff",
            fg="#222",
            font=("Segoe UI", 11, "bold"),
            padx=10,
            pady=10,
        )
        frame_insights.pack(fill=tk.BOTH, padx=18, pady=(0, 16))

        self.texto_insights = scrolledtext.ScrolledText(
            frame_insights,
            wrap=tk.WORD,
            height=7,
            font=("Segoe UI", 10),
            bg="white",
            fg="#222",
            relief="solid",
            bd=1,
        )
        self.texto_insights.pack(fill=tk.BOTH, expand=True)
        self.texto_insights.configure(state="disabled")

    def _cargar_tree(self, tree, filas):
        tree.delete(*tree.get_children())
        for fila in filas:
            tree.insert("", tk.END, values=fila)

    def actualizar_reporte(self):
        try:
            reporte = generar_reporte_ventas(self.tipo_var.get(), self.fecha_var.get())
        except ValueError as exc:
            messagebox.showerror("Fecha inválida", str(exc), parent=self.master)
            return

        self.reporte_actual = reporte

        self.resumen_labels["periodo"].config(text=reporte["periodo_label"])
        self.resumen_labels["ventas"].config(text=str(reporte["cantidad_ventas"]))
        self.resumen_labels["facturado"].config(text=f"${reporte['total_facturado']:.2f}")
        self.resumen_labels["ticket"].config(text=f"${reporte['ticket_promedio']:.2f}")
        self.resumen_labels["unidades"].config(text=str(reporte["unidades_vendidas"]))
        self.resumen_labels["productos"].config(text=str(reporte["productos_distintos"]))

        self._cargar_tree(
            self.tree_productos,
            [
                (
                    producto["nombre"],
                    producto["cantidad_vendida"],
                    f"${producto['facturado']:.2f}",
                    producto["apariciones"],
                )
                for producto in reporte["productos_mas_vendidos"][:10]
            ],
        )

        self._cargar_tree(
            self.tree_pagos,
            [
                (
                    pago["forma_pago"].title(),
                    pago["cantidad_operaciones"],
                    f"${pago['monto_total']:.2f}",
                )
                for pago in reporte["formas_pago"]
            ],
        )

        self._cargar_tree(
            self.tree_empleados,
            [
                (
                    empleado["nombre"],
                    empleado["cantidad_ventas"],
                    empleado["unidades_vendidas"],
                    f"${empleado['monto_total']:.2f}",
                )
                for empleado in reporte["empleados_destacados"][:10]
            ],
        )

        lineas = [
            f"Periodo analizado: {reporte['periodo_label']}",
            f"Rango cubierto: {reporte['inicio']} a {reporte['fin']}",
        ]

        if not reporte["cantidad_ventas"]:
            lineas.append("")
            lineas.append("No hubo ventas registradas en este período.")
        else:
            mejor_producto = reporte.get("mejor_producto")
            mejor_empleado = reporte.get("mejor_empleado")
            mejor_dia = reporte.get("mejor_dia")

            lineas.extend(
                [
                    "",
                    f"Producto líder: {mejor_producto['nombre']} con {mejor_producto['cantidad_vendida']} unidades."
                    if mejor_producto
                    else "Producto líder: sin datos.",
                    f"Empleado destacado: {mejor_empleado['nombre']} con ${mejor_empleado['monto_total']:.2f} facturados."
                    if mejor_empleado
                    else "Empleado destacado: sin datos.",
                    f"Mejor día: {mejor_dia['fecha']} con ${mejor_dia['total']:.2f}."
                    if mejor_dia
                    else "Mejor día: sin datos.",
                ]
            )

        self.texto_insights.configure(state="normal")
        self.texto_insights.delete("1.0", tk.END)
        self.texto_insights.insert("1.0", "\n".join(lineas))
        self.texto_insights.configure(state="disabled")

    def exportar_reporte(self):
        if not self.reporte_actual:
            self.actualizar_reporte()
        if not self.reporte_actual:
            return

        extension_defecto = ".xlsx" if excel_disponible() else ".csv"
        filetypes = [("CSV compatible con Excel", "*.csv")]
        if excel_disponible():
            filetypes.insert(0, ("Excel", "*.xlsx"))

        ruta = filedialog.asksaveasfilename(
            parent=self.master,
            title="Exportar reporte",
            defaultextension=extension_defecto,
            filetypes=filetypes,
            initialfile=f"reporte_{self.reporte_actual['tipo_reporte']}_{self.reporte_actual['fecha_base']}{extension_defecto}",
        )
        if not ruta:
            return

        try:
            exportar_reporte_ventas(self.reporte_actual, ruta)
        except RuntimeError as exc:
            messagebox.showerror("Exportación no disponible", str(exc), parent=self.master)
            return
        except OSError as exc:
            messagebox.showerror("Error al exportar", f"No se pudo guardar el archivo.\n{exc}", parent=self.master)
            return

        messagebox.showinfo("Reporte exportado", f"Archivo guardado en:\n{ruta}", parent=self.master)
