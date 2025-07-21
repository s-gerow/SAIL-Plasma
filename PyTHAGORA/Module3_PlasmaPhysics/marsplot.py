import numpy as np
import imageio as iio
import pandas as pd
import spectral as sp
from math import pi
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh
import os
from PyTHAGORA.PDSnav import *


def sph2cart(azimuth,elevation,r):
    x = r * np.cos(elevation) * np.cos(azimuth)
    y = r * np.cos(elevation) * np.sin(azimuth)
    z = r * np.sin(elevation)
    return x, y, z

filename = 'megt90n000cb.hdr'
R_Mars = 3390e3; 
A  = 10; #scaling factor


MOLA = sp.open_image(filename)
#help(MOLA)
N_lat = MOLA.read_band(0).shape[0]
N_lon = MOLA.read_band(0).shape[1]
MOLA_data=MOLA.read_band(0)

if filename[10]=='c':
    h = 4
elif filename[10]=='e':
    h = 16
elif filename[10]=='f':
    h = 32
elif filename[10]=='g':
    h = 64
elif filename[10]=='h':
    h = 128

if filename[6]=='n':
    d = +1
elif filename[6]=='s':
    d = -1


lambda_0 = float(filename[7:10])
theta_0 = float(filename[4:6])*d
lambda_ = lambda_0 + np.arange(0,N_lon,1)/h
theta_ = theta_0 - np.arange(0,N_lat,1)/h
dlambda = lambda_[1]-lambda_[0]
dtheta = theta_[1]-theta_[0]

lambda_ = np.append(lambda_,(lambda_[-1]+dlambda))
theta_ = np.append(theta_,(theta_[-1]+dtheta))
MOLA_data = np.c_[MOLA_data, MOLA_data[:,0]]
MOLA_data = np.r_[MOLA_data, [MOLA_data[0]]]

az = lambda_*pi/180
el = theta_*pi/180
r = R_Mars

[az,el,r]=np.meshgrid(az,el,r)
[az,el,r] = [az.reshape(721,1441), el.reshape(721,1441),r.reshape(721,1441)]
r = r+A*MOLA_data


[x,y,z] = sph2cart(az,el,r)

fig = plt.figure()
ax = fig.add_subplot(111,projection="3d")
surf = ax.scatter(x, y, z, c=r, cmap=cm.copper)
fig.colorbar(surf, ax=ax)
plt.show()