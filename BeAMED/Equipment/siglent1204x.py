from Experiment import *
from Devices import *

if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = experimentWindow()
    chamber.add_equipment(siglentSDS1204X_E(chamber, chamber.rm, auto_import_configurations=False))
    chamber.mainloop()