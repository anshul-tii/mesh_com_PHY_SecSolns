"""
util.py
Description: 

Author: Willian T. Lunardi
Contact: wtlunar@gmail.com
License:

Repository:
"""

import glob
import os
import random
import re
import sys
from enum import Enum
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

from options import Options

CH_TO_FREQ = {1: 2412, 2: 2417, 3: 2422, 4: 2427, 5: 2432, 6: 2437, 7: 2442, 8: 2447, 9: 2452, 10: 2457, 11: 2462,
              36: 5180, 40: 5200, 44: 5220, 48: 5240, 52: 5260, 56: 5280, 60: 5300, 64: 5320, 100: 5500, 104: 5520,
              108: 5540, 112: 5560, 116: 5580, 120: 5600, 124: 5620, 128: 5640, 132: 5660, 136: 5680, 140: 5700,
              149: 5745, 153: 5765, 157: 5785, 161: 5805, 165: 5825}
FREQ_TO_CH = {v: k for k, v in CH_TO_FREQ.items()}

FEATS_ATH10K = ['max_magnitude', 'total_gain_db', 'base_pwr_db', 'rssi', 'relpwr_db', 'avgpwr_db', 'snr', 'cnr', 'pn', 'ssi', 'pd', 'sinr', 'sir', 'mr', 'pr']


class Band(Enum):
    BAND_24GHZ = "2.4GHz"
    BAND_50GHZ = "5.0GHz"


def map_channel_to_freq(channel: int) -> int:
    """
    Maps the given channel number to its corresponding frequency int.

    :param channel: The channel number.
    :return: The frequency.
    """
    return CH_TO_FREQ[channel]


def map_freq_to_channel(freq: int) -> int:
    """
    Maps the given frequency to its corresponding channel number int.

    :param channel: The channel number.
    :return: The frequency.
    """
    return FREQ_TO_CH[freq]


def map_channel_to_band(channel: int) -> Band:
    """
    Maps the given channel number to its corresponding band enum.

    :param channel: The channel number to map to a band enum.
    :return: The band enum corresponding to the given channel number.
    """
    if channel in range(1, 14):
        # 2.4 GHz channels
        return Band.BAND_24GHZ
    elif channel in range(36, 166, 4):
        # 5 GHz channels
        return Band.BAND_50GHZ
    else:
        raise ValueError(f"Invalid channel number: {channel}.")


def get_current_channel() -> int:
    """
    Get mesh interface information to parse interface name and current channel.

    :return: current channel of mesh interface.
    """
    no_mesh = False
    iw_output = os.popen('iw dev').read()
    iw_output = re.sub('\s+', ' ', iw_output).split(' ')
    size = len(iw_output)
    idx_list = [idx - 1 for idx, val in enumerate(iw_output) if val == "Interface"]
    if (len(idx_list) > 1):  idx_list.pop(0)
    iw_interfaces = [iw_output[i: j] for i, j in
                     zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))]

    for interface_list in iw_interfaces:
        try:
            mesh_index = interface_list.index("mesh")
            mesh_list = interface_list
            no_mesh = False
            break
        except:
            no_mesh = True
    if (no_mesh):
        sys.exit("No mesh interface to scan/No mesh set up")

    mesh_interface_index = mesh_list.index("Interface") + 1
    mesh_interface = mesh_list[mesh_interface_index].split()[0]
    channel_index = mesh_list.index("channel") + 2
    channel_freq = int(re.sub("[^0-9]", "", mesh_list[channel_index]).split()[0])

    return channel_freq


def load_sample_data(sample_type: Optional[str] = None):
    """
    Load sample data from a CSV file based on a randomly chosen sample type.

    :return: A tuple containing the message describing the sample data and a pandas DataFrame with the loaded data.
    """
    sample_types = ['floor', 'video', 'jamming']
    # sample_types = ['floor']  # , 'video', 'jamming']
    sample_type = random.choice(sample_types) if sample_type is None else sample_type

    if sample_type == 'floor':
        csv_files = glob.glob('sample/floor/' + '*.csv')
        path = random.choice(csv_files)
        message = f'Floor data {path}'
    elif sample_type == 'video':
        csv_files = glob.glob('sample/video/' + '*.csv')
        path = random.choice(csv_files)
        message = f'Video data {path}'
    elif sample_type == 'jamming':
        csv_files = glob.glob('sample/jamming/' + '*.csv')
        path = random.choice(csv_files)
        message = f'Jamming data {path}'
    else:
        raise ValueError("Invalid sample_type provided. Choose from 'floor', 'video', 'interference', or 'jamming'.")

    # load the data into a pandas DataFrame
    data = pd.read_csv(path)

    return message, data


def plot_timeseries(X: np.ndarray, X_resized: np.ndarray) -> None:
    # Create the figure and subplots
    fig, axs = plt.subplots(nrows=2, sharex=True, figsize=(8, 6))

    # Plot the original signal on the top
    axs[0].plot(X)
    axs[0].set_title("Original Signal")

    # Plot the resized signal on the bottom
    axs[1].plot(X_resized)
    axs[1].set_title("Resized Signal")

    # Set the x-axis label
    fig.text(0.5, 0.04, 'Time', ha='center')

    # Set the y-axis labels
    axs[0].set_ylabel('Amplitude')
    axs[1].set_ylabel('Amplitude')

    # Display the plot
    plt.show()


def print_channel_quality(args: Options, channels_quality: np.ndarray, probs: np.ndarray, frequencies: np.ndarray) -> None:
    for i, freq in enumerate(frequencies):
        index = np.argmax(probs[i])
        if index == 0:
            pred = 'video like interference'
        elif index == 1:
            pred = 'floor like interference'
        elif index == 2:
            pred = 'wireless lab. like interference'
        elif index == 3:
            pred = 'crypto/finance like interference'
        else:
            pred = 'jamming'

        if channels_quality[i] < args.threshold:
            print(freq, channels_quality[i], np.argmax(probs[i]), pred)
        else:
            print(freq, channels_quality[i], np.argmax(probs[i]), pred)


def trace_model(model):
    example_input = torch.rand(1, 15, 128)
    traced_model = torch.jit.trace(model, example_input)
    torch.jit.save(traced_model, "my_traced_model.pt")
