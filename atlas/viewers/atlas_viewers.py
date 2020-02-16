# **************************************************************************
# *
# * Authors:   Pablo Conesa       (pconesa@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
from PIL import Image
import numpy as np

from pyworkflow.gui.plotter import Plotter
from pyworkflow.viewer import Viewer, DESKTOP_TKINTER

from ..parsers import getAtlasFromMovie
from ..protocols import AtlasEPUImporter

             
class AtlasImporterViewer(Viewer):
    _environments = [DESKTOP_TKINTER]
    _targets = [AtlasEPUImporter]
    
    def __init__(self, **kwargs):
        Viewer.__init__(self, **kwargs)

    def _visualize(self, atlasProt, **kwargs):

        grids = self._getData(atlasProt)

        for key, value in grids.items():

            yield self._plotGrid(key, value[0], value[1])

    def _plotGrid(self, grid, x, y):
        plotter = Plotter(windowTitle="Acquisitions for grid %s" % grid)

        plt = plotter.createSubPlot("Locations", "X", "Y")
        plt.axis('scaled')
        plt.autoscale(tight=True)

        self.loadAtlasImg(plt)

        colors = ("cyan", "cyan", "cyan")
        area = np.pi * 3
        plotter.scatterP(x, y, s=area, c=colors, edgecolors='none', alpha=1)

        return plotter

    def loadAtlasImg(self, plt):

        # Load the atlas image
        # This is hard coded. Need to find out how to relate atlas image to locations.
        img = Image.open(self.getAtlasImagePath())
        img = img.convert('L')
        img = img.point(lambda p: p * 1.5)
        extWidth = self.getAtlasPlotWidth()
        #extX = -0.0015
        #extY = -0.00055
        extX = self.convertUnits(-0.0010849264)
        extY = self.convertUnits(-0.00108488)
        #extY = extX = -extWidth/2

        extent = [extX, extX + extWidth,
                  extY, extY + extWidth]
        plt.imshow(img, cmap='gray', extent=extent)

    @staticmethod
    def convertUnits(value):
        """ To convert native units to visual units """
        # Units from dm files seems to be in meters, we are converting them to microns
        return value * 10**6

    def getAtlasPixelSize(self):

        # TODO: To get from Atlas_1.xml > MicroscopeImage > SpatialScale > pixelSize > x
        return self.convertUnits(5.30380813138737E-07)

    def getAtlasWidth(self):
        # TODO: Get it from the actual image
        return 4096

    def getAtlasImagePath(self):
        # TODO: get it right
        return '/extra/data/tests/atlas/GRID_05/ATLAS/Atlasmrc.jpg'

    def getAtlasPlotWidth(self):
        return self.getAtlasPixelSize() * self.getAtlasWidth()

    def _getData(self, atlasProt):

        # We need to group data by grids
        # We will have a {"05": (x[],y[])
        grids = {}

        # Iterate the movies
        for movie in atlasProt.outputMovies.iterItems():
            atlasLoc = getAtlasFromMovie(movie)
            grid = atlasLoc.grid.get()

            if grid not in grids:
                grids[grid] = ([], [])

            x = grids[grid][0]
            y = grids[grid][1]

            x.append(self.convertUnits(atlasLoc.x.get()))
            y.append(self.convertUnits(atlasLoc.y.get()))

        # Create data
        return grids
