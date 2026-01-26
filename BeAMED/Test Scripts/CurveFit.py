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

def plot_fit(ax, x, y, left_knot_range = 0.25, right_knot_range = 0.25, label = "", show_knots = True, show_stoletow = True, label_regions = True, color = None):
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
    if label_regions:
        ax.text((p_d[left_knot_index])/2, 75, '(I)', fontsize=12, color='grey', ha='center')
        ax.text((p_d[right_knot_index]+p_d[left_knot_index])/2, 75, '(II)', fontsize=12, color='grey', ha='center')
        ax.text((p_d[right_knot_index]+(p_d[right_knot_index]+p_d[left_knot_index])/4), 75, '(III)', fontsize=12, color='grey', ha='center')
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
    #print(f"stoletow: ({x_fit[stoletow_point_index]}pd,{y_fit[stoletow_point_index]}V)\n")
    if show_stoletow:
        ax.scatter(x_fit[stoletow_point_index], y_fit[stoletow_point_index], marker = '+',s = 400, ec = 'black', color = 'black', label = f"{label} Stoletow Point", zorder=7)
    return fitted_coeffs

#initilize Graph
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)

#Most recent lab data
lab_data_5mm = pd.read_csv('./202565_N2_5mm.csv')
lab_data_10mm = pd.read_csv('./2025612_N2_10mm.csv')
lab_data_old = pd.read_csv('./NelsonData.csv')
lab_data_2_5mm = pd.read_csv('./202572_N2_2_5.csv')
nelsonAr_data = pd.read_csv('./Nelson2024Argon.csv')
lab_data_2_5mm = lab_data_2_5mm.sort_values(by='p_MKS(Torr)')
lab_data_5mm = lab_data_5mm.sort_values(by='p_MKS(Torr)')
lab_data_10mm = lab_data_10mm.sort_values(by='p_MKS(Torr)')
nelson = lab_data_old.sort_values(by='Pressure (Torr)')
nelsonAr = nelsonAr_data.sort_values(by='Pressure (Torr)')

#argon lab data
argon_data_5mm = pd.read_csv('./2025115_Ar_5mm.csv')
argon_data_5mm = argon_data_5mm.sort_values(by='p_MKS(Torr)')
argon_data_10mm = pd.read_csv('./2025115_Ar_10mm.csv')
argon_data_10mm = argon_data_10mm.sort_values(by='p_MKS(Torr)')

#Ar
#v_ar_5, pd_ar_5 = plot_data(ax, argon_data_5mm, label = "5mm Gap Ar", color = 'xkcd:red')
v_ar_10, pd_ar_10 = plot_data(ax, argon_data_10mm, label = "10mm Gap Ar", color = 'xkcd:red')

#coeffs_5mm_ar = plot_fit(ax, pd_ar_5, v_ar_5, label = '5mm Ar', show_knots=False, show_stoletow=False, label_regions=False,color='xkcd:red')

#N2
#v, p_d = plot_data(ax, lab_data_5mm, label = "5 mm Gap N2", color = 'xkcd:black')
#v_2_5, p_d_2_5 = plot_data(ax, lab_data_2_5mm, label = "2.5mm Gap", color = 'xkcd:blue')
#v_10, p_d_10 = plot_data(ax, lab_data_10mm, label = "10mm Gap", mask_value=3.5, color='xkcd:black')


#coeffs_5mm = plot_fit(ax, p_d, v, label = '5 mm', show_knots=False, show_stoletow=False, label_regions=False, color='xkcd:black')

#coeffs_10mm = plot_fit(ax, p_d_10, v_10, left_knot_range=0.3, right_knot_range=0.3, label = '10mm', show_knots=False, label_regions = False, show_stoletow=False, color='xkcd:red')

#coeffs_2_5mm = plot_fit(ax, p_d_2_5, v_2_5, label = '2.5 mm',show_knots=False, show_stoletow=True, label_regions=False, color='xkcd:blue')

#nelson data

#Isolation of data

nelsonp = nelson.iloc[:,5].values
nelsond = nelson.iloc[:,7].values
nelsonv = nelson.iloc[:,3].values
nelsonp_d = np.array(nelsonp*nelsond)

nelsonpar = nelsonAr.iloc[:,7].values
nelsondar = nelsonAr.iloc[:,9].values
nelsonvar = nelsonAr.iloc[:,3].values
nelsonp_dar = np.array(nelsonpar*nelsondar)

#Grabbing Errorbars
nelsonpd_err = nelson.iloc[:,11].values
nelsonv_err = nelson.iloc[:,8].values

nelsonpdar_err = nelsonAr.iloc[:,13].values
nelsonvar_err = nelsonAr.iloc[:,10].values

#ax.errorbar(nelsonp_d, nelsonv, yerr=nelsonv_err, xerr=nelsonpd_err, fmt='.', capsize=4, markerfacecolor = 'none', label = "N24", color = 'xkcd:red')
#ax.errorbar(nelsonp_dar, nelsonvar, yerr=nelsonvar_err, xerr=nelsonpdar_err, fmt='.', capsize=4, markerfacecolor = 'none', label = "N24 Ar", color = 'xkcd:blue')
#####

#Theoretical Curve
#A = 15
#B = 365
A=6.1522
B = 485.5867
gg_low = 10**-2
gg_high = 10**-1
p_d_theory_low = np.linspace(0.31, 6, 1000)
p_d_theory_high = np.linspace(0.2, 6, 1000)
Vcr_parallel_low = (B*p_d_theory_low)/np.log((A*p_d_theory_low)/np.log(1+(1/gg_low)))
Vcr_parallel_high = (B*p_d_theory_high)/np.log((A*p_d_theory_high)/np.log(1+(1/gg_high)))
#ax.fill_between(p_d_theory_high, Vcr_parallel_low, Vcr_parallel_high, label = 'SE32', alpha=0.2, color = 'xkcd:grey')
#ax.annotate(f'A = {A}, B = {B} gg [{gg_low},{gg_high}]',xy=(4.5,600), xytext=(4.5, 600))

#Testing Riousset new numbers
A_new = 6.1522
B5 = 658
B25 = 634
B10 = 649
gg5 = 0.0677
gg25 = 0.0848
gg10 = 0.0247
p_d_low = np.linspace(0.2,6,1000)
Vcr10 = (B10*p_d_low)/np.log((A_new*p_d_low)/np.log(1+(1/gg10)))
Vcr5 = (B5*p_d_low)/np.log((A_new*p_d_low)/np.log(1+(1/gg5)))
Vcr25 = (B25*p_d_low)/np.log((A_new*p_d_low)/np.log(1+(1/gg25)))
#ax.plot(p_d_low, Vcr10,label=f"A={A_new}, B={B10},gg={gg10}")

#Theoretical curve with calculated A and B
A_ion = 6.1522 #from Nelson 2024
B_ion =  0.0677 #from Nelson 2024
p_d_theory_low = np.linspace(0.61, 6, 1000)
p_d_theory_high = np.linspace(0.32, 6, 1000)
Vcr_parallel_low_i = (B_ion*p_d_theory_low)/np.log((A_ion*p_d_theory_low)/np.log(1+(1/gg_low)))
Vcr_parallel_high_i = (B_ion*p_d_theory_high)/np.log((A_ion*p_d_theory_high)/np.log(1+(1/gg_high)))
#ax.fill_between(p_d_theory_high, Vcr_parallel_low_i, Vcr_parallel_high_i, label = 'SE32 Ionization', alpha=0.2, color = 'xkcd:red')
#ax.annotate(f'A = {A_ion}, B = {B_ion} gg [{gg_low},{gg_high}]',xy=(3.5,730), xytext=(3.5, 730))


#Riousset Data
#Riousset Spherical literature A,B
p_d_riousset = np.concatenate([np.arange(0.7,2,0.1),np.arange(2,12.5,0.5)])*0.5
Vcr_spherical_lower = np.array([434.256,240.72,184.816,159.144,144.952,136.328,130.808,127.2,124.832,123.32,122.424,121.984,121.88,122.04,125.208,130.328,136.24,142.496,148.888,155.32,161.736,168.12,174.448,180.72,186.928,193.064,199.144,205.16,211.112,217,222.84,228.624,234.352,240.032])
Vcr_spherical_gg_upper = np.array([66.9804000000000,64.5027000000000,63.5136000000000,63.3347000000000,63.6388000000000,64.2491000000000,65.0624000000000,66.0148000000000,67.0649000000000,68.1847000000000,69.3548000000000,70.5614000000000,71.7945000000000,73.0467000000000,79.4403000000000,85.8560000000000,92.1840000000000,98.3920000000000,104.480000000000,110.448000000000,116.296000000000,122.048000000000,127.696000000000,133.264000000000,138.744000000000,144.144000000000,149.480000000000,154.744000000000,159.944000000000,165.088000000000,170.176000000000,175.216000000000,180.208000000000,185.144000000000])
#ax.fill_between(p_d_riousset, Vcr_spherical_lower, Vcr_spherical_gg_upper, label = 'R24 Spherical', alpha = 0.2, color = 'xkcd:green')
#Riousset Spherical Nelson A,B
p_d_riousset_ion = np.concatenate([np.arange(0.7,2.1,0.1),np.arange(2,13,0.5)])*0.5
Vcr_spherical_lower_nelson = np.array([2193.60302446715,1304.06161213306,1015.60163467471,876.029736986455,795.628429812578,744.615918971802,710.272331457175,686.259908399964,669.071215283745,656.610914634398,647.552108095922,641.014988020536,636.394072861376,633.259651480286,633.259651480286,631.282833001172,641.083644451862,656.105556259409,673.765447608646,692.858250519641,712.754555401458,733.098457376642,753.676886005397,774.356920925375,795.053195398290,815.709821778234,836.289835009447,856.768759171871,877.130546333100,897.364936557321,917.465698902416,937.429434753173,957.254749242093,976.941668917791,996.491227307052,1015.90516686331])
Vcr_spherical_upper_nelson = np.array([362.608251490100,344.811029930721,335.232152019294,330.187499304187,327.883664027073,327.347989809217,328.009956515484,329.514325402676,331.629209532965,334.197319238270,337.108510056209,340.283549352715,343.664115840703,347.206420567142,347.206420567142,366.398917653132,386.747178178558,407.418302082329,428.074567792542,448.566916704865,468.828663213330,488.832300644868,508.569945589218,528.043784243930,547.261145183916,566.231860544790,584.966818834404,603.477163276638,621.773850501301,639.867414794494,657.767851235084,675.484567951504,693.026378359467,710.401516070511,727.617662093408,744.681978085533])
#ax.fill_between(p_d_riousset_ion, Vcr_spherical_lower_nelson, Vcr_spherical_upper_nelson, label = 'R24 Spherical Ion', alpha = 0.2, color = 'xkcd:blue')    


#Riousset Cylindrical literature A,B
p_d_riousset_cyl = np.concatenate([np.arange(0.4,2.1,0.1),np.arange(2,13,0.5)])*0.5
Vcr_cylindrical_lower = np.array([656.660502396360,282.611829159552,219.111230424341,195.889489100798,185.658597548679,181.179456144086,179.714856855879,180.005279767344,181.392873976066,183.502083978056,186.103905137914,189.051428506760,192.246548372223,195.621587497584,199.128596959250,202.732842769056,206.408690610014,206.408690610014,225.327424438126,244.447519805703,263.374944765900,281.986798281089,300.252313215410,318.175003447677,335.771218442568,353.061508266136,370.067005221529,386.807918923104,403.302964076538,419.569208669094,435.622109756528,451.475627836146,467.142368117557,482.633724417834,497.960014797176,513.130604644454,528.154016141645,543.038024554454,557.789742451974])
Vcr_cylindrical_upper = np.array([97.6495534122478,93.5289987932898,93.8652227161699,95.9552312845367,98.8724460991904,102.219869008225,105.802507086052,109.515402512322,113.298300624950,117.114971305301,120.942898433592,124.767771903184,128.580378961443,132.374769469745,136.147132263215,139.895085406519,143.617216051443,143.617216051443,161.827680805082,179.399234881911,196.404197485567,212.916643902138,229.000225067944,244.707575763277,260.081998848473,275.159311831976,289.969402958643,304.537455042249,318.884889215829,333.030091244248,346.988973428153,360.775412921415,374.401596876854,387.878296864924,401.215089137716,414.420533040544,427.502316773766,440.467377448957,453.322000726994])
#ax.fill_between(p_d_riousset_cyl, Vcr_cylindrical_lower, Vcr_cylindrical_upper, label = 'R24 Cylindrical', alpha = 0.2, color = 'xkcd:magenta')
#Riousset Cylindrical Nelson A,B
Vcr_cylindrical_upper_nelson = np.array([315.588739514879,205.047740002358,175.583446800180,164.285685079692,159.866218127866,158.736951865010,159.407633986174,161.151887395015,163.575517692923,166.447437056412,169.624079373878,173.012139141636,176.548762225668,180.190361513249,183.905984307428,187.673214969549,191.475554825681,191.475554825681,210.673689741230,229.751970944106,248.486739694499,266.827219102656,284.777775996878,302.360735930766,319.603218217493,336.532246396328,353.172984598970,369.548217891851,385.678333591494,401.581494944075,417.273875664360,432.769899567795,448.082462919511,463.223132015618,478.202315062622,493.029410139050,507.712931975110,522.260620439055,536.679533431112])
Vcr_cylindrical_lower_nelson = np.array([-198.588635239434,-543.514922907131,-76951.1032752973,901.090078958674,545.349248604213,431.854037841349,378.370232824279,348.737301692734,330.948930211967,319.875325799766,312.959263916410,308.784654828297,306.504928861357,305.583579185243,305.664603566498,306.502833134537,307.924174046653,307.924174046653,320.291462252566,336.957036984160,355.291053939675,374.285708408553,393.494291402584,412.701231758761,431.797768458718,450.728585165491,469.466643844964,488.000449101127,506.327245432906,524.449229024798,542.371370109224,560.100131603022,577.642703369283,595.006541236634,612.199090079402,629.227619936765,646.099132390569,662.820310921716,679.397498836684])
#ax.fill_between(p_d_riousset_cyl[3:], Vcr_cylindrical_lower_nelson[3:], Vcr_cylindrical_upper_nelson[3:], label = 'R24 Cylindrical Ion', alpha = 0.2, color = 'xkcd:green')

#Graph Appearence
ax.set_title("Air Breakdown with 0.8 cm Diameter Steel Electrode", fontsize = 18)
#ax.set_ylim([100, 1000])
ax.set_xlabel(r'$pd~{\rm (cm\cdot Torr)}$', fontsize = 18)
ax.set_ylabel(r'$V_{\rm cr}~{\rm (V)}$', fontsize = 18)
#ax.set_xscale('log')
ax.minorticks_on()
ax.tick_params(axis='both', which = 'major', labelsize=16)
ax.legend(loc="lower right", frameon=False)
plt.show()