#!/usr/bin/env python2

"""Plots from git logs."""

import os
import datetime
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('ggplot')
plt.rc('figure', figsize=(12, 9))


def get_date_counts(gitdir):
    """Return dates with at least one commit and corresponding commit freqency
    from given git repository."""

    # get timestamps using git log
    cmd = 'git --git-dir=%s log --format=%%at' % gitdir
    timestamps = subprocess.check_output(cmd.split(' '))
    timestamps = timestamps.split('\n')[:-1]
    timestamps = map(int, timestamps)

    # convert to dates and count commits per date
    dates = map(datetime.date.fromtimestamp, timestamps)
    try:  # faster but requires Numpy >= 1.9.0
        dates, counts = np.unique(dates, return_counts=True)
    except TypeError:  # works with Numpy < 1.9.0
        dates, counts = np.unique(dates, return_inverse=True)
        counts = np.bincount(counts)

    # return dates with commits and commit counts
    return dates, counts


def get_date_counts_series(gitdir):
    """Return dates with commits and commit freqency in a pandas data series.
    """

    # get dates and counts
    dates, counts = get_date_counts(gitdir)

    # convert to pandas dataseries
    dates = pd.DatetimeIndex(dates)
    ds = pd.Series(data=counts, index=dates, name=os.path.basename(gitdir))

    # return data series
    return ds


def get_date_counts_dataframe(gitroot):
    """Return dates with commits and commit frequency for each subdirectory of
    given directory in a pandas dataframe."""

    # find all subdirectories
    subdirs = os.listdir(gitroot)
    subdirs.sort()
    subdirs = [os.path.join(gitroot, d) for d in subdirs]

    # combined date counts series in dataframe
    df = pd.concat([get_date_counts_series(d) for d in subdirs], axis=1)

    # return resulting dataframe
    return df


def get_date_counts_multidataframe(gitroot):
    """Return dates with commits and commit frequency for each subsubdirectory
    of each subdirectory of the given directory in a pandas multi-indexed
    dataframe."""

    # find all subdirectories
    subdirs = os.listdir(gitroot)
    subdirs.sort()
    subdirpaths = [os.path.join(gitroot, d) for d in subdirs]

    # combined date counts series in dataframe
    df = pd.concat([get_date_counts_dataframe(d) for d in subdirpaths],
                   axis=1, keys=subdirs)

    # return resulting dataframe
    return df


def main():
    """Plot stacked commit frequency for each category."""

    # git root
    gitroot = '/home/juliens/git/'

    # other properties
    cmaps = ['Blues', 'Reds', 'Greens']

    # get commit counts
    df = get_date_counts_multidataframe(gitroot)
    df = df.resample('1M', how='sum')

    # initialize figure
    categories = df.columns.get_level_values(0).unique()
    fig, grid = plt.subplots(len(categories), 1, sharex=True)

    # plot counts from each category
    for i, cat in enumerate(categories):
        ax = grid[i]
        df[cat].plot(ax=ax, kind='area', cmap=cmaps[i])
        ax.set_ylabel('commits')
        ax.set_xlabel('date')
        ax.set_xlim('2012-01-01', '2016-01-01')

    # save
    fig.savefig('gitplots')

if __name__ == '__main__':
    main()
