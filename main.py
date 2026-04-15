import sys
import tkinter as tk
from tkinter import messagebox, ttk

from modules.console import registrar_excepcion
from modules.licencia import (
    describir_estado_licencia,
    enviar_whatsapp_registro,
    obtener_id_instalacion,
    validar_licencia,
)
from ui.pantalla_login import LoginApp


def _manejar_excepcion_global(exc_type, exc_value, exc_traceback):
    registrar_excepcion(
        "Excepcion no controlada",
        (exc_type, exc_value, exc_traceback),
    )


def _instalar_manejador_tk(root):
    def _manejar_callback_exception(exc_type, exc_value, exc_traceback):
        registrar_excepcion(
            "Error en callback de Tkinter",
            (exc_type, exc_value, exc_traceback),
        )
        try:
            messagebox.showerror(
                "Error interno",
                "Ocurrio un error interno en la aplicacion.\n"
                "Revisa data\\_system\\app.log para ver el detalle.",
                parent=root,
            )
        except Exception:
            pass

    root.report_callback_exception = _manejar_callback_exception


def _mostrar_aviso_offline(estado):
    root_temporal = tk.Tk()
    root_temporal.withdraw()
    try:
        limite = estado.get("gracia_offline_hasta") or "fecha no disponible"
        messagebox.showwarning(
            "Licencia temporal",
            "No se pudo validar la licencia por internet.\n\n"
            f"La aplicacion seguira funcionando hasta {limite} "
            "si vuelve la conexion antes de que termine la gracia offline.",
        )
    finally:
        root_temporal.destroy()


def _texto_activacion(estado):
    instrucciones = (
        "1. Copie este ID de instalacion.\n"
        "2. Enviemelo a mi o al revendedor.\n"
        "3. Cuando quede cargado en Google Sheets como activa, presione Reintentar."
    )
    return f"{describir_estado_licencia(estado)}\n\n{instrucciones}"


class VentanaActivacion:
    def __init__(self, master, estado_inicial):
        self.master = master
        self.master.title("Activacion de licencia")
        self.master.resizable(False, False)
        self.master.protocol("WM_DELETE_WINDOW", self._salir)
        self.resultado = False
        self.estado_validado = None
        self.id_instalacion = obtener_id_instalacion()

        contenedor = ttk.Frame(master, padding=18)
        contenedor.grid(sticky="nsew")

        ttk.Label(
            contenedor,
            text="Esta instalacion no esta activa",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            contenedor,
            text="ID unico de esta instalacion:",
        ).grid(row=1, column=0, pady=(12, 4), sticky="w")

        self.id_var = tk.StringVar(value=self.id_instalacion)
        campo_id = ttk.Entry(contenedor, textvariable=self.id_var, width=42, state="readonly")
        campo_id.grid(row=2, column=0, sticky="ew")

        self.estado_var = tk.StringVar()
        ttk.Label(
            contenedor,
            textvariable=self.estado_var,
            wraplength=380,
            justify="left",
        ).grid(row=3, column=0, pady=(12, 16), sticky="w")

        self.progreso_var = tk.StringVar(value="")
        ttk.Label(
            contenedor,
            textvariable=self.progreso_var,
            foreground="#1f5f99",
        ).grid(row=4, column=0, pady=(0, 10), sticky="w")

        botonera = ttk.Frame(contenedor)
        botonera.grid(row=5, column=0, sticky="e")

        ttk.Button(botonera, text="Copiar ID", command=self._copiar_id).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(botonera, text="WhatsApp", command=self._abrir_whatsapp).grid(
            row=0, column=1, padx=(0, 8)
        )
        self.boton_reintentar = ttk.Button(botonera, text="Reintentar", command=self._reintentar)
        self.boton_reintentar.grid(row=0, column=2, padx=(0, 8))
        ttk.Button(botonera, text="Salir", command=self._salir).grid(row=0, column=3)

        contenedor.columnconfigure(0, weight=1)
        self._actualizar_estado(estado_inicial)

    def _actualizar_estado(self, estado):
        self.estado_var.set(_texto_activacion(estado))
        self.progreso_var.set("")

    def _copiar_id(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.id_instalacion)
        self.master.update()
        self.estado_var.set(
            "ID copiado al portapapeles.\n\n"
            "Envielo para que la instalacion sea activada y luego presione Reintentar."
        )
        self.progreso_var.set("")

    def _abrir_whatsapp(self):
        resultado = enviar_whatsapp_registro(self.id_instalacion)
        if resultado["ok"]:
            self.estado_var.set(resultado["mensaje"])
            self.progreso_var.set("")
            return

        messagebox.showwarning(
            "WhatsApp",
            resultado["mensaje"],
        )

    def _reintentar(self):
        self.progreso_var.set("Reintentando validacion online...")
        self.boton_reintentar.state(["disabled"])
        self.master.update_idletasks()

        try:
            estado = validar_licencia(forzar=True)
        except Exception as error:
            self.boton_reintentar.state(["!disabled"])
            self.progreso_var.set("Ocurrio un error al reintentar la validacion.")
            messagebox.showerror("Licencia", f"No se pudo completar la validacion:\n{error}")
            return

        if estado["permitir_uso"]:
            self.progreso_var.set("Licencia validada correctamente. Abriendo sistema...")
            self.master.update_idletasks()
            messagebox.showinfo("Licencia", "Licencia validada correctamente.")
            self.resultado = True
            self.estado_validado = estado
            self.master.destroy()
            return

        self.boton_reintentar.state(["!disabled"])
        self._actualizar_estado(estado)
        self.progreso_var.set("La validacion no fue exitosa. Revise el estado mostrado abajo.")
        messagebox.showwarning("Licencia", describir_estado_licencia(estado))

    def _salir(self):
        self.resultado = False
        self.master.destroy()


def _gestionar_licencia():
    estado = validar_licencia()
    if estado["permitir_uso"]:
        if estado["origen"] == "gracia_offline":
            _mostrar_aviso_offline(estado)
        return estado

    root_activacion = tk.Tk()
    _instalar_manejador_tk(root_activacion)
    ventana = VentanaActivacion(root_activacion, estado)
    root_activacion.mainloop()
    if ventana.resultado:
        return ventana.estado_validado or validar_licencia()
    return None


def main():
    sys.excepthook = _manejar_excepcion_global

    estado_licencia = _gestionar_licencia()
    if not estado_licencia:
        return

    root = tk.Tk()
    root._estado_licencia = estado_licencia
    _instalar_manejador_tk(root)
    LoginApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
