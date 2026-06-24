import logging
import pyvisa

from threadcontroller import Controller
from equipment.oscilloscope import SiglentSDS1204XE
from equipment.nidaqequipment import NIDAQEquipment
from equipment.multimeter import KeithleyDMM6500
from equipment.powersupply import Keithley2260B_800_1
from gui.main_window import BeAMEDWindow
from loggingconfig import init_logging

def main():
    init_logging(log_dir="logs", level="INFO")

    rm = pyvisa.ResourceManager()
    oscope = SiglentSDS1204XE(rm)
    nidaq = NIDAQEquipment()
    dmm = KeithleyDMM6500(rm)
    pwr = Keithley2260B_800_1(rm)

    controller = Controller()
    controller.register(oscope.getName(), oscope)
    controller.register(nidaq.getName(), nidaq)
    controller.register(dmm.getName(), dmm)
    controller.register(pwr.getName(), pwr)

    app = BeAMEDWindow(controller)
    app.mainloop()

if __name__=="__main__":
    main()
