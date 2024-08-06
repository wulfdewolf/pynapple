# -*- coding: utf-8 -*-
"""
Wavelet Transform
============
This tutorial demonstrates how we can use the signal processing tools within Pynapple to aid with data analysis.
We will examine the dataset from [Grosmark & Buzsáki (2016)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4919122/).

Specifically, we will examine Local Field Potential data from a period of active traversal of a linear track.

This tutorial was made by Kipp Freud.

"""


# %%
# !!! warning
#     This tutorial uses matplotlib for displaying the figure
#
#     You can install all with `pip install matplotlib requests tqdm seaborn`
#
#
# First, import the necessary libraries:
#
# mkdocs_gallery_thumbnail_number = 6

import math
import os

import matplotlib.pyplot as plt
import numpy as np
import requests
import seaborn
import tqdm

seaborn.set_theme()

import pynapple as nap

# %%
# ***
# Downloading the data
# ------------------
# Let's download the data and save it locally

path = "Achilles_10252013_EEG.nwb"
if path not in os.listdir("."):
    r = requests.get(f"https://osf.io/2dfvp/download", stream=True)
    block_size = 1024 * 1024
    with open(path, "wb") as f:
        for data in tqdm.tqdm(
            r.iter_content(block_size),
            unit="MB",
            unit_scale=True,
            total=math.ceil(int(r.headers.get("content-length", 0)) // block_size),
        ):
            f.write(data)


# %%
# ***
# Loading the data
# ------------------
# Let's load and print the full dataset.

data = nap.load_file(path)

print(data)

# %%
# First we can extract the data from the NWB. The local field potential has been downsampled to 1250Hz. We will call it `eeg`.
#
# The `time_support` of the object `data['position']` contains the interval for which the rat was running along the linear track. We will call it `wake_ep`.
#

FS = 1250

eeg = data["eeg"]

wake_ep = data["position"].time_support

# %%
# ***
# Selecting example
# -----------------------------------
# We will consider a single run of the experiment - where the rodent completes a full traversal of the linear track,
# followed by 4 seconds of post-traversal activity.

forward_ep = data["forward_ep"]
RUN_interval = nap.IntervalSet(forward_ep.start[7], forward_ep.end[7] + 4.0)

eeg_example = eeg.restrict(RUN_interval)[:, 0]
pos_example = data["position"].restrict(RUN_interval)

# %%
# ***
# Plotting the LFP and Behavioural Activity
# -----------------------------------

fig = plt.figure(constrained_layout=True, figsize=(10, 6))
axd = fig.subplot_mosaic(
    [["ephys"], ["pos"]],
    height_ratios=[1, 0.4],
)
axd["ephys"].plot(eeg_example, label="CA1")
axd["ephys"].set_title("EEG (1250 Hz)")
axd["ephys"].set_ylabel("LFP (a.u.)")
axd["ephys"].set_xlabel("time (s)")
axd["ephys"].margins(0)
axd["ephys"].legend()
axd["pos"].plot(pos_example, color="black")
axd["pos"].margins(0)
axd["pos"].set_xlabel("time (s)")
axd["pos"].set_ylabel("Linearized Position")
axd["pos"].set_xlim(RUN_interval[0, 0], RUN_interval[0, 1])


# %%
# ***
# Getting the LFP Spectrogram
# -----------------------------------
# Let's take the Fourier transform of our data to get an initial insight into the dominant frequencies during exploration (`wake_ep`).


power = nap.compute_power_spectral_density(eeg, fs=FS, ep=wake_ep, norm=True)

print(power)

# %%
# ***
# The returned object is a pandas dataframe which uses frequencies as indexes and spectral power as values.
#
# Let's plot the power between 1 and 100 Hz.

fig, ax = plt.subplots(1, constrained_layout=True, figsize=(10, 4))
ax.plot(
    np.abs(power[(power.index >= 1.0) & (power.index <= 100)]),
    alpha=0.5,
    label="LFP Frequency Power",
)
ax.axvspan(6, 10, color="red", alpha=0.1)
ax.set_xlabel("Freq (Hz)")
ax.set_ylabel("Frequency Power")
ax.set_title("LFP Fourier Decomposition")
ax.legend()


# %%
# The red area outlines the theta rhythm (6-10 Hz) which is proeminent in hippocampal LFP. 
# Hippocampal theta rhythm appears mostly when the animal is running. 
# (See Hasselmo, M. E., & Stern, C. E. (2014). Theta rhythm and the encoding and retrieval of space and time. Neuroimage, 85, 656-666.)
# We can check it here by separating `wake_ep` into `run_ep` and `rest_ep`.
run_ep = data['position'].dropna().find_support(1)
rest_ep = wake_ep.set_diff(run_ep)

# %%
# `run_ep` and `rest_ep` are IntervalSet with discontinuous epoch. 
# The function `nap.compute_power_spectral_density` takes signal with a single epoch to avoid artefacts between epochs jumps.
# To compare `run_ep` with `rest_ep`, we can use the function `nap.compute_mean_power_spectral_density` which avearge the FFT over multiple epochs of same duration. The parameter `interval_size` controls the duration of those epochs. 
# 
# In this case, `interval_size` is equal to 1.5 seconds. 

power_run = nap.compute_mean_power_spectral_density(eeg, 1.5, fs=FS, ep=run_ep, norm=True)
power_rest = nap.compute_mean_power_spectral_density(eeg, 1.5, fs=FS, ep=rest_ep, norm=True)

# %%
# `power_run` and `power_rest` are the power spectral density when the animal is respectively running and resting.

fig, ax = plt.subplots(1, constrained_layout=True, figsize=(10, 4))
ax.plot(
    np.abs(power_run[(power_run.index >= 3.0) & (power_run.index <= 30)]),
    alpha=1,
    label="Run",
    linewidth=2
)
ax.plot(
    np.abs(power_rest[(power_rest.index >= 3.0) & (power_rest.index <= 30)]),
    alpha=1,
    label="Rest",
    linewidth=2
)
ax.axvspan(6, 10, color="red", alpha=0.1)
ax.set_xlabel("Freq (Hz)")
ax.set_ylabel("Frequency Power")
ax.set_title("LFP Fourier Decomposition")
ax.legend()


# %%
# ***
# Getting the Wavelet Decomposition
# -----------------------------------
# Overall, the prominent frequencies in the data vary over time. The LFP characteristics may be different when the animal is running along the track, and when it is finished.
# Let's generate a wavelet decomposition to look more closely at the changing frequency powers over time.

# We must define the frequency set that we'd like to use for our decomposition
freqs = np.geomspace(3, 250, 100)

# %%
# Compute and print the wavelet transform on our LFP data

mwt_RUN = nap.compute_wavelet_transform(eeg_example, fs=FS, freqs=freqs)


# %%
# `mwt_RUN` is a TsdFrame with each column being the convolution with one wavelet at a particular frequency.
print(mwt_RUN)

# %%
# ***
# Now let's plot it.

fig = plt.figure(constrained_layout=True, figsize=(10, 6))
gs = plt.GridSpec(3, 1, figure=fig, height_ratios=[1.0, 0.5, 0.1])

ax0 = plt.subplot(gs[0, 0])
pcmesh = ax0.pcolormesh(mwt_RUN.t, freqs, np.transpose(np.abs(mwt_RUN)))
ax0.grid(False)
ax0.set_yscale("log")
ax0.set_title("Wavelet Decomposition")
ax0.set_ylabel("Frequency (Hz)")
cbar = plt.colorbar(pcmesh, ax=ax0, orientation="vertical")
ax0.set_ylabel("Amplitude")

ax1 = plt.subplot(gs[1, 0], sharex=ax0)
ax1.plot(eeg_example)
ax1.set_ylabel("LFP (v)")

ax1 = plt.subplot(gs[2, 0], sharex=ax0)
ax1.plot(pos_example, color="black")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Pos.")


# %%
# ***
# Visualizing Theta Band Power
# -----------------------------------
# There seems to be a strong theta frequency present in the data during the maze traversal.
# Let's plot the estimated 6-10Hz component of the wavelet decomposition on top of our data, and see how well they match up.

theta_freq_index = np.logical_and(freqs>6, freqs<10)


# Extract its real component, as well as its power envelope
theta_band_reconstruction = np.mean(mwt_RUN[:,theta_freq_index], 1)
theta_band_power_envelope = np.abs(theta_band_reconstruction)


# %%
# ***
# Now let's visualise the theta band component of the signal over time.

fig = plt.figure(constrained_layout=True, figsize=(10, 6))
gs = plt.GridSpec(2, 1, figure=fig, height_ratios=[1.0, 0.9])
ax0 = plt.subplot(gs[0,0])
ax0.plot(eeg_example, label="CA1")
ax0.set_title("EEG (1250 Hz)")
ax0.set_ylabel("LFP (a.u.)")
ax0.set_xlabel("time (s)")
ax0.legend()
ax1 = plt.subplot(gs[1,0])
ax1.plot(np.real(theta_band_reconstruction), label="6-10 Hz oscillations")
ax1.plot(theta_band_power_envelope, label="6-10 Hz power envelope")
ax1.set_xlabel("time (s)")
ax1.set_ylabel("Wavelet transform")
ax1.legend()

# %%
# ***
# Visualizing high frequency oscillation
# -----------------------------------
# There also seem to be peaks in the 200Hz frequency power after traversal of thew maze is complete. Here we use the interval (18356, 18357.5) seconds to zoom in.

zoom_ep = nap.IntervalSet(18356.0, 18357.5)

mwt_zoom = mwt_RUN.restrict(zoom_ep)

fig = plt.figure(constrained_layout=True, figsize=(10, 6))
gs = plt.GridSpec(2, 1, figure=fig, height_ratios=[1.0, 0.5])
ax0 = plt.subplot(gs[0, 0])
pcmesh = ax0.pcolormesh(mwt_zoom.t, freqs, np.transpose(np.abs(mwt_zoom)))
ax0.grid(False)
ax0.set_yscale("log")
ax0.set_title("Wavelet Decomposition")
ax0.set_ylabel("Frequency (Hz)")
cbar = plt.colorbar(pcmesh, ax=ax0, orientation="vertical")
ax0.set_label("Amplitude")

ax1 = plt.subplot(gs[1, 0], sharex=ax0)
ax1.plot(eeg_example.restrict(zoom_ep))
ax1.set_ylabel("LFP (a.u.)")
ax1.set_xlabel("Time (s)")

# %%
# Those events are called Sharp-waves ripples (See : Buzsáki, G. (2015). Hippocampal sharp wave‐ripple: A cognitive biomarker for episodic memory and planning. Hippocampus, 25(10), 1073-1188.)
#
# Among other methods, we can use the Wavelet decomposition to isolate them. In this case, we will look at the power of the wavelets for frequencies between 150 to 250 Hz.

ripple_freq_index = np.logical_and(freqs>150, freqs<250)

# %%
# We can compute the mean power for this frequency band.

ripple_power = np.mean(np.abs(mwt_RUN[:, ripple_freq_index]), 1)


# %%
# Now let's visualise the 150-250 Hz mean amplitude of the wavelet decomposition over time

fig = plt.figure(constrained_layout=True, figsize=(10, 5))
gs = plt.GridSpec(2, 1, figure=fig, height_ratios=[1.0, 0.5])
ax0 = plt.subplot(gs[0,0])
ax0.plot(eeg_example.restrict(zoom_ep), label="CA1")
ax0.set_ylabel("LFP (v)")
ax0.set_title(f"EEG (1250 Hz)")
ax1 = plt.subplot(gs[1,0])
ax1.legend()
ax1.plot(ripple_power.restrict(zoom_ep), label="150-250 Hz")
ax1.legend()
ax1.set_ylabel("Mean Amplitude")
ax1.set_xlabel("Time (s)")


# %%
# It is then easy to isolate ripple times by using the pynapple functions `smooth` and `threshold`. In the following lines, `ripples` is smoothed with a gaussian kernel of size 0.005 second and thesholded with a value of 100.
#

smoothed_ripple_power = ripple_power.smooth(0.005)

threshold_ripple_power = smoothed_ripple_power.threshold(100)

# %%
# `threshold_ripple_power` contains all the time points above 100. The ripple epochs are contained in the `time_support` of the threshold time series. Here we call it `rip_ep`.

rip_ep = threshold_ripple_power.time_support


# %%
# Now let's plot the ripples epoch as well as the smoothed ripple power.
#
# We can also plot `rip_ep` as vertical boxes to see if the detection is accurate

fig = plt.figure(constrained_layout=True, figsize=(10, 5))
gs = plt.GridSpec(2, 1, figure=fig, height_ratios=[1.0, 0.5])
ax0 = plt.subplot(gs[0,0])
ax0.plot(eeg_example.restrict(zoom_ep), label="CA1")
for s,e in rip_ep.intersect(zoom_ep).values:
    ax0.axvspan(s, e, color='red', alpha=0.1, ec=None)
ax0.set_ylabel("LFP (v)")
ax0.set_title(f"EEG (1250 Hz)")
ax1 = plt.subplot(gs[1,0])
ax1.legend()
ax1.plot(ripple_power.restrict(zoom_ep), label="150-250 Hz")
ax1.plot(smoothed_ripple_power.restrict(zoom_ep))
for s,e in rip_ep.intersect(zoom_ep).values:
    ax1.axvspan(s, e, color='red', alpha=0.1, ec=None)
ax1.legend()
ax1.set_ylabel("Mean Amplitude")
ax1.set_xlabel("Time (s)")


