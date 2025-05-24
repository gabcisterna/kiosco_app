import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from modules.empleados import cargar_empleados, agregar_empleado, eliminar_empleado, actualizar_empleado

class PantallaEmpleados:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestión de Empleados")
        self.master.geometry("800x550")
        self.master.configure(bg="#e9ecef")

        self.estilizar_widgets()

        # Encabezado con entrada de búsqueda y botón agregar
        top_frame = tk.Frame(self.master, bg="#e9ecef")
        top_frame.pack(pady=15, padx=20, fill=tk.X)

        tk.Label(top_frame, text="Buscar por ID:", bg="#e9ecef", font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_id = ttk.Entry(top_frame)
        self.entry_id.pack(side=tk.LEFT, padx=(0, 10), ipadx=30, ipady=2)
        self.entry_id.bind("<KeyRelease>", lambda e: self.buscar_empleado_dinamico())

        agregar_btn = ttk.Button(top_frame, text="➕ Agregar Empleado", command=self.agregar_empleado_ui, style="Agregar.TButton")
        agregar_btn.pack(side=tk.RIGHT)

        # Tabla de empleados
        self.tree = ttk.Treeview(self.master, columns=("Nombre", "ID", "Activo"), show="headings", height=14)
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Activo", text="Activo")

        self.tree.column("Nombre", width=300)
        self.tree.column("ID", width=150, anchor=tk.CENTER)
        self.tree.column("Activo", width=100, anchor=tk.CENTER)
        self.tree.pack(padx=20, pady=(10, 10), fill=tk.BOTH, expand=True)

        # Botones inferiores
        bottom_frame = tk.Frame(self.master, bg="#e9ecef")
        bottom_frame.pack(pady=10)

        ttk.Button(bottom_frame, text="✏️ Editar", command=self.editar_empleado_ui, style="Editar.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(bottom_frame, text="🗑️ Eliminar", command=self.eliminar_empleado_ui, style="Eliminar.TButton").pack(side=tk.LEFT, padx=10)

        self.buscar_empleado_dinamico()

    def estilizar_widgets(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background="white",
                        foreground="black",
                        rowheight=28,
                        fieldbackground="white",
                        font=("Segoe UI", 10))

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"),
                        background="#dee2e6")

        style.configure("Agregar.TButton",
                        font=("Segoe UI", 10, "bold"),
                        background="#38b000",
                        foreground="white",
                        padding=6)
        style.map("Agregar.TButton",
                  background=[("active", "#2a8800")])

        style.configure("Editar.TButton",
                        font=("Segoe UI", 10),
                        background="#1d84b5",
                        foreground="white",
                        padding=6)
        style.map("Editar.TButton",
                  background=[("active", "#156a96")])

        style.configure("Eliminar.TButton",
                        font=("Segoe UI", 10),
                        background="#e63946",
                        foreground="white",
                        padding=6)
        style.map("Eliminar.TButton",
                  background=[("active", "#c91828")])

    def buscar_empleado_dinamico(self):
        id_buscado = self.entry_id.get().strip().lower()
        empleados = cargar_empleados()
        self.tree.delete(*self.tree.get_children())

        for emp in empleados:
            if id_buscado == "" or emp["id"].lower().startswith(id_buscado):
                activo_str = "✅" if emp.get("activo") else "❌"
                self.tree.insert("", tk.END, values=(emp.get("nombre", ""), emp.get("id", ""), activo_str))

    def agregar_empleado_ui(self):
        nombre = simpledialog.askstring("Nuevo Empleado", "Nombre del empleado:")
        emp_id = simpledialog.askstring("Nuevo Empleado", "ID del empleado:")

        if not nombre or not emp_id:
            messagebox.showerror("Error", "El nombre y el ID son obligatorios.")
            return

        nuevo = {"nombre": nombre, "id": emp_id, "activo": False}
        if agregar_empleado(nuevo):
            messagebox.showinfo("Éxito", "Empleado agregado correctamente.")
            self.entry_id.delete(0, tk.END)
            self.buscar_empleado_dinamico()
        else:
            messagebox.showwarning("Duplicado", f"Ya existe un empleado con ID {emp_id}.")

    def eliminar_empleado_ui(self):
        seleccionado = self.tree.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Seleccioná un empleado para eliminar.")
            return
        valores = self.tree.item(seleccionado)["values"]
        emp_id = valores[1]

        if messagebox.askyesno("Confirmar", f"¿Eliminar al empleado con ID {emp_id}?"):
            if eliminar_empleado(emp_id):
                messagebox.showinfo("Eliminado", "Empleado eliminado correctamente.")
                self.buscar_empleado_dinamico()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el empleado.")

    def editar_empleado_ui(self):
        seleccionado = self.tree.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Seleccioná un empleado para editar.")
            return

        valores = self.tree.item(seleccionado)["values"]
        emp_id = valores[1]

        nuevo_nombre = simpledialog.askstring("Editar Empleado", "Nuevo nombre:", initialvalue=valores[0])
        if not nuevo_nombre:
            messagebox.showerror("Error", "El nombre es obligatorio.")
            return

        nuevos_datos = {"nombre": nuevo_nombre}
        if actualizar_empleado(emp_id, nuevos_datos):
            messagebox.showinfo("Actualizado", "Empleado actualizado correctamente.")
            self.buscar_empleado_dinamico()
        else:
            messagebox.showerror("Error", "No se pudo actualizar el empleado.")
