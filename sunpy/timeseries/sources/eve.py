# -*- coding: utf-8 -*-
"""Provides programs to process and analyze EVE data."""
from __future__ import absolute_import

import os
import numpy
from datetime import datetime
from collections import OrderedDict

import matplotlib.pyplot as plt
from pandas.io.parsers import read_csv
from os.path import basename

from sunpy.timeseries import GenericTimeSeries
from astropy import units as u

__all__ = ['EVELightCurve']


class EVELightCurve(GenericTimeSeries):
    """
    SDO EVE LightCurve for level 0CS data.

    The Extreme Ultraviolet Variability Experiment (EVE) is an instrument on board
    the Solar Dynamics Observatory (SDO). The EVE instrument is designed to
    measure the solar extreme ultraviolet (EUV) irradiance. The EUV radiation
    includes the 0.1-105 nm range, which provides the majority of the energy
    for heating Earth’s thermosphere and creating Earth’s ionosphere (charged plasma).

    EVE includes several irradiance instruments: The Multiple EUV Grating
    Spectrographs (MEGS)-A is a grazing- incidence spectrograph that measures
    the solar EUV irradiance in the 5 to 37 nm range with 0.1-nm resolution,
    and the MEGS-B is a normal-incidence, dual-pass spectrograph that measures
    the solar EUV irradiance in the 35 to 105 nm range with 0.1-nm resolution.

    Level 0CS data is primarily used for space weather. It is provided near
    real-time and is crudely calibrated 1-minute averaged broadband irradiances
    from ESP and MEGS-P broadband.

    Data is available starting on 2010/03/01.

    Examples
    --------
    >>> import sunpy.timeseries
    >>> import sunpy.data.sample

    >>> eve = sunpy.timeseries.TimeSeries(sunpy.data.sample.EVE_LIGHTCURVE, source='EVE')
    >>> eve = sunpy.timeseries.TimeSeries("http://lasp.colorado.edu/eve/data_access/quicklook/quicklook_data/L0CS/LATEST_EVE_L0CS_DIODES_1m.txt", source='EVE')
    >>> eve.peek(subplots=True)    # doctest: +SKIP

    References
    ----------
    * `SDO Mission Homepage <http://sdo.gsfc.nasa.gov>`_
    * `EVE Homepage <http://lasp.colorado.edu/home/eve/>`_
    * `Level 0CS Definition <http://lasp.colorado.edu/home/eve/data/>`_
    * `EVE Data Acess <http://lasp.colorado.edu/home/eve/data/data-access/>`_
    * `Instrument Paper <http://link.springer.com/article/10.1007%2Fs11207-009-9487-6>`_
    """

    def peek(self, column=None, **kwargs):
        """Plots the time series in a new figure. An example is shown below.

        .. plot::

           import sunpy.timeseries
            from sunpy.data.sample import EVE_LIGHTCURVE
            eve = sunpy.timeseries.TimeSeries(EVE_LIGHTCURVE)
            eve.peek(subplots=True)

        Parameters
        ----------
        column : `str`
            The column to display. If None displays all.

        **kwargs : `dict`
            Any additional plot arguments that should be used
            when plotting.

        Returns
        -------
        fig : `~matplotlib.Figure`
            A plot figure.
        """
        figure = plt.figure()
        # Choose title if none was specified
        if "title" not in kwargs and column is None:
            if len(self.data.columns) > 1:
                kwargs['title'] = 'EVE (1 minute data)'
            else:
                if self._filename is not None:
                    base = self._filename.replace('_', ' ')
                    kwargs['title'] = os.path.splitext(base)[0]
                else:
                    kwargs['title'] = 'EVE Averages'

        if column is None:
            self.plot(**kwargs)
        else:
            data = self.data[column]
            if "title" not in kwargs:
                kwargs['title'] = 'EVE ' + column.replace('_', ' ')
            data.plot(**kwargs)
        figure.show()
        return figure

    @classmethod
    def _parse_file(cls, filepath):
        """Parses an EVE CSV file."""
        print('\nin _parse_file()')
        cls._filename = basename(filepath)
        with open(filepath, 'rb') as fp:
            # Determine type of EVE CSV file and parse
            line1 = fp.readline()
            fp.seek(0)

            if line1.startswith("Date".encode('ascii')):
                return cls._parse_average_csv(fp)
                print('Out of _parse_average_csv()\n')
            elif line1.startswith(";".encode('ascii')):
                return cls._parse_level_0cs(fp)
                print('Out of _parse_level_0cs()\n')

    @staticmethod
    def _parse_average_csv(fp):
        """Parses an EVE Averages file."""
        print('\nin _parse_average_csv()')
        return "", read_csv(fp, sep=",", index_col=0, parse_dates=True)

    @staticmethod
    def _parse_level_0cs(fp):
        """Parses and EVE Level 0CS file."""
        print('\nstart _parse_level_0cs()')
        is_missing_data = False      #boolean to check for missing data
        missing_data_val = numpy.nan
        header = []
        fields = []
        line = fp.readline()
        # Read header at top of file
        while line.startswith(";".encode('ascii')):
            header.append(line)
            if '; Missing data:'.encode('ascii') in line :
                is_missing_data = True
                missing_data_val = line.split(':'.encode('ascii'))[1].strip()

            line = fp.readline()

        meta = OrderedDict()
        for hline in header :
            if hline == '; Format:\n'.encode('ascii') or hline == '; Column descriptions:\n'.encode('ascii'):
                continue
            elif ('Created'.encode('ascii') in hline) or ('Source'.encode('ascii') in hline):
                meta[hline.split(':'.encode('ascii'),
                                 1)[0].replace(';'.encode('ascii'),
                                               ' '.encode('ascii')).strip()] = hline.split(':'.encode('ascii'), 1)[1].strip()
            elif ':'.encode('ascii') in hline :
                meta[hline.split(':'.encode('ascii'))[0].replace(';'.encode('ascii'), ' '.encode('ascii')).strip()] = hline.split(':'.encode('ascii'))[1].strip()

        fieldnames_start = False
        for hline in header:
            if hline.startswith("; Format:".encode('ascii')):
                fieldnames_start = False
            if fieldnames_start:
                fields.append(hline.split(":".encode('ascii'))[0].replace(';'.encode('ascii'), ' '.encode('ascii')).strip())
            if hline.startswith("; Column descriptions:".encode('ascii')):
                fieldnames_start = True

        # Next line is YYYY DOY MM DD
        date_parts = line.split(" ".encode('ascii'))

        year = int(date_parts[0])
        month = int(date_parts[2])
        day = int(date_parts[3])
        #last_pos = fp.tell()
        #line = fp.readline()
        #el = line.split()
        #len

        # function to parse date column (HHMM)
        parser = lambda x: datetime(year, month, day, int(x[0:2]), int(x[2:4]))

        data = read_csv(fp, sep="\s*".encode('ascii'), names=fields, index_col=0, date_parser=parser, header=None, engine='python')
        if is_missing_data :   #If missing data specified in header
            data[data == float(missing_data_val)] = numpy.nan
            
        # Add the units data
        units = OrderedDict([(b'XRS-B proxy', u.dimensionless_unscaled),
                             (b'XRS-A proxy', u.dimensionless_unscaled),
                             (b'SEM proxy', u.dimensionless_unscaled),
                             (b'0.1-7ESPquad', u.W/u.m**2),
                             (b'17.1ESP', u.W/u.m**2),
                             (b'25.7ESP', u.W/u.m**2),
                             (b'30.4ESP', u.W/u.m**2),
                             (b'36.6ESP', u.W/u.m**2),
                             (b'darkESP', u.ct),
                             (b'121.6MEGS-P', u.W/u.m**2),
                             (b'darkMEGS-P', u.ct),
                             (b'q0ESP', u.dimensionless_unscaled),
                             (b'q1ESP', u.dimensionless_unscaled),
                             (b'q2ESP', u.dimensionless_unscaled),
                             (b'q3ESP', u.dimensionless_unscaled),
                             (b'CMLat', u.W/u.m**2),
                             (b'CMLon', u.W/u.m**2)])
        # Todo: check units used.
        return data, meta, units

    @classmethod
    def is_datasource_for(cls, **kwargs):
        """Determines if header corresponds to an EVE image"""
        #return header.get('instrume', '').startswith('')
        return kwargs.get('source', '').startswith('EVE')