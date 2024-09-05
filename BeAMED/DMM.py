import pyvisa

rm = pyvisa.ResourceManager()
aliases = []

'''
for i in rm.list_resources():
    aliases.append(rm.list_resources_info()[i][4])

print(aliases)
def get_resource(alias):
    for i in rm.list_resources_info().values():
        if alias in i:
            return i[3]
        
for i in aliases:
    print(i, get_resource(i))
'''

DMM_name = 'USB0::0x05E6::0x6500::04386498::0::INSTR'
DMM = rm.open_resource(DMM_name)
DMM.write("RST")
print(DMM.query("*IDN?"))
DMM.write(':SENS:FUNC "VOLT:DC"')
print(DMM.query(":READ?"))
print(DMM.query(":FUNC?"))
DMM.write("SENS:VOLT:RANG 10")
print(DMM.query(":VOLT:RANG?"))
DMM.write("SENS:VOLT:RANG:AUTO ON")
print(DMM.query(":VOLT:RANG?"))

DMM.close()