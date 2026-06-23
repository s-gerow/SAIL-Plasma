import logging
import pyvisa

from threadcontroller import Controller
from equipment.oscilloscope import SiglentSDS1204XE
from equipment.nidaqequipment import NIDAQEquipment
from gui.main_window import MainWindow
from loggingconfig import init_logging

def main():
    init_logging(log_dir="logs", level="INFO")

    rm = pyvisa.ResourceManager()
    oscope = SiglentSDS1204XE(name='oscilloscope', manager=rm)
    nidaq = NIDAQEquipment()

    controller = Controller()
    controller.register(oscope.getName(), oscope)
    controller.register(nidaq.getName(), nidaq)

    app = MainWindow(controller)
    app.mainloop()

if __name__=="__main__":
    main()
