# **************************************************************************
# *
# * Authors:   Pablo Conesa       (pconesa@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
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
from atlas.parsers import getAtlasFromMovie
from pyworkflow.gui.plotter import Plotter
from pyworkflow.viewer import Viewer
from pyworkflow.viewer import DESKTOP_TKINTER
from atlas.protocols import AtlasImporter
import numpy as np
             
class AtlasImporterViewer(Viewer):
    _environments = [DESKTOP_TKINTER]
    _targets = [AtlasImporter]
    
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

        #self.loadAtlasImg(plt)

        colors = ("cyan", "cyan", "cyan")
        area = np.pi * 3
        plotter.scatterP(x, y, s=area, c=colors, edgecolors='none', alpha=1)

        return plotter

    def loadAtlasImg(self, plt):

        # Load the atlas image
        # THis is hard coded. Need to find out how to relate atlas image to locations.
        img = Image.open('/extra/data/tests/atlas/GRID_05/ATLAS/Atlas_1.jpg')
        img = img.convert('L')
        img = img.point(lambda p: p * 1.5)
        extX = -0.0015
        extY = -0.00055
        #extX = 0.00078655919060111046
        #extY = 0.0050040725618600845
        extWidth = 0.002
        extent = [extX, extX + extWidth,
                  extY, extY + extWidth]
        plt.imshow(img, cmap='gray', extent=extent)

    def _getData(self, atlasProt):

        # We need to group data by grids
        # We will have a {"05": (x[],y[])
        grids = {}

        # Iterate the movies
        for movie in atlasProt.outputMovies.iterItems():
            atlasLoc = getAtlasFromMovie(movie)
            grid = atlasLoc.grid.get()

            if not grid in grids:
                grids[grid] = ([],[])

            x = grids[grid][0]
            y = grids[grid][1]

            x.append(atlasLoc.x.get())
            y.append(atlasLoc.y.get())

        # Create data
        return grids