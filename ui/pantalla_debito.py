import tkinter as tk
from tkinter import ttk
from datetime import datetime
from modules.debito import cargar_registro_debito
import os

class PantallaDebitos:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Registros de Pagos (Débito)")
        self.master.geometry("700x600")
        self.master.configure(bg='#f0f0f0')

        # Frame superior para orden
        top_frame = tk.Frame(self.master, bg='#f0f0f0')
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(top_frame, text="Ordenar por:", bg='#f0f0f0', font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        self.orden_var = tk.StringVar(value="Fecha descendente")
        opciones_orden = ["Fecha descendente", "Fecha ascendente", "Monto descendente", "Monto ascendente"]
        self.combo_orden = ttk.Combobox(top_frame, values=opciones_orden, state="readonly", textvariable=self.orden_var, width=25)
        self.combo_orden.pack(side=tk.LEFT, padx=5)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        # Frame de la tabla
        frame_tabla = tk.Frame(self.master, bg='#f0f0f0')
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columnas = ("fecha", "dni", "nombre", "monto")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("dni", text="DNI")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("monto", text="Monto")

        for col in columnas:
            self.tree.column(col, anchor="center", width=140)

        self.tree.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.actualizar_lista()

    def actualizar_lista(self):
        self.tree.delete(*self.tree.get_children())

        debitos = cargar_registro_debito(os.path.join("data", "registro_debitos.json"), [])

        orden = self.orden_var.get()
        reverse = "descendente" in orden
        clave = "fecha" if "Fecha" in orden else "monto"

        debitos.sort(
            key=lambda d: self.obtener_fecha(d["fecha"]) if clave == "fecha" else d.get("monto", 0),
            reverse=reverse
        )

        for r in debitos:
            fecha = self.formatear_fecha(r.get("fecha"))
            self.tree.insert("", tk.END, values=(
                fecha,
                r.get("dni", ""),
                r.get("nombre", ""),
                f"${r.get('monto', 0):.2f}"
            ))

    def obtener_fecha(self, fecha_str):
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

    def formatear_fecha(self, fecha_str):
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d-%b %H:%M")
        except:
            return fecha_str
