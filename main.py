import tkinter as tk
from ui.pantalla_login import LoginApp

def main():
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
