import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.animation as animation
from CurveFit import unpack_coeffs, find_peicewise, fit_data, continuity_conditions, concavity_conditions, plot_data

def find_optimal_fit(dataframe: pd.DataFrame, animate: bool = False, verbose: bool = False, filename: str = "Untitled", length_constraints = [5, 15, 5]) -> tuple:
    '''
    Takes a set of pd and voltage arrays to find the most optimal fit for the data. Returning the 
    coefficients of the fit, the r_squared value, and node points of the fit.\n
    Parameters:
        dataframe (pd.DataFrame): The dataframe containing the experimental data.
        animate (bool): Whether to animate the fitting process.
    Returns:
        coeffs (list): The coefficients of the optimal fit.
        r_squared (float): The r_squared value of the optimal fit.
        node_points (list): The node points of the optimal fit.
    '''
    def print_log(msg: str):
        if verbose:
            print(msg)

    print_log("Finding optimal fit...")
    if animate:
        fig, ax = plt.subplots()
        ax.set(xlabel='pd (Torr*cm)', ylabel='Voltage (V)', title='Optimal Fit Finding Process')
    

    artistList = []
    
    if animate:
        scatterArtist, v, pd = plot_data(dataframe, ax,return_artist=True)
        ax.set(xlim=[pd.min()-.50, pd.max()+0.5], ylim=[v.min()-50, v.max()+50])
    else:
        v, pd = plot_data(dataframe, return_artist=False)
    # Calculate total sum of squares for R-squared calculation
    v_bar = np.mean(v)
    ss_tot = np.sum((v - v_bar)**2)
    
    # start with an assumption of 5 points per linear segment on the left and right:
    leftLength = length_constraints[0]
    rightLength = length_constraints[2]
    middleLength = length_constraints[1]# setting minimum middle length, for a cubic polynomial at least 4 points are needed but we need two more for 
    # the extra boundary conditions

    Coefficients = [[], 0, []] # [coefficients, r-squared, nodes]
    for leftNode in range(leftLength, len(pd)-middleLength-rightLength):
        # test different lengths of the left segment up to the total length of the dataset minus the minimum lengths of the other segments
        for rightnode in range(rightLength, len(pd)-middleLength-leftNode):
            # test different lengths of the right segment up to the total length of the dataset minus the minimum length of the middle segment 
            # the dynamic length of the left segment
            rightNode = -rightnode # used for backwards indexing... man that is just the best feature of all time

            #leftmost points of pd and v
            leftLinearPD = pd[:leftNode] 
            leftLinearV = v[:leftNode]
            #rightmost points of pd and v
            rightLinearPD = pd[rightNode:]
            rightLinearV = v[rightNode:]
            #middle segment of pd and v
            middlePD = pd[leftNode:rightNode]
            middleV = v[leftNode:rightNode]

            print_log(f"Testing Nodes:\nLeft Range: {leftLinearPD}\nMiddle Range: {middlePD}\nRight Range: {rightLinearPD}")
            print_log("Calculating initial guesses...")
    
            polyLeft = np.polyfit(leftLinearPD, leftLinearV, 1)
            polyMid = np.polyfit(middlePD, middleV, 3)
            polyRight = np.polyfit(rightLinearPD, rightLinearV, 1)
            fittedCoeffs = np.concatenate([polyLeft, polyMid, polyRight])
    
            print_log(f"Initial Coefficients:\nLeft: {polyLeft}\nMiddle: {polyMid}\nRight: {polyRight}")
            #make initial frame of guesses
            print_log("Calculating initial fit...")

            print_log("Calculating initial residuals...")
    
            ss_res = fit_data(fittedCoeffs, pd, v, pd[leftNode-1], pd[rightNode])
            rSquared = 1 - (ss_res / ss_tot)
    
            print_log(f"Initial R-squared: {rSquared}")
            
            def append_artist(color = 'xkcd:black'):
                xFit = np.linspace(pd.min(), pd.max(), 500)
                if rSquared != Coefficients[1]:
                    yFit = find_peicewise(xFit, fittedCoeffs, pd[leftNode-1], pd[rightNode])
                    if animate:
                        fitArtist = ax.plot(xFit, yFit, color=color)[0]
                        annotateArtist = ax.text(pd.max()-1.5, v.min()-25, f"$R^2$: {rSquared}", color = color)
                        localArtistList = [annotateArtist, fitArtist, scatterArtist[0]]
                        localArtistList.extend(scatterArtist[1])
                        localArtistList.extend(scatterArtist[2])
                    if Coefficients[1] != 0:
                        xFit = np.linspace(pd.min(), pd.max(), 500)
                        goodCoeffs = Coefficients[0]
                        goodLeftNode = Coefficients[2][0]
                        goodRightNode = Coefficients[2][1]
                        goodRSquared = Coefficients[1]
                        if animate:
                            yFitGood = find_peicewise(xFit, goodCoeffs,pd[goodLeftNode-1],pd[goodRightNode])
                            goodFitArtist = ax.plot(xFit, yFitGood, color = 'xkcd:green')[0]
                            goodAnnotateArtist = ax.text(pd.max()-1.5, v.min()-10, f"$R^2$: {goodRSquared}", color = 'xkcd:green')
                            localArtistList.append(goodFitArtist)
                            localArtistList.append(goodAnnotateArtist)
                    if animate:
                        artistList.append(localArtistList)
            if animate:
                append_artist()
    
            
            #print_log("Optimizing fit...")
    
            contraints = [
            {
                'type': 'eq',
                'fun': lambda coeffs: continuity_conditions(coeffs, pd[leftNode-1], pd[rightNode])
            },
            {
                'type': 'ineq',
                'fun': lambda coeffs: concavity_conditions(coeffs, pd[leftNode-1], pd[rightNode])
            }
            ]
            # Debug: check knot values and continuity before optimization
            left_knot_val = pd[leftNode-1]
            right_knot_val = pd[rightNode]
            print_log(f"DEBUG: leftNode index={leftNode}, rightNode index={rightNode}")
            print_log(f"DEBUG: left_knot value={left_knot_val}, right_knot value={right_knot_val}")
            initial_cont = continuity_conditions(fittedCoeffs, left_knot_val, right_knot_val)
            print_log(f"DEBUG: Initial continuity conditions: {initial_cont}")
            
            result = minimize(fit_data, fittedCoeffs, args = (pd, v, pd[leftNode-1], pd[rightNode]), constraints=contraints, method='SLSQP')
            
            if result.success:
                print_log("Optimized fit found")
                fittedCoeffs = result.x
                final_cont = continuity_conditions(fittedCoeffs, left_knot_val, right_knot_val)
                print_log(f"DEBUG: Final continuity conditions: {final_cont}")
                print_log("Calculating R-squared")
                ss_res = fit_data(fittedCoeffs, pd, v, pd[leftNode-1], pd[rightNode])
                rSquared = 1 - (ss_res / ss_tot)
                print_log(f'Optimized Result:\nCoefficients:\n\tLeft: {polyLeft}\n\tMiddle: {polyMid}\n\tRight: {polyRight}\nR-Squared:\n\t{rSquared}')
            else:
                print(f"Optimization Failed:\n{result.message}")
            if rSquared > Coefficients[1]:
                Coefficients[0] = fittedCoeffs
                Coefficients[1] = rSquared
                Coefficients[2] = [leftNode, rightNode]
                append_artist(color='xkcd:green')

    xFit = np.linspace(pd.min(), pd.max(), 500)
    if animate:
        localArtistList = [scatterArtist[0]]
        localArtistList.extend(scatterArtist[1])
        localArtistList.extend(scatterArtist[2])
    goodCoeffs = Coefficients[0]
    goodLeftNode = Coefficients[2][0]
    goodRightNode = Coefficients[2][1]
    goodRSquared = Coefficients[1]
    if animate:
        yFitGood = find_peicewise(xFit, goodCoeffs,pd[goodLeftNode-1],pd[goodRightNode])
        goodFitArtist = ax.plot(xFit, yFitGood, color = 'xkcd:green')[0]
        goodAnnotateArtist = ax.text(pd.max()-1.25, v.min()-10, f"$R^2$: {goodRSquared}", color = 'xkcd:green')
        goodNodesArtist = ax.vlines([pd[goodLeftNode], pd[goodRightNode]],v.min()-50, v.max()+50,color = 'xkcd:gray', linestyles='dashed')
        localArtistList.append(goodFitArtist)
        localArtistList.append(goodAnnotateArtist)
        localArtistList.append(goodNodesArtist)
        artistList.append(localArtistList)

    if animate:
        ani = animation.ArtistAnimation(fig, artistList, interval=75, repeat = False)
        plt.show()
        ani.save(filename=f'./BeAMED/Test Scripts/Beamed_data_11102025/{filename}Animation.gif')
        #ax.clear()
        for artist in artistList[-1]:
            print(artist)
            ax.add_artist(artist)
            plt.show()
        fig.savefig(fname = f'./BeAMED/Test Scripts/Beamed_data_11102025/{filename}OptimizedPlot.png')

    return Coefficients

if __name__ == "__main__":
    beamed_5mmN2 = pd.read_csv('./BeAMED/Test Scripts/Beamed_data_11102025/202565_N2_5mm.csv').sort_values(by='p_MKS(Torr)')
    Coefficients = find_optimal_fit(beamed_5mmN2, 0.98, animate=True, verbose=True)
    
