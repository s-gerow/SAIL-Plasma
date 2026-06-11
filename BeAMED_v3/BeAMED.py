import logging
import pyvisa

from threadcontroller import Controller
from equipment.oscilloscope import SiglentSDS1204XE
from gui.main_window import MainWindow
from loggingconfig import init_logging

def main():
    init_logging(log_dir="logs", level="INFO")

    rm = pyvisa.ResourceManager()
    oscope = SiglentSDS1204XE(name='Oscilloscope', manager=rm)

    controller = Controller()
    controller.register("Oscilloscope", oscope)

    app = MainWindow(controller)
    app.mainloop()

if __name__=="__main__":
    main()
