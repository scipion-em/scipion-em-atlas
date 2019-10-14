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
import os
import re
from random import randrange
import xml.etree.ElementTree as ET

ATLAS_ATTR = "atlasLoc"
GRID_ = "GRID_"
GRIDSQUARE_MD = GRIDSQUARE_IMG = "GridSquare_"
TARGET_LOCATION_FILE_PATTERN = "TargetLocation_%s.dm"

def setAtlasToMovie(movie, atlasLocation):

    setattr(movie, ATLAS_ATTR, atlasLocation)


def getAtlasFromMovie(movie):

    return getattr(movie, ATLAS_ATTR, None)


class EPUParser:

    # EPU images name example:
    # GRID_05_DATA_Images - Disc1_GridSquare_1818984_DATA_FoilHole_2872127_Data_1821842_1821843_20190904_0831_Fractions_global_shifts.png
    def __init__(self, importPath):
        self._holesLocations = {}
        self.importPath = importPath

    def _getTargetLocationDmPath(self, atlasLocation):
        return os.path.join(self._getGridSquareMDFolder(atlasLocation),
                            TARGET_LOCATION_FILE_PATTERN % atlasLocation.hole)

    def _getCommonPathToAllGrids(self):

        return self.importPath.split(GRID_)[0]

    def _getGridFolder(self, atlasLocation):

        return os.path.join(self._getCommonPathToAllGrids(), GRID_ + atlasLocation.grid.get())

    def _getMetadataFolder(self, atlasLocation):

        return os.path.join(self._getGridFolder(atlasLocation), "DATA","Metadata")

    def _getGridSquareMDFolder(self, atlasLocation):

        return os.path.join(self._getMetadataFolder(atlasLocation), GRIDSQUARE_MD + atlasLocation.gridSquare.get())

    def decorateMovie(self, protImport, movie, atlasLocation):

        movieFn = movie.getFileName()

        matchingString = GRID_ + "(\d*)_.*_" + GRIDSQUARE_IMG + "(\d*)_.*_FoilHole_(\d*)"

        m = re.search(matchingString, movieFn)
        atlasLocation.grid.set(m.group(1))
        atlasLocation.gridSquare.set(m.group(2))
        atlasLocation.hole.set(m.group(3))
        x, y = self._getCoordinates(atlasLocation)
        atlasLocation.x.set(x)
        atlasLocation.y.set(y)

    def _getCoordinates(self, atlasLocation):

        holeId = atlasLocation.hole.get()

        if not self._holesLocations.has_key(holeId):
            self._holesLocations[holeId] = self.findCooordinatesFromHoleId(atlasLocation)

        return self._holesLocations[holeId]

    def findCooordinatesFromHoleId(self, atlasLocation):

        targetLocationMDfile = self._getTargetLocationDmPath(atlasLocation)

        # Open the medatata file, is an xml
        root = ET.parse(targetLocationMDfile).getroot()

        x = 0
        y = 0

        # Find the StagePosition element
        for element in root:
            if "StagePosition" in element.tag:

                # Get the coordinates
                for stageChild in element:

                    lastChar = stageChild.tag[-1]

                    # Assuming order
                    if "X" == lastChar:
                        x = stageChild.text
                    elif "Y" == lastChar:
                        y = stageChild.text
                        break

        return x,y

