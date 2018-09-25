#!/usr/bin/env python
# Copyright (c) 2015--2018, Julien Seguinot <seguinot@vaw.baug.ethz.ch>
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Plots from git logs.
"""

import os
import datetime
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# FIXME make these command-line options
plt.style.use('ggplot')
plt.rc('figure', figsize=(12.0, 9.0))
plt.rc('figure.subplot', left=0.0625, right=0.9375, bottom=0.0833, top=0.9166)
CMAP_CYCLE = ['Blues', 'Oranges', 'Greens', 'Reds', 'Purples', 'Greys']


def is_git_repo(directory):
    """Check if directory is a git repository."""
    cmd = ['git', '-C', directory, 'log', '-0']
    with open(os.devnull, 'w') as null:
        code = subprocess.call(cmd, stdout=null, stderr=null)
    return code == 0


def get_date_counts(gitdir):
    """Return dates with at least one commit and corresponding commit freqency
    from given git repository."""

    # get timestamps using git log
    cmd = 'git -C %s log --format=%%at' % gitdir
    timestamps = subprocess.check_output(cmd.split(' ')).decode('ascii')
    timestamps = timestamps.split('\n')[:-1]
    timestamps = list(map(int, timestamps))

    # convert to dates and count commits per date
    dates = list(map(datetime.date.fromtimestamp, timestamps))
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
    counts = pd.Series(data=counts, index=dates, name=os.path.basename(gitdir))

    # return data series
    return counts


def get_date_counts_dataframe(gitroot):
    """Return dates with commits and commit frequency for each subdirectory of
    given directory in a pandas dataframe."""

    # find all git repositories
    subdirs = os.listdir(gitroot)
    subdirs.sort()
    subdirs = [os.path.join(gitroot, d) for d in subdirs]
    subdirs = [d for d in subdirs if os.path.isdir(d)]
    subdirs = [d for d in subdirs if is_git_repo(d)]

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


def get_random_dataframe():
    """Return random dates and commit frequency in a pandas dataframe."""

    # generate random data
    numdirs = np.random.randint(2, 7)
    subdirs = ['repo{}'.format(i+1) for i in range(numdirs)]
    dates = pd.date_range('2001-01-01', '2006-12-31')
    counts = np.random.rand(len(dates), len(subdirs))
    counts = (1/counts).astype(int)
    df = pd.DataFrame(columns=subdirs, index=dates, data=counts)

    # return resulting dataframe
    return df


def get_random_multidataframe():
    """Return dates and commit frequency in a pandas multi-indexed
    dataframe."""

    # concatenate random data
    numdirs = np.random.randint(2, 7)
    subdirs = ['cat{}'.format(i+1) for i in range(numdirs)]
    df = pd.concat([get_random_dataframe() for d in subdirs],
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
            commits.plot(ax=ax, kind='area', cmap=CMAP_CYCLE[i])
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
        df[cat].sum().plot(ax=ax, kind='pie', cmap=CMAP_CYCLE[i],
                           startangle=90, autopct='%.1f%%',
                           labeldistance=99, legend=False)
        ax.set_ylabel('')
        ax.set_title(cat)
        if ax.get_legend_handles_labels() != ([], []):
            ax.legend(loc='upper left').get_frame().set_alpha(0.5)

    # return entire figure
    return fig


def main():
    """Main program called upon execution."""

    import argparse

    parser = argparse.ArgumentParser(description='Plots from git logs.')
    parser.add_argument('-g', '--gitroot', metavar='DIR', default='~/git',
                        help="""directory containing git repositories
                                (default: %(default)s)""")
    parser.add_argument('-p', '--plotdir', metavar='DIR', default='.',
                        help="""directory where to save plots
                                (default: %(default)s)""")
    parser.add_argument('-s', '--subdirs', metavar='DIR', nargs='+',
                        help="""subdirectories (categories) to plot
                                (default: all)""")
    parser.add_argument('-t', '--test', action='store_true',
                        help="""generate random commit history""")
    args = parser.parse_args()

    # paths to directories
    gitroot = os.path.expanduser(args.gitroot)
    plotdir = os.path.expanduser(args.plotdir)
    subdirs = args.subdirs

    # output prefix
    prefix = os.path.join(plotdir, 'gitplot_')

    # time spans and frequencies for plots
    freqs = {'lt': '1M', 'mt': '1W', 'st': '1D'}

    # get commit counts
    if args.test is True:
        df = get_random_multidataframe()
    else:
        df = get_date_counts_multidataframe(gitroot, subdirs=subdirs)

    # plot
    for term in ['lt', 'mt', 'st']:
        subdf = df.resample(freqs[term]).sum().tail(50)
        plot_area(subdf).savefig(prefix + 'area_%s' % term)
        plot_pies(subdf).savefig(prefix + 'pies_%s' % term)


if __name__ == '__main__':
    main()
