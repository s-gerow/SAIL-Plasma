import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import matplotlib.pyplot as plt
import numpy as np

with nidaqmx.Task() as task:
    ai_channel = task.ai_channels.add_ai_voltage_chan("NI_DAQ/ai0", min_val = 1, max_val = 8, terminal_config=TerminalConfiguration.RSE)
    print(ai_channel.ai_term_cfg)
    task.timing.cfg_samp_clk_timing(rate = 1000, sample_mode=AcquisitionType.FINITE,samps_per_chan=100)
    data=np.array(task.read(100))
    print(data, type(data), data.shape)