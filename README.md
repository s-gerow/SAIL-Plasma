# SAIL-Plasma
Repository for Python Code Relating to the Project PyTHAGORA or Project BeAMED at the Space and Atmospheric Instrumentation Lab, Embry-Riddle Aeronautical University

## Project PyTHAGORA
***Py**thon **T**raining for **H**eliophysics, **A**stronomy, and **G**eosciences: an **O**pencourse for **R**esearchers with **A**pplications*  
Project PyTHAGORA is a self-guided, open source, cross-platform training course for the purpose of teaching Python to an absolute beginner with relevant examples to current applications across a variety of industries. 
### Course Overview
#### **Py1. Base Track**  
>*Software Requirements: Google Colab, JupyterLab, or equivalent IDE capable of reading and editing .pynb files*  
*Hardware Requirements: A computer with the most recent installation of Python*

This track will teach you the basics of Python programming and prepare you for the 4 more advanced tracks.

*GettingStarted.md*  
The GettingStarted.md file will walk you through some of the skills required to begin this course such as choosing and using an IDE (integrated development environment), working with PyBricks (for the LEGO robotics course), and a few other useful tools.

*1a. Introduction to Python*  
This section will teach you the very basics of Python and give you two programs to run on a Lego SPIKE Prime smart brick.
* Python Basics
* Project 0-1: First Project

*1b. Lists, Tuples, and Dictionaries*  
This section will teach you how lists and other list-like data types work and can be used
* Lists
* Tuples
* Dictionaries

*1c. Loops*  
This section will cover each type of control structure/loop in depth and finish with a project file which will walk you through a few small loop related projects.
* If Statements
* For Loops
* While Loops
* Project 1: Loops Mini-Project
* Other Control Structures and Statements

*1d. Classes and Functions*  
This is the final sections of the Base Track and will cover functions and classes which will allow you to begin building modules and packages.
* Functions
* Classes
* Project 2: Classes

*1e. Modules, Packages, and Open-Source Development*  
An additional mini-track which will teach you about how modules and packages work, as well as introduce you to Github and general good practices when developing software, particularly in the open-source community. This will also include some resources from the Python in HelioPhysics Community and other open source communities.

#### **Py2. Robotics Track**  
>*Prerequisites: Py1*  
*Software Requirements: Google Colab, JupyterLab, or equivalent IDE*  
*Hardware Requirements: A computer with the most recent installation of Python; LEGO Spike smart hub with most recent installation of Pybricks micro-python*

This track aims to teach general robotics and system control by utilizing a LEGO Spike Prime smart brick and Pybricks micro-Python software.

*2a. Pybricks Sensors*  
This section will teach you how to use the Lego motion devices and sensors with the Pybricks micro-Python software.
* Test Pybricks Code
* Project 0-2: First Project (Pybricks)
* Distance Sensor
* Color Sensor
* Force Sensor
* Motors
* Project 3: Move Until...

*2b. Control System Basics*  
This section will teach you the basic concepts of system control and how they are translated to Python.
* Control Systems
* Project 4: PID Line Tracker

#### **Py3. Data Acquisition, Visualization, and Analysis**  
>*Prerequisites: Py1*  
*Software Requirements: Google Colab, JupyterLab, or equivalent IDE*  
*Hardware Requirements: A computer with the most recent installation of Python*  

This track will teach you how to interface with devices in an experiment to retrieve relevant data, visualize it with Matplotlib, and analyze it.
Data Acquisition
* Numpy for Working with large Datasets
* Scipy and Numerical Methods
* Sympy for Symbolic Math
* Matploptlib for Visualizing Data
* Tkinter for building GUIs

#### **Py4. Plasma Physics**  
>*Prerequisites: Py1, Py3*  
*Software Requirements: Google Colab, JupyterLab, or equivalent IDE*  
*Hardware Requirements: A computer with the most recent installation of Python*  

This section will teach you the basic principles of plasma physics as well as several uses for Python within the field.
* Introduction to Plasma Physics
* Particle in Field Lesson
* Project 5: Particle in Field
* Successive Over Relaxation Lesson
* Project 6: Successive Over Relaxation
* Mars Global Surveyor Data
* Project 7: Wet Mars
* Project 8: Mars Crustal Field

#### **Py5. Astronomy**
>*Prerequisites: Py1, Py3*  
*Software Requirements: Google Colab, JupyterLab, or equivalent IDE*  
*Hardware Requirements: A computer with the most recent installation of Python*

This section will teach you various applications of Python in Astrophysics. This section has extensive use of Numpy and Astropy.

*5a. Photometry Time Series* 
* Making Light Curve using TESS Data

## Project BeAMED
***Be**nch for **A**utomated **M**easurements of **E**lectrical **D**ischarges*  
Project BeAMED seeks to characterize the initiation of dielectric breakdown in planetary atmospheres. This is done by inilizing plasma discharges in a dusty plasma chamber in the Space and Atmospheric Instrumentation Laboratory. The experimental outputs (including error bars) will be compared with Riousset et al.’s (2024) generalized Townsend’s theory for Paschen curves in planar, cylindrical, and spherical geometries.  
Included in this repository are the Python files for the user interface (UI) that will operate the dusty plasma chamber. Operation of the chamber includes automated piloting of the following elements:
* a mass flow controller (MFC) for a precision back-fill of the gas mixtures;
* a microcurrent sensor that triggers recordings of the voltage, current, and pressure;
* two motorized linear feedthroughs for higher precision in gap size variations;
* a Dust dispensing And Retaining Equipment (DARE) to explore the feasibility of triboelectric charging in the initiation of electrical discharges in Mars’ atmosphere.
