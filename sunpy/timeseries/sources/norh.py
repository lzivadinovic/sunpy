"""Provides programs to process and analyse NoRH lightcurve data."""

from __future__ import absolute_import

import datetime
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt

from astropy.io import fits
import pandas

from sunpy.timeseries import GenericTimeSeries
from sunpy.time import parse_time
from astropy import units as u

from sunpy import config

TIME_FORMAT = config.get("general", "time_format")

__all__ = ['NoRHLightCurve']

class NoRHLightCurve(GenericTimeSeries):
    """
    Nobeyama Radioheliograph Correlation Lightcurve TimeSeries.

    Nobeyama Radioheliograph (NoRH) is a radio telescope dedicated to observing
    the Sun. It consists of 84 parabolic antennas with 80 cm diameter,
    sitting on lines of 490 m long in the east/west and of 220 m long in the north/south.
    It observes the full solar disk at 17 GHz and 34 GHz with a temporal resolution
    down to 0.1 second resolution (typically 1 s). It is located in Japan at
    `35.941667, 138.475833 <https://www.google.com/maps/place/Nobeyama+radio+observatory/@35.9410098,138.470243,14z/data=!4m2!3m1!1s0x0:0xe5a3821a5f6a3c4b>`_.

    Its first observation was in April, 1992 and daily 8-hour observations are
    available starting June, 1992.

    Examples
    --------
    >>> import sunpy.data.sample
    >>> import sunpy.timeseries
    >>> norh = sunpy.timeseries.TimeSeries(sunpy.data.sample.NORH_LIGHTCURVE, source='NoRH')
    >>> norh.peek()   # doctest: +SKIP

    References
    ----------
    * `Nobeyama Radioheliograph Homepage <http://solar.nro.nao.ac.jp/norh/>`_
    * `Analysis Manual <http://solar.nro.nao.ac.jp/norh/doc/manuale/index.html>`_
    * `Nobeyama Correlation Plots <http://solar.nro.nao.ac.jp/norh/html/cor_plot/>`_
    """

    def __init__(self, data, header, **kwargs):
        GenericTimeSeries.__init__(self, data, header, **kwargs)

        # Fill in some missing info
        self.meta['detector'] = ""
        self._nickname = self.detector
        #self.plot_settings['cmap'] = cm.get_cmap(self._get_cmap_name())
        #self.plot_settings['norm'] = ImageNormalize(stretch=visualization.AsinhStretch(0.01))

    def peek(self, **kwargs):
        """Plots the NoRH lightcurve TimeSeries

        .. plot::

            import sunpy.data.sample
            import sunpy.timeseries
            norh = sunpy.timeseries.TimeSeries(sunpy.data.sample.NORH_LIGHTCURVE, source='NoRH')
            norh.peek()

        Parameters
        ----------
        **kwargs : `dict`
            Any additional plot arguments that should be used when plotting.
        """

        plt.figure()
        axes = plt.gca()
        data_lab=self.meta['OBS-FREQ'][0:2] + ' ' + self.meta['OBS-FREQ'][2:5]
        axes.plot(self.data.index,self.data,label=data_lab)
        axes.set_yscale("log")
        axes.set_ylim(1e-4,1)
        axes.set_title('Nobeyama Radioheliograph')
        axes.set_xlabel('Start time: ' + self.data.index[0].strftime(TIME_FORMAT))
        axes.set_ylabel('Correlation')
        axes.legend()
        plt.show()

    @classmethod
    def _parse_file(cls, filepath):
        """This method parses NoRH tca and tcz correlation FITS files."""
        hdulist = fits.open(filepath)
        header = OrderedDict(hdulist[0].header)
        # For these NoRH files, the time series data is recorded in the primary
        # HDU
        data = hdulist[0].data

        # No explicit time array in FITS file, so construct the time array from
        # the FITS header
        obs_start_time=parse_time(header['DATE-OBS'] + 'T' + header['CRVAL1'])
        length = len(data)
        cadence = np.float(header['CDELT1'])
        sec_array = np.linspace(0, length-1, (length/cadence))

        norh_time = []
        for s in sec_array:
            norh_time.append(obs_start_time + datetime.timedelta(0,s))

        # Add the units data
        units = OrderedDict([('Correlation Coefficient', u.dimensionless_unscaled)])
        # Todo: check units used.
        return pandas.DataFrame(data, index=norh_time, columns=('Correlation Coefficient')), header, units

    @classmethod
    def is_datasource_for(cls, **kwargs):
        """Determines if header corresponds to a Nobeyama Radioheliograph Correlation lightcurve"""
        #return header.get('instrume', '').startswith('')
        return kwargs.get('source', '').startswith('NoRH')