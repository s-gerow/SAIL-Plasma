import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np
from matplotlib.figure import Figure
import matplotlib.colors as mcolors
from tkinter import filedialog as fd
import pandas as pd
from CurveFit import (plot_fit, plot_data, R24_Cylindrical, Townsend, R24_Spherical)
import platform

class PlotMaker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plot Maker")
        self.geometry("1200x600")
        self.curves = []
        self.fig_title = tk.StringVar(value="Paschen Curve")
        self.x_label = tk.StringVar(value="$pd (Torr*cm)$")
        self.y_label = tk.StringVar(value="$V_{cr} (V)$")
        
        #figure object which stores the axes data
        self.figure = Figure(dpi=100)
        #axes object which holds plot data and gets placed on the figure object
        self.axes = self.figure.add_subplot()
        #default values for plot and variables which can be edited by tkinter widgets
        self.y_range = [tk.DoubleVar(value=0),tk.DoubleVar(value=1000)]
        self.x_range = [tk.DoubleVar(value=0),tk.DoubleVar(value=10)]
        self.x_scale = tk.StringVar(value="linear")
        self.y_scale = tk.StringVar(value="linear")

        #function which creates all tkinter widgets and places them on the window
        self.create_widgets()
        #function which generates the plot canvas
        self.create_plot()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.figure_frame = ttk.Frame(self)
        self.figure_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=0, column=1)

        #this is the frame which holdes the scrollable canvas and is where all of the new boxes for different curves are stored
        #each time a new curve is desired, a new frame is added to this frame which stores the data and widgets for that curve
        self.curves_container = ttk.LabelFrame(self, text="Curves")
        self.curves_container.grid(row=1, column=1, sticky="nsew")
        # This makes a tkinter canvas which lives in the curves container and will hold all the other frames
        self.curves_canvas = tk.Canvas(self.curves_container, borderwidth=0)
        #this is a new frame which is placed on the canvas and holds the other frames and allows scrolling
        self.curves_scrollable = tk.Frame(self.curves_canvas)
        #this is the scrollbar which is placed on the curves container which allows you to scroll the curves canvas
        vsb = tk.Scrollbar(self.curves_container, orient="vertical", command=self.curves_canvas.yview)
        #this sets the canvas scrollregion to the scrollbar so they can communicate
        self.curves_canvas.configure(yscrollcommand=vsb.set)

        #this adds the scrollbar to the curves container
        vsb.pack(side="right", fill="y")
        #this adds the curves canvas to the curves container
        self.curves_canvas.pack(side="left", fill="both", expand=True)
        #this creates a windows which holds the scrollable frame and is placed on the canvas
        self.curves_canvas.create_window((4,4), window=self.curves_scrollable, anchor="nw")

        # keep canvas scrollregion in sync with inner frame
        self.curves_scrollable.bind("<Configure>", lambda event, canvas=self.curves_canvas: self.onFrameConfigure(canvas))

        # Bind mouse enter/leave so wheel events scroll this canvas while hovered
        self.curves_canvas.bind("<Enter>", lambda e: self._bind_to_mousewheel(self.curves_canvas))
        self.curves_canvas.bind("<Leave>", lambda e: self._unbind_from_mousewheel(self.curves_canvas))


        #this is back to the noraml widget stuff
        self.update_button = ttk.Button(self.button_frame, text="Update Plot", command=self.update_plot)
        self.update_button.grid(row=0, column=0, padx=10, pady=10)
        self.add_datacurve_button = ttk.Button(self.button_frame, text="Add Data Curve", command=self.create_curve_frame)
        self.add_datacurve_button.grid(row=0, column=1, padx=10, pady=10)
        self.add_theoreticalcurve_button = ttk.Button(self.button_frame, text="Add Theoretical Curve", command=self.create_theoretical_curve_frame)
        self.add_theoreticalcurve_button.grid(row=0, column=2, padx=10, pady=10)
        ttk.Label(self.button_frame, text="Title:").grid(row=1, column=0, pady=5)
        self.title_entry = ttk.Entry(self.button_frame, textvariable=self.fig_title)
        self.title_entry.grid(row=1, column=1, columnspan=2, pady=5)
        ttk.Label(self.button_frame, text="X Label:").grid(row=2, column=0, pady=5)
        self.xlabel_entry = ttk.Entry(self.button_frame, textvariable=self.x_label)
        self.xlabel_entry.grid(row=2, column=1, columnspan=2, pady=5)
        ttk.Label(self.button_frame, text="Y Label:").grid(row=3, column=0, pady=5)
        self.ylabel_entry = ttk.Entry(self.button_frame, textvariable=self.y_label)
        self.ylabel_entry.grid(row=3, column=1, columnspan=2, pady=5)
        ttk.Label(self.button_frame, text='X Range:').grid(row=4, column=0, pady=5)
        self.x_min_entry = ttk.Entry(self.button_frame, width=10, textvariable=self.x_range[0])
        self.x_min_entry.grid(row=4, column=1, pady=5)
        self.x_max_entry = ttk.Entry(self.button_frame, width=10, textvariable=self.x_range[1])
        self.x_max_entry.grid(row=4, column=2, pady=5)
        ttk.Label(self.button_frame, text='Y Range:').grid(row=5, column=0, pady=5)
        self.y_min_entry = ttk.Entry(self.button_frame, width=10, textvariable=self.y_range[0])
        self.y_min_entry.grid(row=5, column=1, pady=5)
        self.y_max_entry = ttk.Entry(self.button_frame, width=10, textvariable=self.y_range[1])
        self.y_max_entry.grid(row=5, column=2, pady=5)
        self.save_button = ttk.Button(self.button_frame, text="Save Figure", command=self.save_current_figure)
        self.save_button.grid(row=6, column=0, columnspan=3, pady=10)
        
        # self.linlin_button = ttk.Checkbutton(self.button_frame, text="Linear Scale", command=lambda: self.set_scale('linear', 'linear'))
        # self.linlin_button.grid(row=7, column=0, pady=5)
        # self.loglin_button = ttk.Checkbutton(self.button_frame, text="Log Y Scale", command=lambda: self.set_scale('log', 'linear'))
        # self.loglin_button.grid(row=7, column=1, pady=5)
        # self.loglog_button = ttk.Checkbutton(self.button_frame, text="Log-Log Scale", command=lambda: self.set_scale('log', 'log'))
        # self.loglog_button.grid(row=7, column=2, pady=5)

    def save_current_figure(self):
        file_path = fd.asksaveasfilename(defaultextension=".svg", filetypes=[("PNG files", "*.png"), ("SVG files", "*.svg")], title="Save Figure As")
        if file_path:
            self.figure.savefig(file_path, transparent=True)

    #need to be called when the scrollable frame is resized
    def onFrameConfigure(self, canvas):
        '''Reset the scroll region to encompass the inner frame'''
        canvas.configure(scrollregion=canvas.bbox("all"))

    #used to allow for scrolling with the mouse wheel when hovering over the canvas
    def _on_mousewheel(self, event, canvas):
        """Handle mousewheel events for different platforms."""
        system = platform.system()
        # Windows reports event.delta in multiples of 120
        try:
            if system == 'Windows':
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif system == 'Darwin':
                # macOS reports smaller delta values; use them directly
                canvas.yview_scroll(int(-1*event.delta), "units")
            else:
                # X11 (Linux) often uses Button-4/5 events instead of delta
                if hasattr(event, 'num') and event.num in (4,5):
                    if event.num == 4:
                        canvas.yview_scroll(-1, "units")
                    else:
                        canvas.yview_scroll(1, "units")
                else:
                    # fallback
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            # safe fallback if event attributes are unexpected
            pass

    #also allows for scrolling with the mouse wheel when hovering over the canvas
    def _bind_to_mousewheel(self, canvas):
        """Bind the appropriate mousewheel events to the given canvas."""
        system = platform.system()
        if system in ('Windows', 'Darwin'):
            # bind to all so the events are captured while the cursor is over the canvas
            canvas.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))
        else:
            # X11: bind both the wheel buttons and MouseWheel as a fallback
            canvas.bind_all("<Button-4>", lambda e: self._on_mousewheel(e, canvas))
            canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel(e, canvas))
            canvas.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))

    #allows you to not scroll all the time
    def _unbind_from_mousewheel(self, canvas):
        """Remove the mousewheel bindings added by _bind_to_mousewheel."""
        try:
            canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass
        try:
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    def create_plot(self):
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self.figure_frame)
        NavigationToolbar2Tk(self.figure_canvas,self.figure_frame).pack(side='top')
        self.figure_canvas.get_tk_widget().pack(side='top')

    def create_curve_frame(self):
        frame_id = len(self.curves)
        self.curve_frame = data_curve_frame( self.curves_scrollable, frame_id)
        self.curve_frame.grid(row=frame_id, column=1, sticky="ew", padx=5, pady=5)
        self.curves.append(self.curve_frame)

    def create_theoretical_curve_frame(self):
        frame_id = len(self.curves)
        self.theoretical_curve_frame = theoretical_curve_frame( self.curves_scrollable, frame_id)
        self.theoretical_curve_frame.grid(row=frame_id, column=1, sticky="ew", padx=5, pady=5)
        self.curves.append(self.theoretical_curve_frame)

    def update_plot(self):
        self.axes.clear()
        for curve in self.curves:
            if curve.show_plot_bool.get():
                curve.make_plot(self.axes)
        self.axes.set_title(self.fig_title.get())
        self.axes.set_xlabel(self.x_label.get())
        self.axes.set_ylabel(self.y_label.get())
        self.axes.set_xbound(self.x_range[0].get(), self.x_range[1].get())
        self.axes.set_ybound(self.y_range[0].get(), self.y_range[1].get())
        self.axes.legend()
        self.figure_canvas.draw()

class data_curve_frame(tk.LabelFrame):
    def __init__(self, parent, curve_id):
        super().__init__(parent, text=f"Curve {curve_id} Settings")
        self.curve_id = curve_id
        self.curve_name = tk.StringVar(value=f"Curve {curve_id}")
        self.color = tk.StringVar(value="XKCD:blue")
        self.source_file = tk.StringVar(value=None)
        self.sourcedb = None
        self.plot_fit_bool = tk.BooleanVar(value=False)
        self.show_plot_bool = tk.BooleanVar(value=True)
        self.curve_style = tk.StringVar(value="solid")#, options=["solid", "dotted", "dashed", "dashdot"]
        self.plot_args = {'left_knot':tk.DoubleVar(value=0.25),
                          'right_knot':tk.DoubleVar(value=0.25), 
                          'show_knots':tk.BooleanVar(value=False), 
                          'show_stoletow':tk.BooleanVar(value=False), 
                          'label_regions':tk.BooleanVar(value=False),
                          'mask_value':tk.DoubleVar(value=3.5)}
        self.create_widgets()

    def create_widgets(self):
        self.curve_name_entry = ttk.Entry(self, textvariable=self.curve_name)
        self.color_cbox = ttk.Combobox(self, textvariable=self.color, values=list(mcolors.XKCD_COLORS.keys()), state="readonly")
        source_button = ttk.Button(self, text="Select Data Source", command=self.open_source)
        source_display = ttk.Spinbox(self, textvariable=self.source_file,state='disabled')
        plot_fit_button = ttk.Checkbutton(self, text="Plot Fit", variable=self.plot_fit_bool)
        plot_show_button = ttk.Checkbutton(self, text="Show Plot", variable=self.show_plot_bool)
        self.left_knot_entry = ttk.Entry(self, textvariable=self.plot_args['left_knot'])
        self.right_knot_entry = ttk.Entry(self, textvariable=self.plot_args['right_knot'])
        self.show_knots_cb = ttk.Checkbutton(self, text="Show Knots", variable=self.plot_args['show_knots'])
        self.show_stoletow_cb = ttk.Checkbutton(self, text="Show Stoletow", variable=self.plot_args['show_stoletow'])
        self.label_regions_cb = ttk.Checkbutton(self, text="Label Regions", variable=self.plot_args['label_regions'])
        self.mask_value_label = ttk.Label(self, text="Mask Value:")
        self.mask_value_entry = ttk.Entry(self, textvariable=self.plot_args['mask_value'])


        widgets = {'Name:': self.curve_name_entry,
                    'Color:': self.color_cbox,
                    'Source File:': source_button,
                    '': source_display,
                    'Plot Fit:': plot_fit_button,
                    'Show Plot:': plot_show_button,
                    'Fit left knot:': self.left_knot_entry,
                    'Fit right knot:': self.right_knot_entry,
                    'Mask Value:': self.mask_value_entry,
                    'Show Knots:': self.show_knots_cb,
                    'Show Stoletow:': self.show_stoletow_cb,
                    'Label Regions:': self.label_regions_cb
                    }

        for i,(label,widget), in enumerate(widgets.items()):
            if isinstance(widget,ttk.Entry):
                ttk.Label(self, text=label).grid(row=i, column=0, padx=5, pady=5)
            widget.grid(row=i, column=1, padx=5, pady=5)

    def open_source(self):
        file_path = fd.askopenfilename(title="Select Data Source", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.source_file.set(file_path)
        self.sourcedb = pd.read_csv(file_path).sort_values(by='p_MKS(Torr)')

    def make_plot(self, ax):
        v, pd = plot_data(ax, self.sourcedb, self.curve_name.get(), color=self.color.get(), mask_value=self.plot_args['mask_value'].get())
        if self.plot_fit_bool.get():
            plot_fit(ax, pd, v, label=self.curve_name.get(), color=self.color.get(), left_knot_range=self.plot_args['left_knot'].get(), right_knot_range=self.plot_args['right_knot'].get(), show_knots=self.plot_args['show_knots'].get(), show_stoletow=self.plot_args['show_stoletow'].get(), label_regions=self.plot_args['label_regions'].get())


class theoretical_curve_frame(tk.LabelFrame):
    def __init__(self, parent, curve_id):
        super().__init__(parent, text=f"Theoretical Curve {curve_id} Settings")
        self.curve_id = curve_id
        self.curve_name = tk.StringVar(value=f"Theoretical Curve {curve_id}")
        self.color = tk.StringVar(value="XKCD:red")
        self.theory = {}
        self.show_plot_bool = tk.BooleanVar(value=True)
        self.args = {'A':tk.DoubleVar(value=15), 'B':tk.DoubleVar(value=365), 'gg':tk.DoubleVar(value=1e-1), 'a':tk.DoubleVar(value=0.8/2), 'd':tk.DoubleVar(value=1), 'p_min':tk.DoubleVar(value=0.001), 'p_max':tk.DoubleVar(value=10), 'p_step':tk.DoubleVar(value=0.001)}
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text=f"Name:").grid(row=0,column=0, padx=5, pady=5)
        self.curve_name_entry = ttk.Entry(self, textvariable=self.curve_name)
        self.curve_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Color:").grid(row=1,column=0, padx=5, pady=5)
        self.color_cbox = ttk.Combobox(self, textvariable=self.color, values=list(mcolors.XKCD_COLORS.keys()), state="readonly")
        self.color_cbox.grid(row=1, column=1, padx=5, pady=5)

        self.show_plot_button = ttk.Checkbutton(self, text="Show Plot", variable=self.show_plot_bool)
        self.show_plot_button.grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(self, text="Theory Type:").grid(row=2,column=0, padx=5, pady=5)
        self.theory_cbox = ttk.Combobox(self, values=["Townsend", "R24: Cylindrical", "R24: Spherical"], state="readonly")
        self.theory_cbox.grid(row=2, column=1, padx=5, pady=5)

        for i, (arg, var) in enumerate(self.args.items()):
            val = var.get()
            ttk.Label(self, text=f"{arg}:").grid(row=3+i,column=0, padx=5, pady=5)
            entry = ttk.Entry(self, textvariable=var)
            entry.grid(row=3+i, column=1, padx=5, pady=5)
            entry.bind("<FocusOut>", lambda e, a=arg, ent=entry: self.update_arg(a, ent.get()))

    def update_arg(self, arg, val):
        self.args[arg].set(float(val))

    def make_plot(self, ax):
        theory_type = self.theory_cbox.get()
        A = self.args['A'].get()
        B = self.args['B'].get()
        gg = self.args['gg'].get()
        a = self.args['a'].get()
        d = self.args['d'].get()
        p_range = (self.args['p_min'].get(), self.args['p_max'].get())
        p_step = self.args['p_step'].get()
        if theory_type == "Townsend":
            pd_theory, Vcr_theory = Townsend(A, B, gg, p_range, d, p_step)
        elif theory_type == "R24: Cylindrical":
            pd_theory, Vcr_theory = R24_Cylindrical(A, B, gg, p_range, a, d, p_step)
        elif theory_type == "R24: Spherical":
            pd_theory, Vcr_theory = R24_Spherical(A, B, gg, p_range, a, d, p_step)
        else:
            return

        ax.plot(pd_theory, Vcr_theory, label=self.curve_name.get(), color=self.color.get())

        


if __name__ == "__main__":
    app = PlotMaker()
    app.mainloop()
