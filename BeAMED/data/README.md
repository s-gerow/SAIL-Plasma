# BeAMED Data Format Description
This file describes the format of the 2024-2026 BeAMED data output files. 

## Naming convention
With the exception of Nelson*.csv data files which have a slightly different column convention and do not include dates in their timestamp or filename, all files are .csv files with the following naming convention:

YYYYMMDD_{Gas}_{Gap Size}.csv

Where the date is the date of the first datapoint in the series.

## Column Convention

Each file contains the following columns:

* Time: Date in MM/DD/YYYY format followed by the time of discharge in 24:00 format
* D_Y(Osc): The difference between the top of the peak and bottom of the spike in current measured by the oscilloscope which detected the discharge. This has units of Volts and should correspond 1V/1A to the current in the system at the time of discharge.
* V_in: This is the input voltage measured by the Keithkley 800-1 power supply. Measured in Volts.
* V(Volts): This is the voltage measured across the breakdown gap by the Keithley DMM 6500 digital multimeter. Measured in Volts.
* Current (Amp): This is the input current measured by the Keithley 800-1 power supply. Measured in Amps.
* p_MKS(Torr): This is the pressure in the chamber measured by the MKS Baratron pressure transducer. Measured in Torr.
* p_KJL(Torr): This is the pressure in the chamber measured by the Kurt J. Lesker ____ pressure sensor. Measured in Torr.
* p_Predict(Torr): This is the input pressure that the system attempted to set the chamber to. Input is in units of Torr.
* dis (cm): This is the gap distance in cm set by the user.
* d(V): This is the uncertainty in the voltage measurement of the Keithley DMM 6500 according to the user manual. Units are Volts.
* d(p_MKS): This is the uncertainty in the pressure measurement of the MKS pressure transducer according to the user manual. Units in Torr.
* d(p_KJL): This is the uncertainty in the pressure measurement of the KJL pressure sensor according to the user manual. Units in Torr.
* d(d) This is the uncertainty of the linear feedthrough which sets the gap distance based on the resolution of the ruler on its side.
* d(pd_KJL): This is the uncertainty of the product $pd$ based on combining the uncertainties of the pressure from the KJL sensor and the distance.
* d(pd_MKS): This is the uncertainty of the product $pd$ based on combining the uncertainties of the pressure from the MKS sensor and the distance.

## Column Convention for Nelson* files

The Nelson files predated the above standard and so have some differences: mainly, that the MKS pressure transducer was not available, the linear feedthrough was not motorized, and time stamps do not include dates. The following are the Columns in these files:

* Time Stamp: If included this is the time of day the discharge was taken, date is not included.
* D_Y(mV): The difference between the top of the peak and bottom of the spike in current measured by the oscilloscope which detected the discharge. This has units of miliVolts and should correspond 1V/1A to the current in the system at the time of discharge.
* Power Supply Voltage: This is the voltage output of the Keithley 800-1 power supply. Measured in Volts.
* Voltage Output:  This is the voltage measured across the breakdown gap by the Keithley DMM 6500 digital multimeter. Measured in Volts.
* Power Supply Current: This is the input current measured by the Keithley 800-1 power supply. Measured in Amps.
* Pressure (Torr): This is the pressure in the chamber measured by the Kurt J. Lesker ____ pressure sensor. Measured in Torr.
* p_Predict(Torr): This is the input pressure that the system attempted to set the chamber to. Input is in units of Torr.
* dis (cm): This is the gap distance in cm set by the user.
* d(V): This is the uncertainty in the voltage measurement of the Keithley DMM 6500 according to the user manual. Units are Volts.
* d(p): This is the uncertainty in the pressure measurement of the KJL pressure sensor according to the user manual. Units in Torr.
* d(pd): This is the uncertainty of the product $pd$ based on combining the uncertainties of the pressure from the KJL sensor and the distance.

## Data Analysis Functions

The following Python functions are provided in addition to the above datasets to aid in the recreation of all figures in the publication.

Filename: dataanalysis.py

Author: Seth Gerow

Contact: gerows@my.erau.edu

Date of Creation: 03/04/2026

Last Changed: 03/12/2026

Functions:

  * open_data
  * unpack_coeffs
  * split_data
  * eval_polynomial
  * continuity_conditions
  * concavity_conditions
  * fit_data
  * find_continuous_fit
  * optimize_fit
  * EngleSteinbeckEquation
  * RioussetEquation

### open_data(filepath: str, use_ps_voltage:bool) -> (p_d: ndarray, v: ndarray, pd_err: ndarray, v_err: ndarray)
This function is used to extract the most commonly needed information from the csv files: $pd$, $v$, and their respective errors/uncertainties. If you need the other values in the file then you will need to get them manually.
Input:
    * filepath: string representing the relative or absolute path to one of the *.csv files above.
    * use_ps_voltage: boolean value representing whether to return the power supply output voltage or the multimeter measured voltage. Default False.
Output:
    * p_d: numpy array containing all p*d values in the file.
    * v: numpy array containing all voltage values in the file.
    * pd_err: numpy array containing all pd error values in the file.
    * v_err: numpy array containing all v error values in the file.

### unpack_coeffs(coeffs: list) -> (left: ndarray, mid: ndarray, right: ndarray)
This function takes a list of coefficients [A1, B1, A2, B2, C2, D2, A1, B1] for a linear, cubic, and linear equations like below:

$A_1x + B_1 = y$

$A_2x^3 + B_2x^2 + C_2x + D_2 = y$

$A_3x + B_3 = y$

Then it returns three tuples containing the containerized coefficients:
(A1, B1), (A2, B2, C2, D2), (A3, B3)
Input:
    * coeffs: list of 8 np.float values in order from highest order to lowest order for each segment of the fit from left to right: [linear, cubic, linear]
Output:
    * (left, mid, right): tuple of lists containing the left, middle, and right segment coefficients respectively.

### split_data(x: ndarray, y: ndarray, n1: int, n2: int, length: int = 100, endpoints: bool = True, use_original_lengths: bool = False) -> ([x1p: ndarray, x2p: ndarray, x3p: ndarray], [y1p: ndarray, y2p: ndarray, y3p: ndarray])
This function takes a full length x and y array and returns three sub arrays split at two provided node points: n1 and n2. If use_original_lengths is enabled then the function will simply split x and y at n1 and n2, producing three arrays which can be concatenated together to produce the original array. If use_original_lengths is diabled then the function will use the node points, n1 and n2, to produce three equal length arrays of size denoted by 'length' (100 by default) where the beginning and end of each array is the point located at the node points or the start/end of the input array. If endpoints is true then the last element of the array before a node point will be equal to the first element of the array after that node.
For example:
```
split_data(
    x=[1,2,3,4,5,6,7,8,9,10,11,12]
    y=[1,2,3,4,5,6,7,8,9,10,11,12]
    n1 = 4
    n2 = 9
    use_original_lengths = True
    endpoints = True
)
>>> ([1,2,3,4,5],[5,6,7,8,9,10],[10,11,12]),([1,2,3,4,5],[5,6,7,8,9,10],[10,11,12])
```
Note that the node points overlap. This is to ensure that when plotting these three arrays separately, they will share the node points and overlap on the graph. This is also necessary for ensuring they are continuous at the nodes.
Input:
    * x (np.array): An array of x data points
    * y (np.array): An array of corresponding y data points
    * n1 (int): x-position index of the first node
    * n2 (int): x-position index of the second node
    * length (int): integer representing the length of each new array
    * endpoints (bool): Boolean input, if true the endpoints of each array at the node points will be equal, e.g. x1[-1] = x2[0]
    * use_original_lengths (bool): if true, the function will simply return the input array split into three segments
Output:
    * x (list): a list of three arrays with each segment of the input set
    * y (list): a list of three arrays with each segment of the input set

### eval_polynomial(x: list, coeffs: list) -> y[y1, y2, y3]
eval_polynomial takes an input array of points and a set of coefficients in order of decreasing order and evaluates the polynomial at that position.
Input:
    * x (list): An list of x data point arrays
    * coeffs (list): A list of coefficients corresponding to each array in x_data
Output:
    * y (list): A list of y data point arrays corresponding to the coefficients inputted evaluated at each position in the x arrays

### continuity_conditions(coeffs: list, left_node_x: int, right_node_x: int):
continuity_conditions takes a full length list of coefficients 