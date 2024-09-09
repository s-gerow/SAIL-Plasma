import pyvisa

#Initialize resrouce manager
rm = pyvisa.ResourceManager()
'''
Query Commands
print(DMM.query(":READ?"))
print(DMM.query(":FUNC?"))
print(DMM.query(":VOLT:RANG?"))
print(DMM.query(":VOLT:NPLC?"))
print(DMM.query('TRAC:FILL:MODE? "defbuffer1"'))
'''
#Initilize DMM and connect
DMM_name = 'USB0::0x05E6::0x6500::04386498::0::INSTR'
DMM = rm.open_resource(DMM_name)
print(DMM.query("*IDN?"))

#The following lines mirror the configuration in Labview
DMM.write("RST")
DMM.write(':SENS:FUNC "VOLT:DC"')
DMM.write("SENS:VOLT:RANG:AUTO ON")
#DMM.write(':SENS:VOLT:NPLC 1') #Default 1
#DMM.write(':SENS:VOLT:LINE:SYNC OFF') #Default OFF
#DMM.write("SENS:VOLT:AZER ON")#Default ON
DMM.write('CALC:VOLT:LIM1:STAT OFF') #Default OFF
DMM.write('CACL:VOLT:LIM1:CLE:AUTO OFF') #Limit Number in GUI is 1 (LIM_), Default ON
DMM.write('CALC:VOLT:LIM1:LOW 0') #Because the voltage limit is disabled this should not be needed but may as well include it because maybe one day we do
DMM.write('CALC:VOLT:LIM1:UPP 0')
DMM.write('TRAC:FILL:MODE "defbuffer1"') #continuous fill
DMM.write('TRAC:POIN "defbuffer1"') #Buffer Size 10

print(DMM.query(':READ?'))

DMM.close()