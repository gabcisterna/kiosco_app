import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from modules.deudas import cargar_registro_deudas
from modules.debito import cargar_registro_debito
import os, json

class PantallaRegistros:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Registros de Pagos y Deudas")
        self.master.geometry("1300x650")
        self.master.configure(bg='#f0f0f0')

        self.orden_var = tk.StringVar(value="Fecha descendente")

        top_frame = tk.Frame(self.master, bg='#f0f0f0')
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(top_frame, text="Ordenar por:", bg='#f0f0f0', font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=5)
        opciones_orden = ["Fecha descendente", "Fecha ascendente", "Monto descendente", "Monto ascendente"]
        self.combo_orden = ttk.Combobox(top_frame, values=opciones_orden, state="readonly", textvariable=self.orden_var, width=25)
        self.combo_orden.pack(side=tk.LEFT, padx=5)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda e: self.actualizar_listas())

        # Paneles para dos listas
        listas_frame = tk.Frame(self.master, bg='#f0f0f0')
        listas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Registro de deudas
        frame_deudas = tk.LabelFrame(listas_frame, text="Registros de Deudas", font=("Segoe UI", 11, "bold"), bg="#f0f0f0", fg="#333")
        frame_deudas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columnas_deudas = ("fecha", "dni", "nombre", "monto", "tipo")
        self.tree_deudas = ttk.Treeview(frame_deudas, columns=columnas_deudas, show="headings")
        self.tree_deudas.heading("fecha", text="Fecha")
        self.tree_deudas.heading("dni", text="DNI")
        self.tree_deudas.heading("nombre", text="Nombre")
        self.tree_deudas.heading("monto", text="Monto")
        self.tree_deudas.heading("tipo", text="Tipo de Deuda")
        for col in columnas_deudas:
            self.tree_deudas.column(col, anchor="center", width=120)
        self.tree_deudas.pack(fill=tk.BOTH, expand=True)

        # Registro de débitos
        frame_debitos = tk.LabelFrame(listas_frame, text="Registros de Pagos (Débito)", font=("Segoe UI", 11, "bold"), bg="#f0f0f0", fg="#333")
        frame_debitos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        columnas_debitos = ("fecha", "dni", "nombre", "monto")
        self.tree_debitos = ttk.Treeview(frame_debitos, columns=columnas_debitos, show="headings")
        self.tree_debitos.heading("fecha", text="Fecha")
        self.tree_debitos.heading("dni", text="DNI")
        self.tree_debitos.heading("nombre", text="Nombre")
        self.tree_debitos.heading("monto", text="Monto")
        for col in columnas_debitos:
            self.tree_debitos.column(col, anchor="center", width=120)
        self.tree_debitos.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.actualizar_listas()

    def actualizar_listas(self):
        self.tree_deudas.delete(*self.tree_deudas.get_children())
        self.tree_debitos.delete(*self.tree_debitos.get_children())

        deudas = cargar_registro_deudas()
        debitos = cargar_registro_debito(os.path.join("data", "registro_debitos.json"), [])

        orden = self.orden_var.get()
        reverse = "descendente" in orden
        clave = "fecha" if "Fecha" in orden else "monto"

        deudas.sort(key=lambda d: self.obtener_fecha(d["fecha"]) if clave == "fecha" else d.get("monto", 0), reverse=reverse)
        debitos.sort(key=lambda d: self.obtener_fecha(d["fecha"]) if clave == "fecha" else d.get("monto", 0), reverse=reverse)

        for r in deudas:
            fecha = self.formatear_fecha(r.get("fecha"))
            tipo = r.get("tipo", "General")
            self.tree_deudas.insert("", tk.END, values=(
                fecha,
                r.get("dni", ""),
                r.get("nombre", ""),
                f"${r.get('monto', 0):.2f}",
                tipo
            ))

        for r in debitos:
            fecha = self.formatear_fecha(r.get("fecha"))
            self.tree_debitos.insert("", tk.END, values=(
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
