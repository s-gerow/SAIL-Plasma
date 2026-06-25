import tkinter as tk
from tkinter import ttk

# ── colours ───────────────────────────────────────────────────────────────────

# BG          = "#1e1e1e"
# BG_SURFACE  = "#252526"
# BG_INPUT    = "#3c3c3c"
# FG_PRIMARY  = "#d4d4d4"
# FG_MUTED    = "#888888"
# FG_ACCENT   = "#569cd6"
# BORDER      = "#444444"

# indicator colours
IND_ON      = "lime"
IND_OFF     = "coldgrey"
IND_WARN    = "orange1"
IND_ERROR   = "red2"

# ── indicator button ──────────────────────────────────────────────────────────

class IndicatorButton(tk.Checkbutton):
    """
    A coloured square indicator that can also act as a button.
    State is toggled via set(bool).

    Usage:
        ind = IndicatorButton(parent, size="small", text="Connected")
        ind.pack()
        ind.set(True)    # lights up
        ind.set(False)   # dims
    """

    SIZES = {
        "small": 15,
        "large": 50,
    }

    def __init__(self, parent, size: str = "small", text: str = "",
                 variable:str | None = None, on_color: str = IND_ON, off_color: str = IND_OFF,
                 **kwargs):
        px = self.SIZES.get(size, 15)

        self._on_image  = tk.PhotoImage(width=px, height=px)
        self._off_image = tk.PhotoImage(width=px, height=px)
        self._on_image.put(on_color,  to=(0, 0, px-1, px-1))
        self._off_image.put(off_color, to=(0, 0, px-1, px-1))

        self._state = False

        super().__init__(
            parent,
            image=self._off_image,
            selectimage=self._on_image,
            text=text,
            compound="left",       # image left of text
            variable=variable,
            # bg=BG_SURFACE,
            # fg=FG_MUTED,
            # activebackground=BG_SURFACE,
            indicatoron=False,
            relief="flat",
            borderwidth=0,
            font=("Courier New", 9),
            **kwargs,
            state="disabled"
        )

    def set(self, state: bool):
        self._state = state
        self.config(
            image=self._on_image if state else self._off_image,
            #fg=FG_PRIMARY if state else FG_MUTED,
        )

    def set_color(self, color: str):
        """Override the ON colour — useful for warning/error states."""
        px = self._on_image.width()
        self._on_image.put(color, to=(0, 0, px-1, px-1))
        if self._state:
            self.config(image=self._on_image)

    @property
    def state(self) -> bool:
        return self._state


# ── header label ──────────────────────────────────────────────────────────────

class HeaderLabel(tk.Label):
    """
    Bold, larger text for frame section headings.

    Usage:
        HeaderLabel(parent, text="Oscilloscope").pack()
    """
    def __init__(self, parent, text: str = "", **kwargs):
        super().__init__(
            parent,
            text=text,
            # bg=BG_SURFACE,
            # fg=FG_PRIMARY,
            font=("TkDefaultFont", 12, "bold"),
            anchor="w",
            **kwargs,
        )


# ── value label ───────────────────────────────────────────────────────────────

class ValueLabel(tk.Label):
    """
    Displays a live value with a recessed outlined background.
    Accepts a tk.StringVar or tk.DoubleVar via textvariable.

    Usage:
        var = tk.StringVar(value="---")
        ValueLabel(parent, textvariable=var, unit="V").pack()
        var.set("3.141")
    """
    def __init__(self, parent, textvariable:tk.Variable|None=None, unit: str = "", **kwargs):
        # if a unit is supplied wrap the frame so unit sits outside the box
        self._unit = unit
        super().__init__(
            parent,
            textvariable=textvariable,
            # bg=BG_INPUT,
            # fg=FG_ACCENT,
            font=("TkDefaultFont", 10),
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=2,
            anchor="e",
            width=10,
            **kwargs,
        )


class ValueDisplay(tk.Frame):
    """
    A labelled ValueLabel with an optional unit tag.
    Combines a HeaderLabel-style name, a ValueLabel, and a unit string.

    Usage:
        vd = ValueDisplay(parent, label="Voltage", unit="V")
        vd.pack()
        vd.set("12.34")
        # or bind a variable:
        vd = ValueDisplay(parent, label="Voltage", unit="V", textvariable=my_var)
    """
    def __init__(self, parent, label: str = "", unit: str = "",
                 textvariable=None, **kwargs):
        super().__init__(parent, **kwargs)

        if textvariable is None:
            self._var = tk.StringVar(value="---")
        else:
            self._var = textvariable

        tk.Label(
            self,
            text=label,
            # bg=BG_SURFACE,
            # fg=FG_MUTED,
            font=("TkDefaultFont", 9),
            anchor="w",
            width=12,
        ).pack(side="left")

        ValueLabel(
            self,
            textvariable=self._var,
        ).pack(side="left", padx=2)

        if unit:
            tk.Label(
                self,
                text=unit,
                # bg=BG_SURFACE,
                # fg=FG_MUTED,
                font=("TkDefaultFont", 9),
            ).pack(side="left", padx=(2, 0))

    def set(self, value):
        self._var.set(str(value))

    def get(self):
        return self._var.get()