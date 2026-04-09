import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

from modules.debito import listar_registro_debitos


class PantallaDebitos:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Registros de Pagos (Debito)")
        self.master.geometry("780x620")
        self.master.configure(bg="#f0f0f0")

        self.orden_var = tk.StringVar(value="Fecha descendente")
        self.registros_por_item = {}

        top_frame = tk.Frame(self.master, bg="#f0f0f0")
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(top_frame, text="Ordenar por:", bg="#f0f0f0", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        opciones_orden = ["Fecha descendente", "Fecha ascendente", "Monto descendente", "Monto ascendente"]
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
            text="Doble click en un pago para ver el detalle.",
            bg="#f0f0f0",
            fg="#555",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18)

        frame_tabla = tk.Frame(self.master, bg="#f0f0f0")
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columnas = ("fecha", "dni", "nombre", "monto")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.abrir_detalle_registro)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("monto", text="Monto")

        for columna in columnas:
            self.tree.column(columna, anchor="center", width=140)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.actualizar_lista()

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())
        self.registros_por_item.clear()

        debitos = listar_registro_debitos()
        orden = self.orden_var.get()
        reverse = "descendente" in orden
        clave = "fecha" if "Fecha" in orden else "monto"

        debitos.sort(
            key=lambda registro: self.obtener_fecha(registro["fecha"]) if clave == "fecha" else registro.get("monto", 0),
            reverse=reverse,
        )

        for indice, registro in enumerate(debitos):
            item_id = f"debito_{indice}"
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(
                    self.formatear_fecha(registro.get("fecha")),
                    registro.get("dni", ""),
                    registro.get("nombre", ""),
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

        contenido = "\n".join(
            [
                f"Fecha: {registro.get('fecha', '')}",
                f"DNI: {registro.get('dni', '')}",
                f"Nombre: {registro.get('nombre', '')}",
                f"Monto: ${registro.get('monto', 0):.2f}",
            ]
        )
        self._mostrar_popup_detalle("Detalle del pago", contenido)

    def _mostrar_popup_detalle(self, titulo, contenido):
        ventana = tk.Toplevel(self.master)
        ventana.title(titulo)
        ventana.geometry("620x360")
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

    def obtener_fecha(self, fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

    def formatear_fecha(self, fecha_str):
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return fecha.strftime("%d-%b %H:%M")
        except Exception:
            return fecha_str
