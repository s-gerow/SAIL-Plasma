import matplotlib.pyplot as plt
import numpy as np
import sympy as sym

from sympy.vector import CoordSys3D
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import rc
from matplotlib.ticker import MultipleLocator, FixedLocator
import matplotlib.ticker as mticker
from matplotlib.ticker import FormatStrFormatter

fig = plt.figure(figsize=(10, 8))

A = 1.04
B = 596.8
gg = 10**-2
pd = np.linspace(10**-1, 10**3, 10**3)

def paschen_perp_2d(angle):
        A = 1.04
        B   = 596.8
        gg = 10**-2
        beta_angle = angle*(np.pi/180)
        beta = np.ones([10**3,])*beta_angle
        pd = np.linspace(10**-1, 10**3, 10**3)
        beta, pd = np.meshgrid(beta, pd)
        return (B*pd*beta/np.sin(beta))/np.log((beta*A*pd/np.sin(beta))/np.log(1+(1/gg)))

def legend_without_duplicate_labels(ax):
    handles, labels = ax.get_legend_handles_labels()
    unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
    ax.legend(*zip(*unique), loc="upper right")

#beta = np.linspace(0, beta_angle, 10**3)

custom_ticks = [0, np.pi/2, np.pi]
custom_tick_labels = ['$0$', '$\pi/2$', '$\pi$']

def log_tick_formatter(val, pos=None):
    return f"$10^{{{int(val)}}}$"  # remove int() if you don't use MaxNLocator
    # return f"{10**val:.2e}"      # e-Notation

#Vcr_non = (B*pd*beta/np.sin(beta))/np.log((beta*A*pd/np.sin(beta))/np.log(1+(1/gg)))
Vcr_parallel = (B*pd)/np.log((A*pd)/np.log(1+(1/gg)))


'''
ax3 = fig.add_subplot(111, projection='3d')
ax3.plot_surface(beta, np.log10(pd), np.log10(Vcr_non), cmap='coolwarm')
ax3.zaxis.set_major_formatter(mticker.FuncFormatter(log_tick_formatter))
ax3.zaxis.set_major_locator(mticker.MaxNLocator(integer=True))
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(log_tick_formatter))
ax3.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))



ax3.set_xticks(custom_ticks)
ax3.set_xticklabels(custom_tick_labels)
ax3.view_init(elev=25, azim=25, roll=0)
'''

ax2 = fig.add_subplot(111)
ax2.plot(np.log10(pd), np.log10(paschen_perp_2d(0.1)), 'b', label = "~0 degrees")
ax2.plot(np.log10(pd), np.log10(paschen_perp_2d(45)), 'orange', label = '15 degrees')
ax2.plot(np.log10(pd), np.log10(paschen_perp_2d(60)), 'green', label = '5 degrees')
ax2.plot(np.log10(pd), np.log10(paschen_perp_2d(90)), 'pink', label = '2.5 degrees' )
ax2.plot(np.log10(pd), np.log10(Vcr_parallel), 'r.', label = 'parallel')

ax2.yaxis.set_major_formatter(mticker.FuncFormatter(log_tick_formatter))
ax2.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(log_tick_formatter))
ax2.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

ax2.set_xlabel(r'$pd[cm*Torr]$')
ax2.set_ylabel(r'$V_{cr}[V]$')

legend_without_duplicate_labels(ax2)
plt.show()