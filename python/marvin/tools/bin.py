#!/usr/bin/env python
# encoding: utf-8
#
# bin.py
#
# Created by José Sánchez-Gallego on 6 Nov 2016.


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import warnings

from marvin.core.exceptions import MarvinError, MarvinUserWarning
from marvin.tools.maps import Maps, _is_MPL4
from marvin.tools.modelcube import ModelCube
from marvin.tools.spaxel import Spaxel


class Bin(object):

    def __init__(self, binid, **kwargs):

        self.plateifu = None
        self.mangaid = None

        self._maps, self._modelcube = self._get_dap_objects(**kwargs)
        self.binid = binid

        # Drops some keyword that could make spaxel load fail.
        kwargs.pop('bintype', None)
        kwargs.pop('mode', None)

        self._load_spaxels(**kwargs)
        self._load_data(**kwargs)

    def __repr__(self):
        return '<Marvin Bin (binid={0}, n_spaxels={1})>'.format(self.binid, len(self.spaxels))

    def _get_dap_objects(self, **kwargs):
        """Gets the Maps and ModelCube object."""

        try:
            kwargs_maps = kwargs.copy()
            kwargs_maps.pop('modelcube_filename', None)
            kwargs_maps['filename'] = kwargs_maps.pop('maps_filename', None)
            maps = Maps(**kwargs_maps)
        except MarvinError as ee:
            raise MarvinError('failed to open a Maps: {0}'.format(str(ee)))

        self.plateifu = maps.plateifu
        self.mangaid = maps.mangaid

        if _is_MPL4(maps._dapver):
            return maps, None

        try:
            kwargs_modelcube = kwargs.copy()
            kwargs_modelcube.pop('maps_filename', None)
            kwargs_modelcube['filename'] = kwargs_modelcube.pop('modelcube_filename', None)
            modelcube = ModelCube(**kwargs_modelcube)
        except Exception:
            warnings.warn('cannot open a ModelCube for this combination of '
                          'parameters. Some fetures will not be available.', MarvinUserWarning)
            modelcube = False

        return maps, modelcube

    def _load_spaxels(self, **kwargs):
        """Creates a list of unloaded spaxels for this binid."""

        load_spaxels = kwargs.pop('load_spaxels', False)

        self.spaxel_coords = self._maps.get_bin_spaxels(self.binid, only_list=True)

        if len(self.spaxel_coords) == 0:
            raise MarvinError('there are no spaxels associated with binid={0}.'.format(self.binid))
        else:

            if 'plateifu' not in kwargs:
                kwargs['plateifu'] = self._maps.plateifu

            modelcube_for_spaxel = False if not self._modelcube else self._modelcube.get_unbinned()
            self.spaxels = [Spaxel(x=cc[0], y=cc[1], cube=True, maps=self._maps.get_unbinned(),
                                   modelcube=modelcube_for_spaxel,
                                   load=load_spaxels,
                                   **kwargs)
                            for cc in self.spaxel_coords]

    def _load_data(self, **kwargs):
        """Loads one of the spaxels to get the DAP properties for the binid."""

        assert len(self.spaxel_coords) > 0

        sample_coords = self.spaxel_coords[0]

        if 'plateifu' not in kwargs:
            kwargs['plateifu'] = self._maps.plateifu

        sample_spaxel = Spaxel(x=sample_coords[0], y=sample_coords[1],
                               cube=True, maps=self._maps, modelcube=self._modelcube,
                               load=True, allow_binned=True, **kwargs)

        self.specres = sample_spaxel.specres
        self.specresd = sample_spaxel.specresd
        self.spectrum = sample_spaxel.spectrum
        self.properties = sample_spaxel.properties

        self.model_flux = sample_spaxel.model_flux
        self.redcorr = sample_spaxel.redcorr
        self.model = sample_spaxel.model
        self.emline = sample_spaxel.emline
        self.emline_base = sample_spaxel.emline_base
        self.stellar_continuum = sample_spaxel.stellar_continuum

    def load_all(self):
        """Loads all the spaxels that for this bin."""

        for spaxel in self.spaxels:
            spaxel.load()

        return
