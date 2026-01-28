import ExperimentWindow
from ExperimentWindow import *

if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = ExperimentWindow.experimentWindow()
    chamber.add_equipment(keithleyDMM6500(chamber))
    chamber.mainloop()


