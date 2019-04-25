"""
==============================================================
Compute real-time power spectrum density with FieldTrip client
==============================================================

Please refer to `ftclient_rt_average.py` for instructions on
how to get the FieldTrip connector working in MNE-Python.

This example demonstrates how to use it for continuous
computation of power spectra in real-time using the
get_data_as_epoch function.

"""
# Author: Mainak Jas <mainak@neuro.hut.fi>
#
# License: BSD (3-clause)

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import time

import mne
from mne.realtime import FieldTripClient
from mne.time_frequency import psd_welch
from mne.utils import running_subprocess

print(__doc__)

# start a subprocess for neuromag2ft
data_path = mne.datasets.sample.data_path()

# user must provide list of bad channels because
# FieldTrip header object does not provide that
bads = ['MEG 2443', 'EEG 053']

fig, ax = plt.subplots(1)

speedup = 10
command = ["neuromag2ft", "--file",
           "{}/MEG/sample/sample_audvis_raw.fif".format(data_path),
           "--speed", str(speedup)]
with running_subprocess(command, after='terminate',
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    with FieldTripClient(host='localhost', port=1972,
                         tmax=10, wait_max=5) as rt_client:

        # get measurement info guessed by MNE-Python
        raw_info = rt_client.get_measurement_info()

        # select gradiometers
        picks = mne.pick_types(raw_info, meg='grad', eeg=False, eog=True,
                               stim=False, include=[], exclude=bads)

        n_fft = 256  # the FFT size. Ideally a power of 2
        n_samples = 2048  # time window on which to compute FFT

        # make sure at least one epoch is available
        time.sleep(n_samples / raw_info['sfreq'])

        for ii in range(5):
            epoch = rt_client.get_data_as_epoch(n_samples=n_samples,
                                                picks=picks)
            psd, freqs = psd_welch(epoch, fmin=2, fmax=200, n_fft=n_fft)

            cmap = 'RdBu_r'
            freq_mask = freqs < 150
            freqs = freqs[freq_mask]
            log_psd = 10 * np.log10(psd[0])

            tmin = epoch.events[0][0] / raw_info['sfreq']
            tmax = (epoch.events[0][0] + n_samples) / raw_info['sfreq']

            if ii == 0:
                im = ax.imshow(log_psd[:, freq_mask].T, aspect='auto',
                               origin='lower', cmap=cmap)

                ax.set_yticks(np.arange(0, len(freqs), 10))
                ax.set_yticklabels(freqs[::10].round(1))
                ax.set_xlabel('Frequency (Hz)')
                ax.set_xticks(np.arange(0, len(picks), 30))
                ax.set_xticklabels(picks[::30])
                ax.set_xlabel('MEG channel index')
                im.set_clim()
            else:
                im.set_data(log_psd[:, freq_mask].T)

            plt.title('continuous power spectrum (t = %0.2f sec to %0.2f sec)'
                      % (tmin, tmax), fontsize=10)

            plt.pause(0.5 / speedup)
