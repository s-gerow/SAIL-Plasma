import sys
import time
from typing import Literal

import numpy as np
import pyvisa
from dataclasses import dataclass

from equipment.visaequipment import VisaEquipment

class KeithleyDMM6500(VisaEquipment):
    def __init__(self,):
        pass