import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)
#t_trigger = 1749748821.804677 #0
t_trigger = 1750099801.6371176
dmmseries = pd.read_csv('C:/Users/gerows/Python/SAIL-Plasma/dmm_timeseries.csv')
time = np.array(dmmseries.iloc[:,0].values)
voltage = np.array(dmmseries.iloc[:,1].values)
t_trigger = t_trigger-time[0]
time = time-time[0]

plt.plot(time, voltage, label='Data')
plt.axvline(t_trigger, color='gray', linestyle='--', label='Discharge')
plt.legend()
plt.title("DMM Timeseries for Breakdown at 0.705 cm*Torr")
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.grid(True)
plt.tight_layout()
plt.show()