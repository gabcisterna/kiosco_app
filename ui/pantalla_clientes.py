import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from modules.clientes import cargar_clientes, agregar_cliente

class PantallaClientes:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Buscar Clientes")
        self.master.geometry("700x450")
        self.master.configure(bg="#f5f5f5")

        # Entrada de búsqueda
        top_frame = tk.Frame(self.master, bg="#f5f5f5")
        top_frame.pack(pady=15, padx=20, fill=tk.X)

        tk.Label(top_frame, text="Buscar por DNI:", bg="#f5f5f5", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_dni = ttk.Entry(top_frame)
        self.entry_dni.pack(side=tk.LEFT, padx=(0, 10), ipadx=30)
        self.entry_dni.bind("<KeyRelease>", lambda e: self.buscar_cliente_dinamico())

        tk.Button(
            top_frame, text="Agregar Cliente", command=self.agregar_cliente_ui,
            font=("Segoe UI", 10, "bold"), bg="#4CAF50", fg="white",
            activebackground="#45a049", bd=0, padx=10, pady=5
        ).pack(side=tk.RIGHT)

        # Lista de resultados
        self.tree = ttk.Treeview(self.master, columns=("Nombre", "DNI", "Deuda"), show="headings", height=12)
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("DNI", text="DNI")
        self.tree.heading("Deuda", text="Deuda")
        self.tree.column("Nombre", width=220)
        self.tree.column("DNI", width=120, anchor=tk.CENTER)
        self.tree.column("Deuda", width=120, anchor=tk.CENTER)
        self.tree.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Mostrar todos los clientes al abrir
        self.buscar_cliente_dinamico()

    def buscar_cliente_dinamico(self):
        dni_buscado = self.entry_dni.get().strip()
        todos = cargar_clientes()

        # Limpiar árbol
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filtrar por DNI parcial
        for cliente in todos:
            if dni_buscado == "" or cliente["dni"].startswith(dni_buscado):
                self.tree.insert("", tk.END, values=(
                    cliente.get("nombre", ""),
                    cliente.get("dni", ""),
                    f"${cliente.get('deuda', 0):.2f}"
                ))

    def agregar_cliente_ui(self):
        try:
            nuevo = {
                "nombre": simpledialog.askstring("Nuevo Cliente", "Nombre:"),
                "dni": simpledialog.askstring("Nuevo Cliente", "DNI:"),
                "deuda": 0.0,
            }
        except Exception as e:
            messagebox.showerror("Error", "Datos inválidos.")
            return

        if not nuevo["nombre"] or not nuevo["dni"]:
            messagebox.showerror("Error", "El nombre y DNI son obligatorios.")
            return

        if agregar_cliente(nuevo):
            messagebox.showinfo("Éxito", "Cliente agregado correctamente.")
            self.entry_dni.delete(0, tk.END)
            self.buscar_cliente_dinamico()
        else:
            messagebox.showwarning("Duplicado", f"Ya existe un cliente con DNI {nuevo['dni']}.")
