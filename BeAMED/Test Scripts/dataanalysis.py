import numpy as np
import pandas as pd
from tkinter import filedialog as fd
import matplotlib.pyplot as plt
from scipy.optimize import minimize, brentq
import matplotlib.animation as animation
import time

plt.rcParams['text.usetex'] = False

class animator():
    def __init__(self, fig, ax, filename):
        self.fig = fig
        self.ax = ax
        self.filename = filename
        self.artistlist = [[]]
        self.persistentartist = []
        self.persistentkeep = []

    def set_persistent(self, artist, keep = False):
        print(f'setting persistent artist list')
        if isinstance(artist, list):
            self.persistentartist = artist
        else:
            self.persistentartist = [artist]
        if keep:
            self.persistentkeep = self.persistentartist
        self.artistlist[0] = self.persistentartist

    def append_persistent(self, artist):
        print('appending to persistent artist list')
        if isinstance(artist, list):
            self.persistentartist.extend(artist)
        else:
            self.persistentartist.append(artist)
        self.artistlist[0] = self.persistentartist

    def list_frames(self):
        print('Current artists in artist list:')
        for i, frame in enumerate(self.artistlist):
            print(f"Frame: {i} | Artists: {frame}")
        
    def get_frame(self, frame_id):
        return self.artistlist[frame_id]
    
    def add_new_frame(self, artists):
        print('adding new animation frame')
        local_list = self.persistentartist.copy()
        if isinstance(artists, list):
            local_list.extend(artists)
        else:
            local_list.append(artists)
        self.artistlist.append(local_list)
        #print(self.artistlist)

    def append_frame(self, artists, frame_id):
        local_list = self.artistlist[frame_id].copy()
        if isinstance(artists, list):
            local_list.extend(artists)
        else:
            local_list.append(artists)    
        self.artistlist[frame_id] = local_list
    
    def generate_animation(self):
        ani = animation.ArtistAnimation(self.fig, self.artistlist, interval=50, repeat = False)
        ani.save(filename=f'./BeAMED/Test Scripts/Beamed_data_11102025/{self.filename}Animation.gif')
        plt.show()
        return ani


def open_data(filepath:str, use_ps_voltage:bool = False):
    '''
    Opens BeAMED output csv and upacks it into v, pd, verr, and pderr
    Parameters:
        filepath (str): string representing the location of the BeAMED csv file
        use_ps_voltage (bool): if true, will use the power supply output measurement instead of multimeter measurement.
    Returns:
        pd, v, pderr, verr
    '''
    print(f'opening {filepath}')
    data = pd.read_csv(filepath).sort_values(by='p_MKS(Torr)')
    p = data.iloc[:,5].values
    d = data.iloc[:,8].values
    if use_ps_voltage:
        v = data.iloc[:,2].values
    else:
        v = data.iloc[:,3].values
    p_d = np.array(p*d)
    pd_err = data.iloc[:,14].values
    v_err = data.iloc[:,9].values
    return p_d, v, pd_err, v_err

def unpack_coeffs(coeffs: list) -> tuple:
    '''
    Takes a list of coeffecients and for a peicewise function with a linear, cubic, and linear section, 
    unpacks the coeffecients into their respective sections.\n
    
    Parameters:
        coeffs (list): A list of 10 coeffecients for the peicewise
    Returns:
        left (list): The coeffecients for the left linear section.
        mid (list): The coeffecients for the middle cubic section.
        right (list): The coeffecients for the right linear section.
    '''
    left = coeffs[:2]
    mid = coeffs[2:6]
    right = coeffs[6:]
    return left, mid, right

def split_data(x: np.array, y: np.array, n1: int, n2: int, length: int = 100, endpoints = True, use_original_lengths = False):
    '''
    Split a dataset at two node points, creating three new arrays per axis. Defaults to 100 points per new array but 
    can be overwritten using the length parameter.

    Parameters:
        x (np.array): An array of x data points
        y (np.array): An array of corresponding y data points
        n1 (int): x-position index of the first node
        n2 (int): x-position index of the second node
        length (int): integer representing the length of each new array
        endpoints (bool): Boolean input, if true the endpoints of each array at the node points will be equal, e.g. x1[-1] = x2[0]
        use_original_lengths (bool): if true, the function will simply return the input array split into three segments
    Returns:
        x (list): a list of three arrays with each segment of the input set
        y (list): a list of three arrays with each segment of the input set
    '''
    #print(f'splitting array of length {len(x)} at node points {n1} and {n2}')
    if endpoints:
        x1 = x[:n1+1]
        x2 = x[n1:n2+1]
        x3 = x[n2:]
        y1 = y[:n1+1]
        y2 = y[n1:n2+1]
        y3 = y[n2:]
    else:
        x1 = x[:n1]
        x2 = x[n1:n2]
        x3 = x[n2:]
        y1 = y[:n1]
        y2 = y[n1:n2]
        y3 = y[n2:]
    if use_original_lengths:
        #print(f'returning arrays of sizes: {len(x1)}, {len(x2)}, and {len(x3)}')
        return [x1,x2,x3],[y1,y2,y3]
    else:
        x1p = np.linspace(x1[0], x1[-1], length)
        x2p = np.linspace(x2[0], x2[-1], length)
        x3p = np.linspace(x3[0], x3[-1], length)
        y1p = np.linspace(y1[0], y1[-1], length)
        y2p = np.linspace(y2[0], y2[-1], length)
        y3p = np.linspace(y3[0], y3[-1], length)
        #print(f'returning expanded arrays of sizes: {len(x1p)}, {len(x2p)}, and {len(x3p)}')
    return [x1p,x2p,x3p],[y1p,y2p,y3p]

def eval_polynomial(x: list, coeffs: list):
    '''
    Finds the y values of a peicewise polynomial curve given the x values, list of coefficients, and the location of the 
    function nodes.\n
    Parameters:
        x (list): An list of x data point arrays
        coeffs (list): A list of coefficients corresponding to each array in x_data
    Returns:
        y (list): A list of y data point arrays corresponding to the coefficients inputted evaluated at each position in the x arrays
    '''

    c_left, c_mid, c_right = unpack_coeffs(coeffs)
    x1 = x[0]
    x2 = x[1]
    x3 = x[2]

    y1 = np.zeros_like(x1)
    y2 = np.zeros_like(x2)
    y3 = np.zeros_like(x3)

    for i,x in enumerate(x1):
        #print(f'evaluating first segment with coefficients: {c_left}')
        y1[i] = np.polyval(c_left, x)
    for i,x in enumerate(x2):
        #print(f'evaluating first segment with coefficients: {c_mid}')
        y2[i] = np.polyval(c_mid, x)
    for i,x in enumerate(x3):
        #print(f'evaluating first segment with coefficients: {c_right}')
        y3[i] = np.polyval(c_right, x)
    
    return [y1, y2, y3]

def continuity_conditions(coeffs, left_node_x, right_node_x):
    c_left, c_mid, c_right = unpack_coeffs(coeffs)

    d_left = np.polyder(c_left)

    d_mid = np.polyder(c_mid)
    dd_mid = np.polyder(d_mid)

    d_right = np.polyder(c_right)

    #c0 continuity
    c0_left = np.polyval(c_left, left_node_x) - np.polyval(c_mid, left_node_x)
    c0_right = np.polyval(c_right, right_node_x) - np.polyval(c_mid, right_node_x)

    #c1 continuity
    c1_left = np.polyval(d_left, left_node_x) - np.polyval(d_mid, left_node_x)
    c1_right = np.polyval(d_right, right_node_x) - np.polyval(d_mid, right_node_x)

    #c2 continuity
    #c2_left = np.polyval(dd_mid, left_knot)
    #c2_right = np.polyval(dd_mid, right_knot)

    return [c0_left, c0_right, c1_left, c1_right]#, c2_left, c2_right]

def concavity_conditions(coeffs, left_node_x, right_node_x):
    c_left, c_mid, c_right = unpack_coeffs(coeffs)

    d_mid = np.polyder(c_mid)
    dd_mid = np.polyder(d_mid)

    c_up_left = np.polyval(dd_mid, left_node_x)
    c_up_right = np.polyval(dd_mid, right_node_x)

    return [c_up_left, c_up_right]

def fit_data(coeffs, x_data_list, y_data_list):
    y_fit_list = eval_polynomial(x_data_list, coeffs)
    y_fit = np.concatenate(y_fit_list)
    x_data = np.concatenate(x_data_list)
    y_data = np.concatenate(y_data_list)
    if len(y_data) != len(y_fit):
        raise ValueError(f"Input arrays of size {len(y_data)} and {len(y_fit)} not compatitble")
    return np.sum((y_data - y_fit)**2)

def find_continuous_fit(x: np.array, y: np.array, n1: int, n2: int):
    # split x and y experimental data into three parts
    #ybar = np.mean(y)
    x_data_list, y_data_list = split_data(x, y, n1, n2, use_original_lengths=True)
    x1 = x_data_list[0]
    x2 = x_data_list[1]
    x3 = x_data_list[2]
    y1 = y_data_list[0]
    y2 = y_data_list[1]
    y3 = y_data_list[2]

    # create fitted x-axis array
    x_data = np.concatenate(x_data_list)
    y_data = np.concatenate(y_data_list)

    # find polynomial fit for each segment, this is our initial guess
    poly1 = np.polyfit(x1, y1, 1)
    poly2 = np.polyfit(x2, y2, 3)
    poly3 = np.polyfit(x3, y3, 1)

    initial_guess = np.concatenate([poly1, poly2, poly3])

    # test if data is sufficient for further testing
    n1 = x1[-1]
    n1_ = x2[0]
    n2 = x2[-1]
    n2_ = x3[0]

    if n1 != n1_:
        raise ValueError("Node end points in x1 and x2 not compatible for continuity test")
    if n2 != n2_:
        raise ValueError("Node end points in x2 and x3 not compatible for continuity test")
    
    # set constraints, continuous at nodes and derivatives 
    contraints = [
        {
            'type': 'eq',
            'fun': lambda coeffs: continuity_conditions(coeffs, n1, n2)
        },
        {
            'type': 'ineq',
            'fun': lambda coeffs: concavity_conditions(coeffs, n1, n2)
        }
    ]

    result = minimize(fit_data, initial_guess, args = (x_data_list, y_data_list), constraints=contraints, method='SLSQP')

    ss_res = fit_data(result.x, x_data_list, y_data_list)

    return result.x, ss_res

def optimize_fit(x: np.array, y: np.array, r1_min_length:int, r2_min_length: int, r3_min_length: int, animate:bool = True, animator:animator = None):
    leftLength = r1_min_length
    rightLength = r3_min_length
    middleLength = r2_min_length

    if animate:
        ax = animator.ax

    y_bar = np.mean(y)
    ss_tot = np.sum((y - y_bar)**2)

    # initilize return array
    Coefficients = [[], 0, []]

    for leftNode in range(leftLength, len(x)-middleLength-rightLength):
        # test different lengths of the left segment up to the total length of the dataset minus the minimum lengths of the other segments
        for rightnode in range(rightLength, len(y)-middleLength-leftNode):
            # test different lengths of the right segment up to the total length of the dataset minus the minimum length of the middle segment 
            # the dynamic length of the left segment
            rightNode = -rightnode # used for backwards indexing... man that is just the best feature of all time
            coeffs, ss_res = find_continuous_fit(x, y, leftNode, rightNode)

            x_fit, _ = split_data(x, y, leftNode, rightNode)
            y_fit = eval_polynomial(x_fit, coeffs)
            rSquared = 1 - (ss_res / ss_tot)
            if animate:
                plotArtist = ax.plot(np.concatenate(x_fit), np.concatenate(y_fit), color = 'xkcd:black')[0]
                annotateArtist = ax.text(x.max()-1.5, y.min()-10, f"$R^2$: {rSquared}", color = 'xkcd:black')
                animator.add_new_frame(plotArtist)
                animator.append_frame(annotateArtist, -1)
            if rSquared > Coefficients[1]:
                if animate:
                    scatterArtist = animator.persistentkeep.copy()
                    plotGoodArtist = ax.plot(np.concatenate(x_fit), np.concatenate(y_fit), color = 'xkcd:green')[0]
                    annotateGoodArtist = ax.text(x.max()-1.5, y.min()+10, f"$R^2$: {rSquared}", color = 'xkcd:green')
                    animator.set_persistent(scatterArtist)
                    animator.append_persistent(plotGoodArtist)
                    animator.append_persistent(annotateGoodArtist)
                Coefficients[0] = coeffs
                Coefficients[1] = rSquared
                Coefficients[2] = [leftNode, rightNode]
    if animate:
        animator.add_new_frame([])
    return Coefficients

def EngleSteinbeckEquation(pd, A, B, gg, reject_asymptote = False):
    VES = lambda pd: (B*pd)/np.log((A*pd)/np.log(1+(1/gg)))
    if reject_asymptote:
        pd = pd[pd >brentq(VES, pd[0], pd[-1])]
    v = np.zeros_like(pd)

    for i,pdx in enumerate(pd):
        v[i] = VES(pdx)
    return pd, v

def main():
    filepath = './BeAMED/Test Scripts/Beamed_data_11102025/202565_N2_5mm.csv'
    p_d, v, pd_err, v_err = open_data(filepath=filepath)
    fig, ax = plt.subplots()
    ax.set(xlim=[p_d.min()-.50, p_d.max()+0.5], ylim=[v.min()-50, v.max()+50])

    errorbarActor = ax.errorbar(p_d, v, v_err, pd_err, fmt='.', capsize=4, markerfacecolor = 'none')
    artistList = [errorbarActor[0]]
    artistList.extend(errorbarActor[1])
    artistList.extend(errorbarActor[2])

    ani_object = animator(fig, ax, filename="testing")
    ani_object.set_persistent(artistList, keep = True)

    coeffs_list = optimize_fit(p_d, v, 5, 6, 5, animator=ani_object, animate=True)
    coeffs = coeffs_list[0]
    pd_fit, _ = split_data(p_d, v, coeffs_list[2][0], coeffs_list[2][1])
    v_fit = eval_polynomial(pd_fit, coeffs)

    ani = ani_object.generate_animation()
    for artist in ani_object.get_frame(-1):
        ax.add_artist(artist)
        plt.show()
        #ani_object.fig.savefig(fname = f'./BeAMED/Test Scripts/Beamed_data_11102025/{ani_object.filename}OptimizedPlot.png')


if __name__ == "__main__":
    main()