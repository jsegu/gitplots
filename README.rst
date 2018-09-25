.. Copyright (c) 2018, Julien Seguinot <seguinot@vaw.baug.ethz.ch>
.. GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)

Gitplots
========

A small script to plot comparative commit history across mutiple git
repositories, assuming the following directory structure::

   {gitroot}/{category}/{repository}

Requires matplotlib_ and pandas_.

Installation::

   pip install gitplots

Example usage::

   gitplots.py --gitroot {gitroot}
   gitplots.py --help

.. _matplotlib: https://matplotlib.org
.. _pandas: https://pandas.pydata.org
