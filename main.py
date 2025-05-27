import tkinter as tk
from tkinter import simpledialog, messagebox
from ui.pantalla_login import LoginApp
import tkinter as tk
from tkinter import simpledialog, messagebox
from ui.pantalla_login import LoginApp
from modules.licencia import esta_activado, activar, generar_clave_mensual, CLAVE_MAESTRA

def main():
    if not esta_activado():
        root = tk.Tk()
        root.withdraw()
        while True:
            clave = simpledialog.askstring("Licencia", "Ingrese la clave mensual:")
            if clave is None:
                return  # Usuario canceló

            if clave == CLAVE_MAESTRA:
                activar("permanente")
                messagebox.showinfo("Activación", "Activación permanente exitosa.")
                break
            elif clave == generar_clave_mensual():
                activar("mensual")
                messagebox.showinfo("Activación", "Activación mensual exitosa.")
                break
            else:
                messagebox.showerror("Error", "Clave incorrecta. Intente nuevamente.")

        root.destroy()  # Cerrar el root temporal
    
    # Ahora sí, lanzar app real
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
