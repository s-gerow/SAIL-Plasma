import tkinter as tk
from tkinter.dialog import Dialog
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
import openpyxl as op
import numpy as np
import pandas as pd
import os



class excel_reader(tk.Tk):
    def __init__(self):
        super().__init__()

        self.workbook = None
        headers = ['D_Y(Osc)', 'V_in', 'V(Volts)', 'Current (Amp)', 'p_Exact(Torr)', 'p_Predict(Torr)', 'dis (cm)', 'd(V)', 'd(p)', 'd(d)', 'd(pd)']
        
        mainframe = tk.LabelFrame(self,text="This is the mainframe")
        mainframe.pack()
        tk.Label(mainframe, text="This is a label on the window").pack()

        tk.Button(mainframe, text="Choose Excel File", command= self.choose_excel).pack()



        self.filevar = tk.StringVar()
        tk.Spinbox(mainframe, textvariable=self.filevar, state='readonly').pack()

        self.workbook_sheets = ['New']

        self.sheetVar = tk.StringVar()
        tk.Label(mainframe, text="Choose the File Sheet").pack()

        self.sheetbox = ttk.Combobox(mainframe, textvariable=self.sheetVar, values=self.workbook_sheets)
        self.sheetbox.pack()

        tk.Button(mainframe, text="read first line of sheet", command=self.read_first_line).pack()


    def choose_excel(self):
        filepath = fd.askopenfilename()
        filename = os.path.splitext(os.path.basename(filepath))[0]+os.path.splitext(os.path.basename(filepath))[1]
        self.filevar.set(filename)
        self.workbook = op.load_workbook(filename = filepath)
        for i in self.workbook.sheetnames:
            self.workbook_sheets.append(i)
        print(self.workbook_sheets)
        self.sheetbox['values'] = self.workbook_sheets

    def read_first_line(self):
        sheet = self.workbook[self.sheetVar.get()]
        headers = [x.value for x in sheet["A1:K1"][0]]
        print(headers)
        




root = excel_reader()

root.mainloop()