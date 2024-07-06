#Interface for Plasma Chamber
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Plasma Chamber 1.0")

ToggleFrame = tk.Frame(root, relief = 'sunken', )
ToggleFrame.place(relx=0, rely=0, relwidth=0.5, relheight=1)
PlotFrame = tk.Frame(root)
PlotFrame.place(relx=0.5, rely=0, relwidth=0.5, relheight = 1)

root.mainloop()