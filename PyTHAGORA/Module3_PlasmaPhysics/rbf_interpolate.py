
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
from PDSnav import *
from scipy.interpolate import RBFInterpolator, Rbf

def sph2cart(azimuth,elevation,r):
    x = r * np.cos(elevation) * np.cos(azimuth)
    y = r * np.cos(elevation) * np.sin(azimuth)
    z = r * np.sin(elevation)
    return x, y, z

