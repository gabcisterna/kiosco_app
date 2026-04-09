import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from modules.clientes import buscar_clientes_por_texto, cargar_clientes, resolver_cliente_para_venta

class PantallaClientes:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Buscar Clientes")
        self.master.geometry("700x450")
        self.master.configure(bg="#f5f5f5")

        # Entrada de búsqueda
        top_frame = tk.Frame(self.master, bg="#f5f5f5")
        top_frame.pack(pady=15, padx=20, fill=tk.X)

        tk.Label(top_frame, text="Buscar por nombre, DNI o referencia:", bg="#f5f5f5", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
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
        texto_buscado = self.entry_dni.get().strip()
        todos = buscar_clientes_por_texto(texto_buscado) if texto_buscado else cargar_clientes()

        # Limpiar árbol
        for item in self.tree.get_children():
            self.tree.delete(item)

        for cliente in todos:
            self.tree.insert("", tk.END, values=(
                cliente.get("nombre", ""),
                cliente.get("dni", ""),
                f"${cliente.get('deuda', 0):.2f}"
            ))

    def agregar_cliente_ui(self):
        try:
            nombre = simpledialog.askstring("Nuevo Cliente", "Nombre o alias:")
            dni = simpledialog.askstring("Nuevo Cliente", "DNI o referencia (opcional):")
        except Exception:
            messagebox.showerror("Error", "Datos inválidos.")
            return

        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio.")
            return

        cliente = resolver_cliente_para_venta(dni=dni, nombre=nombre, crear_si_no_existe=True)
        if not cliente:
            messagebox.showerror("Error", "No se pudo guardar el cliente.")
            return

        messagebox.showinfo(
            "Éxito",
            f"Cliente listo: {cliente['nombre']} | Ref: {cliente['dni']}",
        )
        self.entry_dni.delete(0, tk.END)
        self.buscar_cliente_dinamico()
