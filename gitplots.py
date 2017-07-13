#!/usr/bin/env python2

"""Plots from git logs."""

import os
import argparse
import datetime
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.style.use('ggplot')
cmap_cycle = ['Blues', 'Oranges', 'Greens', 'Reds', 'Purples', 'Greys']


def get_date_counts(gitdir):
    """Return dates with at least one commit and corresponding commit freqency
    from given git repository."""

    # get timestamps using git log
    cmd = 'git -C %s log --format=%%at' % gitdir
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
    subdirs = [d for d in subdirs if os.path.isdir(d)]

    # combined date counts series in dataframe
    df = pd.concat([get_date_counts_series(d) for d in subdirs], axis=1)

    # return resulting dataframe
    return df


def get_date_counts_multidataframe(gitroot, subdirs=None):
    """Return dates with commits and commit frequency for each subsubdirectory
    of each subdirectory of the given directory in a pandas multi-indexed
    dataframe."""

    # find all subdirectories
    if subdirs is None:
        subdirs = os.listdir(gitroot)
        subdirs.sort()
    subdirpaths = [os.path.join(gitroot, d) for d in subdirs]

    # combined date counts series in dataframe
    df = pd.concat([get_date_counts_dataframe(d) for d in subdirpaths],
                   axis=1, keys=subdirs)

    # return resulting dataframe
    return df


def plot_area(df):
    """Plot stacked commit frequency for each category."""

    # initialize figure
    categories = df.columns.get_level_values(0).unique()
    fig, grid = plt.subplots(len(categories), 1, sharex=True, squeeze=False)

    # plot counts from each category
    for i, cat in enumerate(categories):
        ax = grid.flat[i]
        ax.set_ylabel('commits')
        ax.set_xlabel('date')
        commits = df[cat].dropna(axis=1, how='all')
        if not commits.empty:
            commits.plot(ax=ax, kind='area', cmap=cmap_cycle[i])
            ax.legend(loc='upper left').get_frame().set_alpha(0.5)

    # return entire figure
    return fig


def plot_pies(df):
    """Plot pie chart of commit frequency for each category."""

    # initialize figure
    categories = df.columns.get_level_values(0).unique()
    fig, grid = plt.subplots(1, len(categories), sharex=True, squeeze=False)

    # plot counts from each category
    for i, cat in enumerate(categories):
        ax = grid.flat[i]
        ax.set_aspect('equal')
        df[cat].sum().plot(ax=ax, kind='pie', cmap=cmap_cycle[i],
                               startangle=90, autopct='%.1f%%',
                               labeldistance=99, legend=False)
        ax.set_ylabel('')
        ax.set_title(cat)
        if ax.get_legend_handles_labels() != ([], []):
            ax.legend(loc='upper left').get_frame().set_alpha(0.5)

    # return entire figure
    return fig


if __name__ == '__main__':
    """Main program called upon execution."""
    parser = argparse.ArgumentParser(description='Plots from git logs.')
    parser.add_argument('-g', '--gitroot', metavar='DIR', default='~/git',
                        help="""directory containing git repositories
                                (default: %(default)s)""")
    parser.add_argument('-s', '--subdirs', metavar='DIR', default=None, nargs='+',
                        help="""subdirectories (categories) to plot
                                (default: all)""")
    args = parser.parse_args()

    # git root
    gitroot = os.path.expanduser(args.gitroot)
    subdirs = args.subdirs

    # time spans and frequencies for plots
    today = pd.to_datetime('today')
    freqs = {'lt': '1M', 'mt': '1W', 'st': '1D'}

    # get commit counts
    df = get_date_counts_multidataframe(gitroot, subdirs=subdirs)

    # plot
    for term in ['lt', 'mt', 'st']:
        subdf = df.resample(freqs[term]).sum().tail(50)
        plot_area(subdf).savefig('gitplot_area_%s' % term)
        plot_pies(subdf).savefig('gitplot_pies_%s' % term)
