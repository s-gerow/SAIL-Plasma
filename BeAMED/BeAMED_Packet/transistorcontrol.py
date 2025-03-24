from ChamberGUIBuilder import *

class Experiment():
    def __init__(self, parent: ChamberApp):
        self.parent = parent
        self.rm = parent.rm #this is a the resource manager. Used to

        self.DAQ_Frame = tk.Frame(self.parent.experimentFrame, width=550, height = 450, relief='sunken')
        self.DAQ_Frame.pack(fill=None, side='left',expand=False)

        self.LED_ON = tk.PhotoImage(width=13, height=13)
        self.LED_OFF = tk.PhotoImage(width=13, height=13)
        self.LED_ON.put(("lime"), to=(0,0,12,12))
        self.LED_OFF.put(("red"), to=(0,0,12,12))
        self.DAQ_PIN = tk.PhotoImage(file='./BeAMED/DAQ_Pinout.PNG')

        self.daq_line_labels = ['/0', '/ai0', '/ai4', '/0', '/ai1', '/ai5', '/0', '/ai2', '/ai6', '/0', '/ai3', '/ai7', '/0', '/ao0', '/ao1', '/0',
                           '/port0/line0', '/port0/line1', '/port0/line2', '/port0/line3', '/port0/line4', '/port0/line5', '/port0/line6', '/port0/line7',
                           '/port1/line0', '/port1/line1', '/port1/line2', '/port1/line3', '/port2/line0', '/0', '/0', '/0']
        analog_output_row = 0
        digital_output_row = 447
        analog_enable_row = 20
        digital_enable_row = 427
        label_row = 40
        label = ttk.Label(self.DAQ_Frame, image = self.DAQ_PIN)
        label.place(x=label_row,y=0)

        self.output_bool_vars = [tk.BooleanVar() for _ in range(32)]
        self.output_buttons = [tk.Checkbutton(self.DAQ_Frame, 
                        image = self.LED_OFF, 
                        selectimage = self.LED_ON, 
                        indicatoron = False, 
                        onvalue = True, 
                        offvalue = False, 
                        variable = self.output_bool_vars[i],
                        state = "disabled" if self.daq_line_labels[i]=='/0' else "normal",
                        command = lambda j=i: pin_output(j),
                        borderwidth=0) for i in range(32)]
        self.enable_var = [tk.IntVar() for _ in range(32)]
        self.enable_checkboxes = [tk.Checkbutton(self.DAQ_Frame,
                                                  variable = self.enable_var[i],
                                                  onvalue = 1,
                                                  offvalue = 0,
                                                  highlightthickness=0,
                                                  bd=0,
                                                  state = "disabled" if self.daq_line_labels[i]=='/0' else "normal",
                                                  command = lambda j=i: pin_enable(j),
                                                  ) for i in range(32)]
        start_y = 99
        for i in range(16):
            self.output_buttons[i].place(x=analog_output_row,y=start_y)
            self.output_buttons[i+16].place(x=digital_output_row, y=start_y)
            self.enable_checkboxes[i].place(x=analog_enable_row,y=start_y-1)
            self.enable_checkboxes[i+16].place(x=digital_enable_row,y=start_y-1)
            start_y += 16
        
        def pin_output(i):
            if self.enable_var[i].get() == False:
                print(f"ERROR: output for {self.daq_line_labels[i]} not enabled.")
                self.output_bool_vars[i].set(0)
            else:
                if self.output_bool_vars[i].get() == 1:
                    print(f"{self.daq_line_labels[i]} output started")
                elif self.output_bool_vars[i].get() ==0:
                    print(f"{self.daq_line_labels[i]} output stopped")
        
        def pin_enable(i):
            if self.enable_var[i].get() == False:
                self.output_bool_vars[i].set(0)
                print(f"{self.daq_line_labels[i]} disabled")
            elif self.enable_var[i].get() == True:
                print(f"{self.daq_line_labels[i]} enabled")
        

if __name__ == "__main__":
    #Automatically creates chamebr app and imports experiment
    #For this to work you will need to write in the file location of the current file as well as the file location of the configuration files
    chamber = ChamberApp()

    chamber.menubar.load_experiment("./BeAMED/BeAMED_Packet/transistorcontrol.py")
    
    for config in ["Power_TL.config"]:
        file = "./BeAMED/BeAMED_Packet/" + config
        chamber.generate_configuration_frame(filepath = file)

    chamber.mainloop()