'''
Particle in Field Simulations
(MATLAB) v1: N Cicotte & JA Riousset ©2020
(MATLAB) v2: JA Riousset ©2022
(Python) v3: Seth Gerow 2024
'''
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import cm
from numpy import linalg
from math import *

class b_field:
    '''
    This class defines a magnetic field. 
    mag is the magnitude of the field. 
    btype specifies how the magnetic feild vector should be calcualted from the magnitude:
    "Bx, By, Bz, null, gradB, dipole, bottle, user"
    beta is the coefficient for the magnetic field default = 0
    N is the number of magnetic field lines to show default = 7
    '''
    rRef = 1
    def __init__(self, btype = "null", mag = 1, beta = 0, N = 7):
        self.btype = btype
        self.magnitude = mag
        self.beta = beta
        self.field_lines = N
    def get_field(self, X):
        x = float(X[0])
        y = float(X[1])
        z = float(X[2])
        r = sqrt(x**2 + y**2 + z**2)
        btype = self.btype
        if r != 0:
            match btype:
                case "null":
                    Bx = 0
                    By = 0
                    Bz = 0
                case "Bx":
                    Bx = self.magnitude
                    By = 0
                    Bz = 0
                case "By":
                    Bx = 0
                    By = self.magnitude
                    Bz = 0
                case "Bz":
                    Bx = 0
                    By = 0
                    Bz = self.magnitude
                case "user":
                    Bx = 0
                    By = 0
                    Bz = 0
                case "dipole":
                    Bx = self.magnitude*self.rRef**3*(3*x*z)/r**5
                    By = self.magnitude*self.rRef**3*(3*y*z)/r**5
                    Bz = self.magnitude*self.rRef**3*(3*z**2-r**2)/r**5
                case "bottle":
                    Bx = self.magnitude*(-1*self.beta**2*x*z)
                    By = self.magnitude*(-1*self.beta**2*y*z)
                    Bz = self.magnitude*(1+self.beta**2*z**2)
                case "gradB":
                    Bx = 0
                    By = 0
                    Bz = self.magnitude*(1+self.beta*y)
        else:
            Bx = 0
            By = 0
            Bz = 0
        B = np.array([Bx,By,Bz])
        return B

class e_field:
    def __init__(self, etype = "null", mag = 0.01, alpha = 0.05):
        self.etype = etype
        self.magnitude = mag
        self.alpha = alpha
    def get_field(self,X):
        x = float(X[0])
        y = float(X[1])
        z = float(X[2])
        r = sqrt(x**2 + y**2 + z**2)
        etype = self.etype
        if r != 0:
            match etype:
                case "null":
                    Ex = 0
                    Ey = 0
                    Ez = 0
                case "Ex":
                    Ex = self.magnitude
                    Ey = 0
                    Ez = 0
                case "Ey":
                    Ex = 0
                    Ey = self.magnitude
                    Ez = 0
                case "Ez":
                    Ex = 0
                    Ey = 0
                    Ez = self.magnitude
                case "user":
                    Ex = self.magnitude*cos(self.alpha*x)
                    Ey = 0
                    Ez = 0
        else:
            Ex = 0
            Ey = 0
            Ez = 0
        E = np.array([Ex,Ey,Ez])
        return E

class particle:
    def __init__(self, q = 1, m = 1, name = "particle"):
        self.name = name
        self.charge = q
        self.mass = m

def solver(particle, efield, bfield, R0, V0, t0, tf):
    def eom(t,X):
        x = X[0]
        y = X[1]
        z = X[2]
        vx = X[3]
        vy = X[4]
        vz = X[5]
        R = np.array([x,y,z])
        V = np.array([vx,vy,vz])
        F = Lorentz_Force(X)
        Fx = F[0]
        Fy = F[1]
        Fz = F[2]
        ax = Fx/m
        ay = Fy/m
        az = Fz/m
        dX = np.array([vx,vy,vz,ax,ay,az])
        return dX
    
    def Lorentz_Force(X):
        x = X[0]
        y = X[1]
        z = X[2]
        vx = X[3]
        vy = X[4]
        vz = X[5]
        R = np.array([x,y,z])
        E = efield.get_field(R)
        B = bfield.get_field(R)
        V = np.array([vx,vy,vz])
        F = q*(E + np.cross(V,B))
        return F

    def velocity(V,B,vtype = "vpp"):
        b = linalg.norm(B)
        vpp = linalg.norm(np.cross(V,B))/b
        vpr = int(np.dot(V,B))/b
        match vtype:
            case "vpp":
                return vpp
            case "vpr":
                return vpr
    
    m = particle.mass
    q = particle.charge
    X0 = np.concat([np.transpose(R0),np.transpose(V0)])
    E0 = efield.get_field(X0)
    B0 = bfield.get_field(X0)
    b0 = linalg.norm(B0)
    wg = abs(particle.charge)*b0/particle.mass
    Tg = 2*pi/wg
    vpp0 = velocity(V0,B0, vtype = "vpp")
    rg = vpp0/wg
    N = round(tf/Tg)
    print(f"Simulation Running for {N} Gyro Period")
    t_span = (t0,tf)

    sol = solve_ivp(eom, t_span, X0, max_step = 0.01)
    return sol

def simulate(initial_conditions, speed = 'real', title = 'Simulation of Particle in a Field', view = "3D", earth = False):
    '''initial_conditions takes the form of a tuple or list containing a particle object, field objects, and initial
    position and velocity values as numpy arrays size (3,), as well as an initial time and final time.
    
    initial conditions = (particle, e_field, b_field, R0 = np.array([x,y,z]), V0 = np.array([vx,vy,vz]), t0, tf)
    
    speed:  'real' - real time speed
            'slow' - 1/2x speed
            
    view:   '3D' - 3d view
            'x-y'
            'y-z'
            'x-z'
    '''
    particle, efield, bfield, R0, V0, t0, tf = initial_conditions
    sol = solver(particle, efield, bfield, R0, V0, t0, tf)
    t = sol.t
    x = sol.y[0]
    y = sol.y[1]
    z = sol.y[2]

    fig = plt.figure()
    if earth == True:
        ax = fig.add_subplot(111, projection='3d')
        ax.set_aspect("equal")
        u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:100j]
        e_x = np.cos(u)*np.sin(v)/4
        e_y = np.sin(u)*np.sin(v)/4
        e_z = np.cos(v)/4
        ax.plot_surface(e_x, e_y, e_z, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    elif earth == False:
        pass
    match view:
        case "3D":
            if earth == False:
                ax = fig.add_subplot(111, projection='3d')
            ax.plot(x, y, z, color='black', label='particle path')
            ax.set_xlim(-1,1)
            ax.set_ylim(-1,1)
            ax.set_zlim(-1,1)
            ax.set_xlabel('x(m)')
            ax.set_ylabel('y(m)')
            ax.set_zlabel('z(m)')
            ax.view_init(elev=20, azim=45)
            particle_point, = ax.plot([], [], [], 'ro', label = particle.name)
            time_text = ax.text2D(0.05, 0.95, '', transform=ax.transAxes)
        case "x-y":
            ax = fig.add_subplot(111)
            ax.plot(x,y,color='black',label = 'particle path')
            ax.set_xlabel('x(m)')
            ax.set_ylabel('y(m)')
            particle_point, = ax.plot([], [], 'ro', label = particle.name)
            time_text = ax.text(0.05, 0.95, '', transform=ax.transAxes)
        case "y-z":
            ax = fig.add_subplot(111)
            ax.plot(y,z,color='black',label = 'particle path')
            ax.set_xlabel('y(m)')
            ax.set_ylabel('z(m)')
            particle_point, = ax.plot([], [], 'ro', label = particle.name)
            time_text = ax.text(0.05, 0.95, '', transform=ax.transAxes)
        case "x-z":
            ax = fig.add_subplot(111)
            ax.plot(x,z,color='black',label = 'particle path')
            ax.set_xlabel('x(m)')
            ax.set_ylabel('z(m)')
            particle_point, = ax.plot([], [], 'ro', label = particle.name)
            time_text = ax.text(0.05, 0.95, '', transform=ax.transAxes)

    ax.grid(False)
    ax.set_title(title)
    ax.legend()



    def update(num, x, y, z, particle_point, time_text):
        if view == "3D":
            particle_point.set_data([x[num]], [y[num]])  # Pass sequences
            particle_point.set_3d_properties([z[num]])  # Pass sequences
        elif view == "x-y":
            particle_point.set_data([x[num]], [y[num]])  # Pass sequences
        elif view == "y-z":
            particle_point.set_data([y[num]], [z[num]])  # Pass sequences
        elif view == "x-z":
            particle_point.set_data([x[num]], [z[num]])  # Pass sequences
        time_text.set_text(f'Time: {t[num]:.2f}s')
        return particle_point, time_text

    #blit = False for Jupyter Lab, blit = true otherwise
    match speed:
        case 'real':
            interval = 0
        case 'slow':
            interval = 2
    ani = FuncAnimation(fig, update, frames=len(t), fargs=(x, y, z, particle_point, time_text), interval = interval, blit=False, repeat=False)

    global animation
    animation = ani
    
    plt.show()
    return ani

def test():
    example_particle = particle(q=-1)
    efield = e_field(etype = "null", mag = 0.01, alpha = 0.05)
    bfield = b_field(btype = "dipole", mag = -1, beta = 0.1)
    R0 = np.array([1,0,0])
    V0 = np.array([0.04,0.04,0.07])
    t0 = 0
    tf = 1200
    speed = 'real'

    IC = (example_particle, efield, bfield, R0, V0, t0, tf)
    title = 'Movement of a Negatively Charged Particle in a Dipole Magnetic Field'
    simulate(IC, speed, title, earth = True)