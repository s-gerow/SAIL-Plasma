import numpy as np
import pandas as pd
from tkinter import filedialog as fd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

plt.rcParams['text.usetex'] = False

def unpack_coeffs(coeffs):
    left = coeffs[:2]
    mid = coeffs[2:6]
    right = coeffs[6:]
    return left, mid, right

def find_peicewise(x_data, coeffs, left_knot, right_knot):
    c_left, c_mid, c_right = unpack_coeffs(coeffs)
    y_data = np.zeros_like(x_data)

    for i, x in enumerate(x_data):
        if x < left_knot:
            y_data[i] = np.polyval(c_left, x)
        elif left_knot <= x <= right_knot:
            y_data[i] = np.polyval(c_mid, x)
        elif x > right_knot:
            y_data[i] = np.polyval(c_right, x)
    
    return y_data

def fit_data(coeffs, x_data, y_data, left_knot, right_knot):
    y_fit = find_peicewise(x_data, coeffs, left_knot, right_knot)
    return np.sum((y_fit - y_data)**2)

def continuity_conditions(coeffs, left_knot, right_knot):
    c_left, c_mid, c_right = unpack_coeffs(coeffs)

    d_left = np.polyder(c_left)

    d_mid = np.polyder(c_mid)
    dd_mid = np.polyder(d_mid)

    d_right = np.polyder(c_right)

    #c0 continuity
    c0_left = np.polyval(c_left, left_knot) - np.polyval(c_mid, left_knot)
    c0_right = np.polyval(c_right, right_knot) - np.polyval(c_mid, right_knot)

    #c1 continuity
    c1_left = np.polyval(d_left, left_knot) - np.polyval(d_mid, left_knot)
    c1_right = np.polyval(d_right, right_knot) - np.polyval(d_mid, right_knot)

    #c2 continuity
    #c2_left = np.polyval(dd_mid, left_knot)
    #c2_right = np.polyval(dd_mid, right_knot)

    return [ c0_left, c0_right, c1_left, c1_right]#, c2_left, c2_right]

def concavity_conditions(coeffs, left_knot, right_knot):
    c_left, c_mid, c_right = unpack_coeffs(coeffs)

    d_mid = np.polyder(c_mid)
    dd_mid = np.polyder(d_mid)

    c_up_left = np.polyval(dd_mid, left_knot)
    c_up_right = np.polyval(dd_mid, right_knot)

    return [c_up_left, c_up_right]


def plot_data(ax, dataframe: pd.DataFrame, label = "Experimental Data", color = None, mask_value = 0):
    #Isolation of data
    p = dataframe.iloc[:,5].values
    d = dataframe.iloc[:,8].values
    v = dataframe.iloc[:,3].values
    p_d = np.array(p*d)

    #Grabbing Errorbars
    pd_err = dataframe.iloc[:,14].values
    v_err = dataframe.iloc[:,9].values

    #masking for <2 cm*torr
    def mask_less_than(arr, value):
        return np.ma.masked_where(p_d>value,arr)

    if mask_value > 0:
        v = mask_less_than(v, 3.5)
        pd_err = mask_less_than(pd_err, 3.5)
        v_err = mask_less_than(v_err, 3.5)
        p_d = mask_less_than(p_d, 3.5)

    
    ax.errorbar(p_d, v, yerr=v_err, xerr=pd_err, fmt='.', capsize=4, markerfacecolor = 'none', label = label, color = color)
    return v, p_d

def plot_fit(ax, x, y, left_knot_range = 0.25, right_knot_range = 0.25, label = "", show_knots = True, show_stoletow = True, color = None):
    p_d = x
    v = y
    #Piecewise Fit 
    min_index = np.argmin(v)
    pd_min = p_d[min_index]
    v_min = v[min_index]

    #Knots at +10% of min V
    uncertainty = 0.05
    #left
    #left_side = v[:min_index]
    #left_knot_index = (np.abs(left_side - v_min*(1+0.2))).argmin() #based on knowing v_min
    left_side = p_d[:min_index+1]
    left_knot_index = (np.abs(left_side - (pd_min-left_knot_range))).argmin() #based on knowing pd_min
    
    
    #right
    #right_side = v[min_index:]
    #right_knot_index = (np.abs(right_side - v_min*(1+0.05))).argmin() + min_index
    right_side = p_d[min_index:]
    right_knot_index = (np.abs(right_side - (pd_min+right_knot_range))).argmin() + min_index

    if show_knots:
        ax.axvline(x=p_d[left_knot_index], color = 'grey', linestyle = '--', label = 'Left Min Knot')
        ax.axvline(x=p_d[right_knot_index], color = 'grey', linestyle = '-.', label = 'Right Min Knot')

    #piecewise functions
    left_v = v[:left_knot_index+1]
    middle_v = v[left_knot_index:right_knot_index+1]
    right_v = v[right_knot_index:]
    left_pd = p_d[:left_knot_index+1]
    middle_pd = p_d[left_knot_index:right_knot_index+1]
    right_pd = p_d[right_knot_index:]

    poly_left = np.polyfit(left_pd, left_v, 1)
    poly_mid = np.polyfit(middle_pd, middle_v, 3)
    poly_right = np.polyfit(right_pd, right_v, 1)

    initial_guess = np.concatenate([poly_left, poly_mid, poly_right])



    contraints = [
        {
            'type': 'eq',
            'fun': lambda coeffs: continuity_conditions(coeffs, p_d[left_knot_index], p_d[right_knot_index])
        },
        {
            'type': 'ineq',
            'fun': lambda coeffs: concavity_conditions(coeffs, p_d[left_knot_index], p_d[right_knot_index])
        }
    ]

    result = minimize(fit_data, initial_guess, args = (p_d, v, p_d[left_knot_index], p_d[right_knot_index]), constraints=contraints, method='SLSQP')



    fitted_coeffs = result.x
    x_fit = np.linspace(p_d.min(), p_d.max(), 500)
    y_fit = find_peicewise(x_fit, fitted_coeffs, p_d[left_knot_index], p_d[right_knot_index])
    ax.plot(x_fit, y_fit, color = color, label = f"{label} Fitted Piecewise Model")

    stoletow_point_index = y_fit.argmin()
    if show_stoletow:
        ax.scatter(x_fit[stoletow_point_index], y_fit[stoletow_point_index], marker = '*',s = 200, ec = 'black', color = 'yellow', label = f"{label} Stoletow Point")
    return fitted_coeffs

#initilize Graph
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)

#Most recent lab data
lab_data_5mm = pd.read_csv('C:/Users/gerows/Python/SAIL-Plasma/202565_N2_5mm.csv')
lab_data_10mm = pd.read_csv('C:/Users/gerows/Python/SAIL-Plasma/2025612_N2_10mm.csv')
lab_data_old = pd.read_csv('C:/Users/gerows/Python/SAIL-Plasma/NelsonData.csv')
lab_data_2_5mm = pd.read_csv('C:/USers/gerows/Python/SAIL-Plasma/202572_N2_2_5.csv')
lab_data_2_5mm = lab_data_2_5mm.sort_values(by='p_MKS(Torr)')
lab_data_5mm = lab_data_5mm.sort_values(by='p_MKS(Torr)')
lab_data_10mm = lab_data_10mm.sort_values(by='p_MKS(Torr)')
nelson = lab_data_old.sort_values(by='Pressure (Torr)')

v, p_d = plot_data(ax, lab_data_5mm, label = "5 mm Gap", color = 'xkcd:black')
v_2_5, p_d_2_5 = plot_data(ax, lab_data_2_5mm, label = "2.5mm Gap", color = 'xkcd:blue')
v_10, p_d_10 = plot_data(ax, lab_data_10mm, label = "10mm Gap", mask_value=3.5, color='xkcd:red')


#coeffs_5mm = plot_fit(ax, p_d, v, label = '5 mm', show_knots=False, show_stoletow=False, color='xkcd:black')
#coeffs_10mm = plot_fit(ax, p_d_10, v_10, left_knot_range=0.3, right_knot_range=0.3, label = '10mm', show_knots=False, show_stoletow=False, color='xkcd:red')
coeffs_2_5mm = plot_fit(ax, p_d_2_5, v_2_5, label = '2.5 mm',show_knots=False, show_stoletow=False, color='xkcd:blue')

#nelson data

#Isolation of data
nelsonp = nelson.iloc[:,5].values
nelsond = nelson.iloc[:,7].values
nelsonv = nelson.iloc[:,3].values
nelsonp_d = np.array(nelsonp*nelsond)

#Grabbing Errorbars
nelsonpd_err = nelson.iloc[:,11].values
nelsonv_err = nelson.iloc[:,8].values

#ax.errorbar(nelsonp_d, nelsonv, yerr=nelsonv_err, xerr=nelsonpd_err, fmt='.', capsize=4, markerfacecolor = 'none', label = "N24", color = 'xkcd:red')

#####

#Theoretical Curve
A = 15
B = 365
gg_low = 10**-2
gg_high = 10**-1
p_d_theory_low = np.linspace(0.31, 6, 1000)
p_d_theory_high = np.linspace(0.2, 6, 1000)
Vcr_parallel_low = (B*p_d_theory_low)/np.log((A*p_d_theory_low)/np.log(1+(1/gg_low)))
Vcr_parallel_high = (B*p_d_theory_high)/np.log((A*p_d_theory_high)/np.log(1+(1/gg_high)))
#ax.fill_between(p_d_theory_high, Vcr_parallel_low, Vcr_parallel_high, label = 'SE32 Literature', alpha=0.2)
#ax.annotate(f'A = {A}, B = {B} gg [{gg_low},{gg_high}]',xy=(4.5,600), xytext=(4.5, 600))


#Theoretical curve with calculated A and B
A_ion = 7.68 #from Nelson 2024
B_ion = 366.69 #from Nelson 2024
p_d_theory_low = np.linspace(0.61, 6, 1000)
p_d_theory_high = np.linspace(0.32, 6, 1000)
Vcr_parallel_low_i = (B_ion*p_d_theory_low)/np.log((A_ion*p_d_theory_low)/np.log(1+(1/gg_low)))
Vcr_parallel_high_i = (B_ion*p_d_theory_high)/np.log((A_ion*p_d_theory_high)/np.log(1+(1/gg_high)))
#ax.fill_between(p_d_theory_high, Vcr_parallel_low_i, Vcr_parallel_high_i, label = 'SE32 Ionization', alpha=0.2)
#ax.annotate(f'A = {A_ion}, B = {B_ion} gg [{gg_low},{gg_high}]',xy=(3.5,730), xytext=(3.5, 730))

p_d_riousset = np.concatenate([np.arange(0.7,2,0.1),np.arange(2,12.5,0.5)])*0.5
Vcr_spherical_lower = np.array([434.256,
                            240.72,
                            184.816,
                            159.144,
                            144.952,
                            136.328,
                            130.808,
                            127.2,
                            124.832,
                            123.32,
                            122.424,
                            121.984,
                            121.88,
                            122.04,
                            125.208,
                            130.328,
                            136.24,
                            142.496,
                            148.888,
                            155.32,
                            161.736,
                            168.12,
                            174.448,
                            180.72,
                            186.928,
                            193.064,
                            199.144,
                            205.16,
                            211.112,
                            217,
                            222.84,
                            228.624,
                            234.352,
                            240.032
                            ])
Vcr_spherical_gg_upper = np.array([66.9804000000000,
                                   64.5027000000000,
                                   63.5136000000000,
                                   63.3347000000000,
                                   63.6388000000000,
                                   64.2491000000000,
                                   65.0624000000000,
                                   66.0148000000000,
                                   67.0649000000000,
                                   68.1847000000000,
                                   69.3548000000000,
                                   70.5614000000000,
                                   71.7945000000000,
                                   73.0467000000000,
                                   79.4403000000000,
                                   85.8560000000000,
                                   92.1840000000000,
                                   98.3920000000000,
                                   104.480000000000,
                                   110.448000000000,
                                   116.296000000000,
                                   122.048000000000,
                                   127.696000000000,
                                   133.264000000000,
                                   138.744000000000,
                                   144.144000000000,
                                   149.480000000000,
                                   154.744000000000,
                                   159.944000000000,
                                   165.088000000000,
                                   170.176000000000,
                                   175.216000000000,
                                   180.208000000000,
                                   185.144000000000])
#ax.fill_between(p_d_riousset, Vcr_spherical_lower, Vcr_spherical_gg_upper, label = 'R24', alpha = 0.2, color = 'xkcd:green')

#Graph Appearence
ax.set_title("Air Breakdown with 0.8cm Steel Electrode", fontsize = 18)
ax.set_ylim([50, 750])
ax.set_xlabel(r'$pd[cm*Torr]$', fontsize = 18)
ax.set_ylabel(r'$V_{cr}[V]$', fontsize = 18)
ax.minorticks_on()
ax.tick_params(axis='both', which = 'major', labelsize=16)
ax.legend(loc="lower right", frameon=False)
plt.show()