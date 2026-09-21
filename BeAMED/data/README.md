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

### open_data(filepath: str, use_ps_voltage:bool) -> (p_d, v, pd_err, v_err)

Input:
    * filepath: string representing the relative or absolute path to one of the *.csv files above.
    * use_ps_voltage: boolean value representing whether to return the power supply output voltage or the multimeter measured voltage. Default False.
Output:
    * p_d: numpy array containing all p*d values in the file.
    * v: numpy array containing all voltage values in the file.
    * pd_err: numpy array containing all pd error values in the file.
    * v_err: numpy array containing all v error values in the file.
