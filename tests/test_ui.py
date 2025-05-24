import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tkinter as tk
from tkinter import messagebox
from modules.productos import agregar_producto



def guardar_desde_ui():
    try:
        producto = {
            "id": entrada_id.get(),
            "nombre": entrada_nombre.get(),
            "precio": float(entrada_precio.get()),
            "stock_actual": int(entrada_stock.get()),
            "stock_minimo": int(entrada_stock_minimo.get())
        }
    except ValueError:
        messagebox.showerror("Error", "Stock debe ser entero y precio debe ser numérico.")
        return

    if agregar_producto(producto):
        messagebox.showinfo("Éxito", f"Producto '{producto['nombre']}' agregado.")
        entrada_id.delete(0, tk.END)
        entrada_nombre.delete(0, tk.END)
        entrada_stock.delete(0, tk.END)
        entrada_stock_minimo.delete(0, tk.END)
        entrada_precio.delete(0, tk.END)
    else:
        messagebox.showwarning("Advertencia", "No se pudo agregar el producto. Verifica los datos o el ID duplicado.")

ventana = tk.Tk()
ventana.title("Gestión de Productos")
ventana.geometry("300x250")

tk.Label(ventana, text="ID del producto:").pack()
entrada_id = tk.Entry(ventana)
entrada_id.pack()

tk.Label(ventana, text="Nombre:").pack()
entrada_nombre = tk.Entry(ventana)
entrada_nombre.pack()

tk.Label(ventana, text="Stock actual:").pack()
entrada_stock = tk.Entry(ventana)
entrada_stock.pack()

tk.Label(ventana, text="Stock minimo:").pack()
entrada_stock_minimo = tk.Entry(ventana)
entrada_stock_minimo.pack()

tk.Label(ventana, text="Precio:").pack()
entrada_precio = tk.Entry(ventana)
entrada_precio.pack()

tk.Button(ventana, text="Agregar producto", command=guardar_desde_ui).pack(pady=10)

ventana.mainloop()