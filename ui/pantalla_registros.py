import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

from modules.deudas import cargar_registro_deudas
from modules.productos import formatear_cantidad, producto_se_vende_por_kilo


class PantallaRegistros:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Registros de Deudas")
        self.master.geometry("1180x640")
        self.master.configure(bg="#f0f0f0")

        self.orden_var = tk.StringVar(value="Fecha descendente")
        self.registros_por_item = {}

        top_frame = tk.Frame(self.master, bg="#f0f0f0")
        top_frame.pack(pady=10, padx=12, fill=tk.X)

        tk.Label(
            top_frame,
            text="Ordenar por:",
            bg="#f0f0f0",
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=5)

        opciones_orden = [
            "Fecha descendente",
            "Fecha ascendente",
            "Monto descendente",
            "Monto ascendente",
        ]
        self.combo_orden = ttk.Combobox(
            top_frame,
            values=opciones_orden,
            state="readonly",
            textvariable=self.orden_var,
            width=25,
        )
        self.combo_orden.pack(side=tk.LEFT, padx=5)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda event: self.actualizar_lista())

        tk.Label(
            self.master,
            text="Doble click en un movimiento para abrir el detalle.",
            bg="#f0f0f0",
            fg="#555",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18)

        frame = tk.LabelFrame(
            self.master,
            text="Movimientos de deuda",
            font=("Segoe UI", 11, "bold"),
            bg="#f0f0f0",
            fg="#333",
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        columnas = ("fecha", "dni", "nombre", "tipo", "detalle", "monto")
        self.tree = ttk.Treeview(frame, columns=columnas, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.abrir_detalle_registro)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("detalle", text="Detalle")
        self.tree.heading("monto", text="Monto")

        self.tree.column("fecha", width=130, anchor="center")
        self.tree.column("dni", width=90, anchor="center")
        self.tree.column("nombre", width=150, anchor="center")
        self.tree.column("tipo", width=100, anchor="center")
        self.tree.column("detalle", width=560, anchor="w")
        self.tree.column("monto", width=110, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.actualizar_lista()

    def _obtener_fecha(self, fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

    def _formatear_fecha(self, fecha_str):
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return fecha.strftime("%d-%b %H:%M")
        except Exception:
            return fecha_str

    def _texto_cantidad(self, item, campo="cantidad"):
        tipo_venta = item.get("tipo_venta")
        if not tipo_venta and str(item.get("unidad_medida", "")).strip().lower() == "kg":
            tipo_venta = "kilo"
        return formatear_cantidad(item.get(campo, 0), tipo_venta=tipo_venta, con_unidad=True)

    def _texto_detalle_item(self, item, campo="cantidad"):
        cantidad = self._texto_cantidad(item, campo=campo)
        nombre = item.get("nombre", "")
        if producto_se_vende_por_kilo(tipo_venta=item.get("tipo_venta")) or str(item.get("unidad_medida", "")).strip().lower() == "kg":
            return f"{cantidad} de {nombre}"
        return f"{cantidad} x {nombre}"

    def _detalle_resumido(self, registro):
        detalle_lista = registro.get("detalle", [])
        if not detalle_lista:
            return "-"

        partes = []
        for detalle in detalle_lista:
            campo_cantidad = "cantidad" if "cantidad" in detalle else "cantidad_total"
            subtotal = detalle.get("subtotal")
            if subtotal is not None:
                partes.append(f"{self._texto_detalle_item(detalle, campo=campo_cantidad)} (${subtotal:.2f})")
            else:
                partes.append(self._texto_detalle_item(detalle, campo=campo_cantidad))
        return ", ".join(partes)

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        self.registros_por_item.clear()

        registros = cargar_registro_deudas()
        orden = self.orden_var.get()
        reverse = "descendente" in orden
        clave = "fecha" if "Fecha" in orden else "monto"

        registros.sort(
            key=lambda registro: self._obtener_fecha(registro["fecha"]) if clave == "fecha" else registro.get("monto", 0),
            reverse=reverse,
        )

        for indice, registro in enumerate(registros):
            item_id = f"registro_{indice}"
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(
                    self._formatear_fecha(registro.get("fecha")),
                    registro.get("dni", ""),
                    registro.get("nombre", ""),
                    registro.get("tipo", "General"),
                    self._detalle_resumido(registro),
                    f"${registro.get('monto', 0):.2f}",
                ),
            )
            self.registros_por_item[item_id] = registro

    def abrir_detalle_registro(self, event=None):
        item_id = self.tree.focus()
        if not item_id:
            return

        registro = self.registros_por_item.get(item_id)
        if not registro:
            return

        lineas = [
            f"Fecha: {registro.get('fecha', '')}",
            f"Tipo: {registro.get('tipo', 'General')}",
            f"DNI: {registro.get('dni', '')}",
            f"Nombre: {registro.get('nombre', '')}",
            f"Monto: ${registro.get('monto', 0):.2f}",
            "",
            "Detalle:",
        ]

        detalle = registro.get("detalle", [])
        if detalle:
            for item in detalle:
                campo_cantidad = "cantidad" if "cantidad" in item else "cantidad_total"
                lineas.append(f"- {self._texto_detalle_item(item, campo=campo_cantidad)} | ID {item.get('id', '-')}")
                if "precio_unitario" in item or "subtotal" in item:
                    precio = float(item.get("precio_unitario", 0) or 0)
                    sufijo = " / kg" if str(item.get("unidad_medida", "")).strip().lower() == "kg" else " c/u"
                    lineas.append(
                        f"  Precio unitario: ${precio:.2f}{sufijo} | Subtotal: ${item.get('subtotal', 0):.2f}"
                    )
                if "cantidad_pagada" in item:
                    lineas.append(f"  Pagado: {self._texto_cantidad(item, campo='cantidad_pagada')}")
        else:
            lineas.append("- Sin detalle adicional")

        self._mostrar_popup_detalle("Detalle del movimiento", "\n".join(lineas))

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
