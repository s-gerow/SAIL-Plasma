import BeAMED.Equipment.Experiment as Experiment
from BeAMED.Equipment.Experiment import *

if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = Experiment.experimentWindow()
    chamber.add_equipment(keithleyDMM6500(chamber))
    chamber.mainloop()


