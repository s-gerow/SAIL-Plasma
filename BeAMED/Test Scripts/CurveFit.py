import numpy as np
import pandas as pd
from tkinter import filedialog as fd
import matplotlib.pyplot as plt

#initilize Graph
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)

#Most recent lab data
lab_data_new = pd.read_csv('C:/Users/gerows/Python/SAIL-Plasma/202565_N2_5mm.csv')
lab_data_new = lab_data_new.sort_values(by='p_MKS(Torr)')
#Isolation of data
p = lab_data_new.iloc[:,5].values
d = lab_data_new.iloc[:,8].values
v = lab_data_new.iloc[:,3].values
p_d = np.array(p*d)

#Grabbing Errorbars
p_err = lab_data_new.iloc[:,10].values
pd_err = lab_data_new.iloc[:,14].values
v_err = lab_data_new.iloc[:,9].values
ax.errorbar(p_d, v, yerr=v_err, xerr=pd_err, fmt='b.', capsize=4, label = "Experimental Data")

#Theoretical Curve
A = 15
B = 365
gg = 10**-2
p_d_theory = np.linspace(0.31, 6, 1000)
Vcr_parallel = (B*p_d_theory)/np.log((A*p_d_theory)/np.log(1+(1/gg)))
ax.plot(p_d_theory, Vcr_parallel, label = 'Theoretical Curve')

#Piecewise Fit 
min_index = np.argmin(v)
pd_min = p_d[min_index]
v_min = v[min_index]

#Knots at +10% of min V
#left
left_side = v[:min_index+1]
left_knot_index = (np.abs(left_side - v_min*1.1)).argmin()
ax.axvline(x=p_d[left_knot_index], color = 'b', linestyle = '--', label = 'Left Min Knot')
#right
right_side = v[min_index:]
right_knot_index = (np.abs(right_side - v_min*1.1)).argmin() + min_index
ax.axvline(x=p_d[right_knot_index], color = 'b', linestyle = '-.', label = 'Right Min Knot')

#piecewise functions
left_v = v[:left_knot_index+1]
middle_v = v[left_knot_index:right_knot_index+1]
right_v = v[right_knot_index:]
left_pd = p_d[:left_knot_index+1]
middle_pd = p_d[left_knot_index:right_knot_index+1]
right_pd = p_d[right_knot_index:]

poly_left = np.polyfit(left_pd, left_v, 1)
poly_mid = np.polyfit(middle_pd, middle_v, 2)
poly_right = np.polyfit(right_pd, right_v, 1)

f_left = lambda pd_: np.polyval(poly_left, pd_)
f_mid = lambda pd_: np.polyval(poly_mid, pd_)
f_right = lambda pd_: np.polyval(poly_right, pd_)

v_fit = np.zeros(np.size(p_d))
v_fit[p_d <= p_d[left_knot_index]] = f_left(p_d[p_d <= p_d[left_knot_index]])
v_fit[(p_d >= p_d[left_knot_index]) & (p_d <= p_d[right_knot_index])] = f_mid(p_d[(p_d >= p_d[left_knot_index]) & (p_d <= p_d[right_knot_index])])
v_fit[p_d >= p_d[right_knot_index]] = f_right(p_d[p_d >= p_d[right_knot_index]])
ax.plot(p_d, v_fit, linestyle = '-', color = 'r', label = 'Piecewise Fit')
#Graph Appearence
ax.set_title("N2 5mm Paschen Breakdown")
ax.set_ylim([200, 800])
ax.set_xlabel(r'$pd[cm*Torr]$')
ax.set_ylabel(r'$V_{cr}[V]$')
ax.minorticks_on()
ax.legend(loc="upper right", frameon=False)
plt.show()