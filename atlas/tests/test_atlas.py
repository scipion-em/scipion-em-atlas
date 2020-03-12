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

from pwem.objects import Movie, Pointer
from pwem.protocols import ProtImportMovies
from pyworkflow.tests import BaseTest, DataSet, setupTestProject

from atlas.parsers import EPUParser, GRID_, GRIDSQUARE_MD, \
    TARGET_LOCATION_FILE_PATTERN


# Define new dataset here
from atlas.protocols import AtlasEPUImporter

DataSet(name='atlas', folder='atlas',
        files={
               'root': '',
               'importPath': 'GRID_??/DATA/Images-Disc1/GridSquare_*/Data'
                })


class MockImport:

    def __init__(self, fileName="foo"):

        self.fileName = fileName

    def iterFiles(self):

        yield self.fileName, "id"

class TestAtlas(BaseTest):
    """ Test most basic elements """

    @classmethod
    def setUpClass(cls):
        cls.dataset = DataSet.getDataSet('atlas')
        setupTestProject(cls)

    def test_FEIImporter(self):

        importArgs = {
            'objLabel': 'movies with atlas info',
            'importFrom': ProtImportMovies.IMPORT_FROM_FILES,
            'filesPath': self.dataset.getFile('importPath'),
            'filesPattern': "*_Fractions.mrc",
            'amplitudConstrast': 0.1,
            'sphericalAberration': 2.,
            'voltage': 300,
            'samplingRate': 3.54
            }

        importMovies = self.newProtocol(ProtImportMovies, **importArgs)

        self.launchProtocol(importMovies)

        atlasProt = self.newProtocol(AtlasEPUImporter)

        atlasProt.importProtocol = Pointer(importMovies)

        self.launchProtocol(atlasProt)

    def test_FEIParser(self):

        protImport = MockImport()

        # Test movie decoration
        commonPath = self.dataset.getFile('root')

        epuParser = EPUParser(self.dataset.getFile('importPath'))

        movie = Movie("GRID_05_DATA_Images - Disc1_GridSquare_1818984_DATA_FoilHole_2872127_Data_1821842_1821843_20190904_0831_Fractions_global_shifts.mrc")
        atlasLoc = epuParser.getAtlasLocation(protImport, movie)

        self.assertEqual(atlasLoc.grid.get(), "05")
        self.assertEqual(atlasLoc.gridSquare.get(), "1818984")
        self.assertEqual(atlasLoc.hole.get(), "2872127")
        self.assertIsNotNone(atlasLoc.x.get())
        self.assertIsNotNone(atlasLoc.y.get())

        # Get X and Y
        x = atlasLoc.x.get()
        y = atlasLoc.y.get()

        self.assertEqual(len(epuParser._holesLocations), 1, "Hole location not cached")

        atlasLoc = epuParser.getAtlasLocation(protImport, movie)


        self.assertEqual(len(epuParser._holesLocations), 1, "Hole location wrongly increased")
        self.assertEqual(atlasLoc.x.get(), x, "X value does not match")
        self.assertEqual(atlasLoc.y.get(), y, "Y value does not match")

        # Test common path to all grids
        self.assertEqual(epuParser._getCommonPathToAllGrids(),
                         commonPath, "Common path to grids is wrong.")

        self.assertEqual(epuParser._getGridFolder(atlasLoc),
                         os.path.join(commonPath, GRID_ + atlasLoc.grid.get()),
                         "Grid folder is wrong.")

        self.assertEqual(epuParser._getMetadataFolder(atlasLoc),
                         os.path.join(commonPath, GRID_ + atlasLoc.grid.get(), "DATA", "Metadata"),
                         "Metadata folder is wrong.")

        # Test GridSquare metadata folder
        self.assertEqual(epuParser._getGridSquareMDFolder(atlasLoc),
                         os.path.join(epuParser._getMetadataFolder(atlasLoc),  GRIDSQUARE_MD + atlasLoc.gridSquare.get()),
                         "GridSquare metadata folder is wrong.")

        # Test TargetLocationFile metadata file
        self.assertEqual(epuParser._getTargetLocationDmPath(atlasLoc),
                         os.path.join(epuParser._getGridSquareMDFolder(atlasLoc),  TARGET_LOCATION_FILE_PATTERN % atlasLoc.hole.get()),
                         "GridSquare metadata folder is wrong.")



