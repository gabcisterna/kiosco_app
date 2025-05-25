import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from modules.empleados import cargar_empleados, agregar_empleado, eliminar_empleado, actualizar_empleado
import json
import os

RUTA_TURNOS = os.path.join("data", "turnos.json")

class PantallaEmpleados:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestión de Empleados y Turnos")
        self.master.geometry("900x600")
        self.master.configure(bg="#e9ecef")

        self.estilizar_widgets()

        self.vista_actual = tk.StringVar(value="turnos")

        # Botones de navegación
        top_nav = tk.Frame(self.master, bg="#e9ecef")
        top_nav.pack(fill=tk.X, padx=20, pady=(10, 5))

        ttk.Button(top_nav, text="📋 Ver Turnos", command=self.mostrar_vista_turnos).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_nav, text="👥 Ver Empleados", command=self.mostrar_vista_empleados).pack(side=tk.LEFT, padx=5)

        # Contenedor dinámico
        self.content_frame = tk.Frame(self.master, bg="#e9ecef")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.mostrar_vista_turnos()

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

    def mostrar_vista_turnos(self):
        self.vista_actual.set("turnos")
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        label = tk.Label(self.content_frame, text="Historial de Turnos", bg="#e9ecef", font=("Segoe UI", 14, "bold"))
        label.pack(anchor="w")

        self.tree_turnos = ttk.Treeview(self.content_frame, columns=("Empleado", "Inicio", "Fin"), show="headings", height=20)
        self.tree_turnos.heading("Empleado", text="Empleado")
        self.tree_turnos.heading("Inicio", text="Inicio")
        self.tree_turnos.heading("Fin", text="Fin")

        self.tree_turnos.column("Empleado", width=200)
        self.tree_turnos.column("Inicio", width=250)
        self.tree_turnos.column("Fin", width=250)

        self.tree_turnos.pack(fill=tk.BOTH, expand=True)
        self.cargar_turnos()

    def cargar_turnos(self):
        self.tree_turnos.delete(*self.tree_turnos.get_children())
        if os.path.exists(RUTA_TURNOS):
            with open(RUTA_TURNOS, "r", encoding="utf-8") as archivo:
                try:
                    turnos = json.load(archivo)
                except json.JSONDecodeError:
                    messagebox.showerror("Error", "turnos.json está mal formado")
                    return

                for t in reversed(turnos):
                    fin = t["fin"] if t["fin"] else "En curso"
                    self.tree_turnos.insert("", tk.END, values=(t["empleado"], t["inicio"], fin))

    def mostrar_vista_empleados(self):
        self.vista_actual.set("empleados")
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Encabezado con entrada de búsqueda y botón agregar
        top_frame = tk.Frame(self.content_frame, bg="#e9ecef")
        top_frame.pack(pady=10, fill=tk.X)

        tk.Label(top_frame, text="Buscar por ID:", bg="#e9ecef", font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=(0, 5))
        self.entry_id = ttk.Entry(top_frame)
        self.entry_id.pack(side=tk.LEFT, padx=(0, 10), ipadx=30, ipady=2)
        self.entry_id.bind("<KeyRelease>", lambda e: self.buscar_empleado_dinamico())

        agregar_btn = ttk.Button(top_frame, text="➕ Agregar Empleado", command=self.agregar_empleado_ui, style="Agregar.TButton")
        agregar_btn.pack(side=tk.RIGHT)


        self.tree = ttk.Treeview(self.content_frame, columns=("Nombre", "ID", "Correo", "Puesto"), show="headings")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Correo", text="Correo")
        self.tree.heading("Puesto", text="Puesto")

        self.tree.column("Nombre", width=150)
        self.tree.column("ID", width=50)
        self.tree.column("Correo", width=180)
        self.tree.column("Puesto", width=100)

        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(self.content_frame, bg="#e9ecef")
        bottom_frame.pack(pady=10)

        ttk.Button(bottom_frame, text="✏️ Editar", command=self.editar_empleado_ui, style="Editar.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(bottom_frame, text="🗑️ Eliminar", command=self.eliminar_empleado_ui, style="Eliminar.TButton").pack(side=tk.LEFT, padx=10)

        self.buscar_empleado_dinamico()

    def buscar_empleado_dinamico(self):
        id_buscado = self.entry_id.get().strip().lower()
        empleados = cargar_empleados()
        self.tree.delete(*self.tree.get_children())

        for emp in empleados:
            if id_buscado == "" or emp["id"].lower().startswith(id_buscado):
                self.tree.insert("", tk.END, values=(
                    emp.get("nombre", ""),
                    emp.get("id", ""),
                    emp.get("correo", ""),
                    emp.get("puesto", "")
                ))


    def agregar_empleado_ui(self):
        ventana = tk.Toplevel()
        ventana.title("Agregar Empleado")

        tk.Label(ventana, text="Nombre:").grid(row=0, column=0)
        entry_nombre = tk.Entry(ventana)
        entry_nombre.grid(row=0, column=1)

        tk.Label(ventana, text="Correo:").grid(row=1, column=0)
        entry_correo = tk.Entry(ventana)
        entry_correo.grid(row=1, column=1)

        tk.Label(ventana, text="Puesto:").grid(row=2, column=0)
        combo_puesto = ttk.Combobox(ventana, values=["Encargado", "Cajero"], state="readonly")
        combo_puesto.set("Cajero")
        combo_puesto.grid(row=2, column=1)

        def confirmar():
            nombre = entry_nombre.get().strip()
            correo = entry_correo.get().strip()
            puesto = combo_puesto.get()

            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio.")
                return

            empleados = cargar_empleados()
            ids_existentes = [int(emp["id"]) for emp in empleados if emp["id"].isdigit()]
            nuevo_id = str(max(ids_existentes, default=0) + 1)

            nuevo = {
                "nombre": nombre,
                "id": nuevo_id,
                "correo": correo,
                "puesto": puesto,
                "activo": False
            }

            if agregar_empleado(nuevo):
                messagebox.showinfo("Éxito", f"Empleado agregado correctamente con ID {nuevo_id}.")
                self.entry_id.delete(0, tk.END)
                self.buscar_empleado_dinamico()
                ventana.destroy()
            else:
                messagebox.showwarning("Duplicado", f"Ya existe un empleado con ID {nuevo_id}.")

        btn = tk.Button(ventana, text="Agregar", command=confirmar)
        btn.grid(row=3, column=0, columnspan=2, pady=10)


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
        nombre_actual = valores[0]
        correo_actual = valores[2] if len(valores) > 2 else ""
        puesto_actual = valores[3] if len(valores) > 3 else "Cajero"

        ventana = tk.Toplevel()
        ventana.title("Editar Empleado")

        tk.Label(ventana, text="Nombre:").grid(row=0, column=0)
        entry_nombre = tk.Entry(ventana)
        entry_nombre.insert(0, nombre_actual)
        entry_nombre.grid(row=0, column=1)

        tk.Label(ventana, text="Correo:").grid(row=1, column=0)
        entry_correo = tk.Entry(ventana)
        entry_correo.insert(0, correo_actual)
        entry_correo.grid(row=1, column=1)

        tk.Label(ventana, text="Puesto:").grid(row=2, column=0)
        combo_puesto = ttk.Combobox(ventana, values=["Encargado", "Cajero"], state="readonly")
        combo_puesto.set(puesto_actual)
        combo_puesto.grid(row=2, column=1)

        def confirmar():
            nuevo_nombre = entry_nombre.get().strip()
            nuevo_correo = entry_correo.get().strip()
            nuevo_puesto = combo_puesto.get()

            if not nuevo_nombre:
                messagebox.showerror("Error", "El nombre es obligatorio.")
                return

            nuevos_datos = {
                "nombre": nuevo_nombre,
                "correo": nuevo_correo,
                "puesto": nuevo_puesto
            }

            if actualizar_empleado(emp_id, nuevos_datos):
                messagebox.showinfo("Actualizado", "Empleado actualizado correctamente.")
                self.buscar_empleado_dinamico()
                ventana.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar el empleado.")

        btn = tk.Button(ventana, text="Actualizar", command=confirmar)
        btn.grid(row=3, column=0, columnspan=2, pady=10)

