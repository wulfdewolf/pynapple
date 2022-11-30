"""Tests of randomize for `pynapple` package."""

import pynapple as nap
import numpy as np
import pandas as pd
import pytest


def test_shift_ts():
    ts = nap.Ts(t=np.arange(0, 100))
    shift_ts = nap.randomize.shift_timestamps(ts,min_shift=0.1,max_shift=0.2)

    assert isinstance(shift_ts,nap.Ts)
    assert len(ts) == len(shift_ts)
    assert (ts.time_support.values == shift_ts.time_support.values).all()


def test_shift_tsgroup():
    tsgroup = nap.TsGroup(
        {0: nap.Ts(t=np.arange(0, 100)), 1: nap.Ts(t=np.arange(0, 200))}
    )
    shift_tsgroup = nap.randomize.shift_timestamps(tsgroup,min_shift=0.1,max_shift=0.2)

    assert isinstance(shift_tsgroup,nap.TsGroup)
    assert len(tsgroup) == len(shift_tsgroup)
    assert (tsgroup.time_support.values == shift_tsgroup.time_support.values).all()

    for j,k in zip(tsgroup.keys(),shift_tsgroup.keys()):
        assert j == k
        assert len(tsgroup[j]) == len(shift_tsgroup[k])


def test_jitter_ts():
    ts = nap.Ts(t=np.arange(0, 100))
    jitter_ts = nap.randomize.jitter_timestamps(ts,min_jitter=0.01,max_jitter=0.1)

    assert isinstance(jitter_ts,nap.Ts)
    assert len(ts) == len(jitter_ts)


def test_jitter_tsgroup():
    tsgroup = nap.TsGroup(
        {0: nap.Ts(t=np.arange(0, 100)), 1: nap.Ts(t=np.arange(0, 200))}
    )
    jitter_tsgroup = nap.randomize.jitter_timestamps(tsgroup,min_jitter=0.01,max_jitter=0.1)

    assert isinstance(jitter_tsgroup,nap.TsGroup)
    assert len(tsgroup) == len(jitter_tsgroup)

    for j,k in zip(tsgroup.keys(),jitter_tsgroup.keys()):
        assert j == k
        assert len(tsgroup[j]) == len(jitter_tsgroup[k])


def test_resample_ts():
    ts = nap.Ts(t=np.arange(0, 100))
    resampled_ts = nap.randomize.resample_timestamps(ts)

    assert len(ts) == len(resampled_ts)
    assert isinstance(resampled_ts,nap.Ts)
    assert (ts.time_support.values == resampled_ts.time_support.values).all()


def test_resample_tsgroup():
    tsgroup = nap.TsGroup(
        {0: nap.Ts(t=np.arange(0, 100)), 1: nap.Ts(t=np.arange(0, 200))}
    )
    resampled_tsgroup = nap.randomize.resample_timestamps(tsgroup)

    assert isinstance(resampled_tsgroup,nap.TsGroup)
    assert len(tsgroup) == len(resampled_tsgroup)
    assert (tsgroup.time_support.values == resampled_tsgroup.time_support.values).all()

    for j,k in zip(tsgroup.keys(),resampled_tsgroup.keys()):
        assert j == k
        assert len(tsgroup[j]) == len(resampled_tsgroup[k])
