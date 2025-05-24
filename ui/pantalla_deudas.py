import tkinter as tk
from tkinter import ttk, messagebox
from modules.deudas import cargar_deudas, pagar_deuda

COLOR_FONDO = "#f4f6f7"
COLOR_BLANCO = "#ffffff"
COLOR_BOTON = "#4CAF50"
COLOR_ENTRADA = "#ffffff"
FUENTE_TEXTO = ("Segoe UI", 10)
FUENTE_TITULO = ("Segoe UI", 11, "bold")

class PantallaDeudas:
    def __init__(self, master):
        self.master = tk.Toplevel(master)
        self.master.title("Gestión de Deudas")
        self.master.geometry("900x600")
        self.master.configure(bg=COLOR_FONDO)

        self.busqueda_var = tk.StringVar()
        self.orden_var = tk.StringVar(value="Monto descendente")

        # Frame superior (buscador + combo orden)
        top_frame = tk.Frame(self.master, bg=COLOR_FONDO)
        top_frame.pack(pady=10, fill=tk.X, padx=20)

        tk.Label(top_frame, text="🔍 Buscar por DNI:", bg=COLOR_FONDO, font=FUENTE_TITULO).pack(side=tk.LEFT)
        self.entry_buscar = tk.Entry(top_frame, textvariable=self.busqueda_var, font=FUENTE_TEXTO, width=25,
                                     bg=COLOR_ENTRADA, relief="solid", bd=1)
        self.entry_buscar.pack(side=tk.LEFT, padx=10)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.actualizar_lista())

        opciones_orden = ["Monto descendente", "Monto ascendente"]
        self.combo_orden = ttk.Combobox(top_frame, values=opciones_orden, state="readonly",
                                        textvariable=self.orden_var, width=20, font=FUENTE_TEXTO)
        self.combo_orden.pack(side=tk.RIGHT)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda e: self.actualizar_lista())

        # Frame scrollable para clientes + productos
        frame_scroll = tk.Frame(self.master, bg=COLOR_FONDO)
        frame_scroll.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(frame_scroll, bg=COLOR_FONDO, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        self.inner_frame = tk.Frame(canvas, bg=COLOR_FONDO)

        self.inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botón pagar
        btn_frame = tk.Frame(self.master, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        self.btn_pagar = tk.Button(btn_frame, text="💵 Pagar Deuda", font=("Segoe UI", 10, "bold"),
                                   bg=COLOR_BOTON, fg="white", height=2, width=20,
                                   command=self.pagar_deuda_dialog, relief="flat", cursor="hand2",
                                   activebackground="#45a049")
        self.btn_pagar.pack()

        self.actualizar_lista()

    def actualizar_lista(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.cliente_seleccionado_frame = None  # Reset selección

        clientes = cargar_deudas()
        busqueda = self.busqueda_var.get().strip()
        orden = self.orden_var.get()

        if busqueda:
            clientes = [c for c in clientes if c["dni"].startswith(busqueda)]

        clientes_deuda = [c for c in clientes if c.get("monto", 0) > 0]
        reverse = "descendente" in orden
        clientes_deuda.sort(key=lambda c: c["monto"], reverse=reverse)

        if not clientes_deuda:
            tk.Label(self.inner_frame, text="No hay deudas que coincidan.", font=FUENTE_TITULO, bg=COLOR_FONDO).pack(pady=20)
            return

        for cliente in clientes_deuda:
            frame_cliente = tk.Frame(self.inner_frame, bg=COLOR_BLANCO, bd=1, relief="solid")
            frame_cliente.pack(fill="x", pady=5, padx=5)
            frame_cliente.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))

            nombre = cliente.get("nombre", "(Sin nombre)")
            deuda = cliente.get("monto", 0)
            productos = cliente.get("productos", [])

            header = f"DNI: {cliente['dni']}   |   Nombre: {nombre}   |   Deuda: ${deuda:.2f}"
            label_header = tk.Label(frame_cliente, text=header, font=FUENTE_TITULO, bg=COLOR_BLANCO, anchor="w")
            label_header.pack(fill="x", padx=10, pady=5)
            label_header.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))

            if productos:
                for prod in productos:
                    texto_prod = f"• {prod['cantidad']} x {prod['nombre']} = ${prod['subtotal']:.2f}"
                    label_prod = tk.Label(frame_cliente, text=texto_prod, font=FUENTE_TEXTO, bg=COLOR_BLANCO, anchor="w")
                    label_prod.pack(fill="x", padx=20)
                    label_prod.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))
            else:
                label_sin = tk.Label(frame_cliente, text="(Sin productos cargados)", font=FUENTE_TEXTO,
                                    bg=COLOR_BLANCO, fg="gray", anchor="w")
                label_sin.pack(fill="x", padx=20)
                label_sin.bind("<Button-1>", lambda e, f=frame_cliente: self.seleccionar_cliente(f))

    def seleccionar_cliente(self, frame):
        # Desmarcar el anterior
        if hasattr(self, "cliente_seleccionado_frame") and self.cliente_seleccionado_frame:
            self.cliente_seleccionado_frame.config(bg=COLOR_BLANCO)
            for widget in self.cliente_seleccionado_frame.winfo_children():
                widget.config(bg=COLOR_BLANCO)

        # Marcar el nuevo
        self.cliente_seleccionado_frame = frame
        frame.config(bg="#d0eaff")  # Celeste claro
        for widget in frame.winfo_children():
            widget.config(bg="#d0eaff")


    def pagar_deuda_dialog(self):
        frame = getattr(self, "cliente_seleccionado_frame", None)
        if not frame:
            messagebox.showwarning("Atención", "Selecciona un cliente con deuda haciendo clic en él.")
            return

        header_label = frame.winfo_children()[0]
        texto = header_label.cget("text")
        dni = texto.split("DNI:")[1].split("|")[0].strip()

        # Ventana de pago
        pago_window = tk.Toplevel(self.master)
        pago_window.title(f"Pagar deuda - DNI {dni}")
        pago_window.geometry("350x180")
        pago_window.configure(bg=COLOR_FONDO)
        pago_window.grab_set()

        tk.Label(pago_window, text=f"Ingrese monto a pagar para DNI {dni}:", bg=COLOR_FONDO, font=FUENTE_TEXTO).pack(pady=(20, 5))
        monto_var = tk.StringVar()
        entry_monto = tk.Entry(pago_window, textvariable=monto_var, font=FUENTE_TEXTO, bg=COLOR_ENTRADA, relief="solid", bd=1)
        entry_monto.pack(pady=5)
        entry_monto.focus()

        def confirmar_pago():
            try:
                pago = float(monto_var.get())
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido.")
                return

            if pagar_deuda(dni, pago):
                messagebox.showinfo("Éxito", f"Pago de ${pago:.2f} registrado.")
                self.actualizar_lista()
                pago_window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo registrar el pago.")

        tk.Button(pago_window, text="Confirmar Pago", command=confirmar_pago,
                font=("Segoe UI", 10, "bold"), bg=COLOR_BOTON, fg="white",
                relief="flat", width=18, height=2, activebackground="#45a049").pack(pady=15)

