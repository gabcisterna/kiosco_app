import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.login import registrar_inicio_sesion
from modules.empleados import agregar_empleado, cargar_empleados
from ui.pantalla_principal import PantallaCaja

# Paleta de colores
COLOR_FONDO = "#f4f6f7"
COLOR_BLANCO = "#ffffff"
COLOR_BOTON = "#4CAF50"
COLOR_REGISTRO = "#2196F3"
FUENTE = ("Segoe UI", 11)


class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("Iniciar Sesión")
        master.geometry("400x300")
        master.configure(bg=COLOR_FONDO)
        master.resizable(False, False)

        # Contenedor centrado tipo "card"
        frame = tk.Frame(master, bg=COLOR_BLANCO, bd=0)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=320, height=230)

        # Botón registrar (esquina)
        self.boton_registro = tk.Button(master, text="➕ Registrar empleado", font=("Segoe UI", 9),
                                        command=self.abrir_registro, bg=COLOR_FONDO, bd=0, fg="#007ACC", activebackground=COLOR_FONDO)
        self.boton_registro.place(relx=1.0, x=-10, y=10, anchor="ne")

        # Widgets dentro del frame
        tk.Label(frame, text="Correo del empleado", bg=COLOR_BLANCO, font=FUENTE).pack(pady=(20, 5))

        self.entry_correo = tk.Entry(frame, font=FUENTE, width=30, relief="solid", bd=1)
        self.entry_correo.pack()

        self.boton_login = tk.Button(frame, text="Iniciar sesión", font=("Segoe UI", 10, "bold"),
                                     command=self.iniciar_sesion, bg=COLOR_BOTON, fg="white",
                                     activebackground="#45a049", relief="flat", height=2, width=20)
        self.boton_login.pack(pady=20)

        self.entry_correo.bind("<Return>", lambda event: self.iniciar_sesion())

    def iniciar_sesion(self):
        correo = self.entry_correo.get().strip()
        if not correo:
            messagebox.showwarning("Campo vacío", "Por favor, ingresa el correo del empleado.")
            return

        empleados = cargar_empleados()
        empleado = next((e for e in empleados if e["correo"] == correo), None)

        if not empleado:
            messagebox.showerror("Error", "Correo no encontrado.")
            return

        nombre = empleado["nombre"]
        if registrar_inicio_sesion(nombre):
            messagebox.showinfo("Sesión iniciada", f"Bienvenido: {nombre}")
            self.master.destroy()

            root = tk.Tk()
            PantallaCaja(root, mostrar_login)
            root.mainloop()

    def abrir_registro(self):
        RegistroEmpleado(self.master)


class RegistroEmpleado:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Registrar Empleado")
        self.window.geometry("360x350")
        self.window.configure(bg=COLOR_FONDO)
        self.window.resizable(False, False)

        frame = tk.Frame(self.window, bg=COLOR_BLANCO)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=320, height=280)

        tk.Label(frame, text="Nombre", bg=COLOR_BLANCO, font=FUENTE).pack(pady=(15, 0))
        self.entry_nombre = tk.Entry(frame, font=FUENTE, width=28, relief="solid", bd=1)
        self.entry_nombre.pack(pady=5)

        tk.Label(frame, text="Correo", bg=COLOR_BLANCO, font=FUENTE).pack()
        self.entry_correo = tk.Entry(frame, font=FUENTE, width=28, relief="solid", bd=1)
        self.entry_correo.pack(pady=5)

        tk.Label(frame, text="Puesto", bg=COLOR_BLANCO, font=FUENTE).pack()
        self.opciones_puesto = ["Encargado", "Cajero"]
        self.puesto_var = tk.StringVar(value=self.opciones_puesto[0])
        self.combo_puesto = ttk.Combobox(frame, values=self.opciones_puesto,
                                         textvariable=self.puesto_var, state="readonly", font=FUENTE, width=25)
        self.combo_puesto.pack(pady=5)

        self.boton_guardar = tk.Button(frame, text="Guardar", font=("Segoe UI", 10, "bold"),
                                       command=self.registrar_empleado, bg=COLOR_REGISTRO, fg="white",
                                       activebackground="#1976D2", relief="flat", height=2, width=18)
        self.boton_guardar.pack(pady=15)

    def registrar_empleado(self):
        nombre = self.entry_nombre.get().strip()
        correo = self.entry_correo.get().strip()
        puesto = self.puesto_var.get().strip()

        if not nombre or not correo:
            messagebox.showwarning("Campos vacíos", "Completa todos los campos.")
            return

        empleados = cargar_empleados()
        siguiente_id = 1
        if empleados:
            ids = [int(e["id"]) for e in empleados if str(e["id"]).isdigit()]
            if ids:
                siguiente_id = max(ids) + 1

        if siguiente_id == 1:
            puesto = "Dueño"

        nuevo_empleado = {
            "id": str(siguiente_id),
            "nombre": nombre,
            "correo": correo,
            "puesto": puesto,
            "usuario": nombre,
            "activo": False
        }

        if agregar_empleado(nuevo_empleado):
            messagebox.showinfo("Éxito", f"Empleado registrado correctamente como {puesto}.")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "No se pudo registrar al empleado.")


def mostrar_login(root):
    LoginApp(root)


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
