import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.empleados import (
    PUESTO_DUENO,
    agregar_empleado,
    buscar_empleado_por_correo,
    cargar_empleados,
    listar_puestos_disponibles,
    normalizar_correo,
)
from modules.login import registrar_inicio_sesion
from ui.pantalla_principal import PantallaCaja

COLOR_FONDO = "#f4f6f7"
COLOR_BLANCO = "#ffffff"
COLOR_BOTON = "#4CAF50"
COLOR_REGISTRO = "#2196F3"
FUENTE = ("Segoe UI", 11)


def limpiar_ventana_principal(master):
    pantalla_activa = getattr(master, "_pantalla_activa", None)
    if pantalla_activa is not None and hasattr(pantalla_activa, "liberar_recursos"):
        try:
            pantalla_activa.liberar_recursos()
        except Exception:
            pass

    try:
        master.attributes("-fullscreen", False)
    except tk.TclError:
        pass

    for evento in ("<Return>", "<F2>", "<Escape>", "<Configure>"):
        try:
            master.unbind(evento)
        except tk.TclError:
            pass

    if hasattr(master, "_pantalla_activa"):
        master._pantalla_activa = None

    for child in master.winfo_children():
        try:
            child.destroy()
        except tk.TclError:
            pass


def mostrar_caja(master):
    limpiar_ventana_principal(master)
    PantallaCaja(master, mostrar_login)


class LoginApp:
    def __init__(self, master):
        self.master = master
        self.registro_abierto = None
        master.title("Iniciar sesion")
        master.geometry("460x360")
        master.configure(bg=COLOR_FONDO)
        master.resizable(False, False)

        tk.Label(
            master,
            text="Kiosco App",
            bg=COLOR_FONDO,
            fg="#1f2937",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(22, 4))

        self.mensaje_secundario_var = tk.StringVar(value="")
        tk.Label(
            master,
            textvariable=self.mensaje_secundario_var,
            bg=COLOR_FONDO,
            fg="#52606d",
            font=("Segoe UI", 10),
        ).pack()

        frame = tk.Frame(master, bg=COLOR_BLANCO, bd=1, relief="solid")
        frame.place(relx=0.5, rely=0.56, anchor="center", width=360, height=220)

        self.boton_registro = tk.Button(
            master,
            text="Registrar empleado",
            font=("Segoe UI", 9, "bold"),
            command=self.abrir_registro,
            bg=COLOR_FONDO,
            bd=0,
            fg="#007ACC",
            activebackground=COLOR_FONDO,
        )
        self.boton_registro.place(relx=1.0, x=-10, y=10, anchor="ne")

        tk.Label(
            frame,
            text="Correo del empleado",
            bg=COLOR_BLANCO,
            fg="#374151",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=26, pady=(24, 6))

        self.entry_correo = tk.Entry(frame, font=FUENTE, width=32, relief="solid", bd=1)
        self.entry_correo.pack(ipady=4)

        tk.Label(
            frame,
            text="Ejemplo: empleado@negocio.com",
            bg=COLOR_BLANCO,
            fg="#6b7280",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=26, pady=(6, 10))

        self.boton_login = tk.Button(
            frame,
            text="Iniciar sesion",
            font=("Segoe UI", 10, "bold"),
            command=self.iniciar_sesion,
            bg=COLOR_BOTON,
            fg="white",
            activebackground="#45a049",
            relief="flat",
            height=2,
            width=22,
        )
        self.boton_login.pack(pady=12)

        self.entry_correo.bind("<Return>", lambda event: self.iniciar_sesion())
        self._actualizar_estado_login()
        self.master.after(120, self._forzar_registro_inicial_si_hace_falta)

    def _hay_empleados_registrados(self):
        return bool(cargar_empleados())

    def _actualizar_estado_login(self):
        if self._hay_empleados_registrados():
            self.mensaje_secundario_var.set("Ingresa con el correo del empleado activo")
            self.boton_registro.config(text="Registrar empleado")
            self.boton_login.config(state="normal")
            return

        self.mensaje_secundario_var.set("Todavia no hay empleados. Primero registra el due\u00f1o.")
        self.boton_registro.config(text="Registrar due\u00f1o")
        self.boton_login.config(state="disabled")

    def _forzar_registro_inicial_si_hace_falta(self):
        self._actualizar_estado_login()
        if not self._hay_empleados_registrados():
            self.abrir_registro(es_obligatorio=True)

    def iniciar_sesion(self):
        correo = normalizar_correo(self.entry_correo.get())
        if not correo:
            messagebox.showwarning(
                "Campo vacio",
                "Por favor, ingresa el correo del empleado.",
                parent=self.master,
            )
            return

        empleado = buscar_empleado_por_correo(correo)
        if not empleado:
            messagebox.showerror("Error", "Correo no encontrado.", parent=self.master)
            return

        nombre = empleado["nombre"]
        usuario_login = empleado.get("usuario") or empleado.get("correo") or nombre
        if registrar_inicio_sesion(usuario_login):
            messagebox.showinfo("Sesion iniciada", f"Bienvenido: {nombre}", parent=self.master)
            self.master.after_idle(lambda: mostrar_caja(self.master))

    def abrir_registro(self, es_obligatorio=None):
        if self.registro_abierto is not None:
            try:
                if self.registro_abierto.window.winfo_exists():
                    self.registro_abierto.window.lift()
                    self.registro_abierto.window.focus_force()
                    return
            except tk.TclError:
                self.registro_abierto = None

        if es_obligatorio is None:
            es_obligatorio = not self._hay_empleados_registrados()

        self.registro_abierto = RegistroEmpleado(
            self.master,
            on_success=self._registro_exitoso,
            on_close=self._registro_cerrado,
            es_obligatorio=es_obligatorio,
        )

    def _registro_exitoso(self):
        self._actualizar_estado_login()
        self.entry_correo.delete(0, tk.END)
        self.entry_correo.focus_set()

    def _registro_cerrado(self):
        self.registro_abierto = None


class RegistroEmpleado:
    def __init__(self, parent, on_success=None, on_close=None, es_obligatorio=False):
        self.on_success = on_success
        self.on_close = on_close
        self.es_obligatorio = es_obligatorio
        self.window = tk.Toplevel(parent)
        self.window.title("Registrar due\u00f1o" if es_obligatorio else "Registrar empleado")
        self.window.geometry("430x500")
        self.window.configure(bg=COLOR_FONDO)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.cerrar)

        frame = tk.Frame(self.window, bg=COLOR_BLANCO, bd=1, relief="solid")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(
            frame,
            text="Registrar due\u00f1o" if es_obligatorio else "Nuevo empleado",
            bg=COLOR_BLANCO,
            fg="#1f2937",
            font=("Segoe UI", 15, "bold"),
        ).pack(pady=(18, 8))

        tk.Label(frame, text="Nombre", bg=COLOR_BLANCO, font=FUENTE).pack(anchor="w", padx=28)
        self.entry_nombre = tk.Entry(frame, font=FUENTE, width=28, relief="solid", bd=1)
        self.entry_nombre.pack(pady=5, ipady=3)

        tk.Label(frame, text="Correo", bg=COLOR_BLANCO, font=FUENTE).pack(anchor="w", padx=28)
        self.entry_correo = tk.Entry(frame, font=FUENTE, width=28, relief="solid", bd=1)
        self.entry_correo.pack(pady=5, ipady=3)

        tk.Label(frame, text="Puesto", bg=COLOR_BLANCO, font=FUENTE).pack(anchor="w", padx=28)
        self.es_primer_registro = not cargar_empleados()
        if self.es_primer_registro:
            self.opciones_puesto = [PUESTO_DUENO]
        else:
            self.opciones_puesto = [puesto for puesto in listar_puestos_disponibles() if puesto != PUESTO_DUENO]

        self.puesto_var = tk.StringVar(value=self.opciones_puesto[0])
        self.combo_puesto = ttk.Combobox(
            frame,
            values=self.opciones_puesto,
            textvariable=self.puesto_var,
            state="readonly",
            font=FUENTE,
            width=25,
        )
        self.combo_puesto.pack(pady=5)
        if self.es_primer_registro:
            self.combo_puesto.state(["disabled"])

        tk.Label(
            frame,
            text="El primer usuario registrado queda como due\u00f1o.",
            bg=COLOR_BLANCO,
            fg="#6b7280",
            font=("Segoe UI", 9),
        ).pack(pady=(6, 12), padx=28, anchor="w")

        self.boton_guardar = tk.Button(
            frame,
            text="Registrar due\u00f1o" if self.es_primer_registro else "Guardar",
            font=("Segoe UI", 10, "bold"),
            command=self.registrar_empleado,
            bg=COLOR_REGISTRO,
            fg="white",
            activebackground="#1976D2",
            relief="flat",
            height=2,
            width=24,
        )
        self.boton_guardar.pack(fill="x", padx=28, pady=(0, 12))

        tk.Label(
            frame,
            text="Si completas nombre y correo, este boton crea el usuario.",
            bg=COLOR_BLANCO,
            fg="#6b7280",
            font=("Segoe UI", 9),
        ).pack(padx=28, anchor="w")

        self.entry_nombre.focus_set()

    def registrar_empleado(self):
        nombre = self.entry_nombre.get().strip()
        correo = normalizar_correo(self.entry_correo.get())
        puesto = self.puesto_var.get().strip()

        if not nombre or not correo:
            messagebox.showwarning(
                "Campos vacios",
                "Completa todos los campos.",
                parent=self.window,
            )
            return

        if buscar_empleado_por_correo(correo):
            messagebox.showerror(
                "Error",
                "Ya existe un empleado con ese correo.",
                parent=self.window,
            )
            return

        empleados = cargar_empleados()
        siguiente_id = 1
        if empleados:
            ids = [int(empleado["id"]) for empleado in empleados if str(empleado["id"]).isdigit()]
            if ids:
                siguiente_id = max(ids) + 1

        if siguiente_id == 1:
            puesto = PUESTO_DUENO

        nuevo_empleado = {
            "id": str(siguiente_id),
            "nombre": nombre,
            "correo": correo,
            "puesto": puesto,
            "usuario": correo or nombre,
            "activo": False,
        }

        if agregar_empleado(nuevo_empleado):
            messagebox.showinfo(
                "Exito",
                f"Empleado registrado correctamente como {puesto}.",
                parent=self.window,
            )
            if self.on_success:
                self.on_success()
            self.cerrar()
        else:
            messagebox.showerror(
                "Error",
                "No se pudo registrar al empleado.",
                parent=self.window,
            )

    def cerrar(self):
        try:
            self.window.grab_release()
        except tk.TclError:
            pass

        if self.window.winfo_exists():
            self.window.destroy()

        if self.on_close:
            self.on_close()


def mostrar_login(root):
    limpiar_ventana_principal(root)
    LoginApp(root)


if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()
