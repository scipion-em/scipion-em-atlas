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
import os
import tempfile

from PIL import Image
from atlas.collage import Collage
from pwem.objects import Movie, Pointer
from pwem.protocols import ProtImportMovies
from pyworkflow.tests import BaseTest, DataSet, setupTestProject

from ..parsers import EPUParser, GRID_, GRIDSQUARE_MD, \
    TARGET_LOCATION_FILE_PATTERN


# Define new dataset here
from ..protocols import AtlasEPUImporter

class DSKeys:
    ROOT = 'root'
    IMPORTPATH = 'importPath'
    TILEIMAGE1 = 'tileImage1'
    TILEIMAGE2 = 'tileImage2'
    TILE1DM = 'tile1dm'
    TILEMRC1= 'mrc1'
    ATLAS_DIR='atlasdir'

ATLAS_FOLDER = 'GRID_05/ATLAS'

DataSet(name='atlas', folder='atlas',
        files={
            DSKeys.ROOT: '',
            DSKeys.IMPORTPATH: 'GRID_??/DATA/Images-Disc1/GridSquare_*/Data',
            DSKeys.ATLAS_DIR: ATLAS_FOLDER,
            DSKeys.TILEIMAGE1: os.path.join(ATLAS_FOLDER,'Tile_1818556_1_1.jpg'),
            DSKeys.TILEIMAGE2: os.path.join(ATLAS_FOLDER,'Tile_1818512_0_1.jpg'),
            DSKeys.TILE1DM: os.path.join(ATLAS_FOLDER,'Tile_1818512_0_1.dm'),
            DSKeys.TILEMRC1: os.path.join(ATLAS_FOLDER,'Tile_1818512_0_1.mrc'),
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

        movie = Movie("GRID_05_DATA_Images - Disc1_GridSquare_1818577_DATA_FoilHole_1821393_Data_1821842_1821843_20190904_0831_Fractions_global_shifts.mrc")
        atlasLoc = epuParser.getAtlasLocation(protImport, movie)

        self.assertEqual(atlasLoc.grid.get(), "05")
        self.assertEqual(atlasLoc.gridSquare.get(), "1818577")
        self.assertEqual(atlasLoc.hole.get(), "1821393")
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


    def test_collage(self):
        """ Tests basic collage composition"""
        collage = Collage()

        # Create a 2x2 pixel image
        img = Image.new(mode="RGB", size=(2,2), color=(255, 255, 255))
        collage.addImage(img)

        # Create a 2x2 pixel image
        img = Image.new(mode="RGB", size=(2, 2), color=(200, 200, 200))
        collage.addImage(img)

        self.assertEqual(collage.getSize(), (4, 2), "Collage wrong growth on X")

        # Create a 2x2 pixel image
        img = Image.new(mode="RGB", size=(2, 2), color=(100, 100, 100))
        collage.newLine()
        collage.addImage(img)

        self.assertEqual(collage.getSize(), (4, 4), "Collage wrong growth on Y after newLine")

        # Get a temporary filename
        collageFn = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        print("Collage file %s" % collageFn.name)
        collage.save(collageFn)

        # Assertions
        img = Image.open(collageFn)
        self.assertEqual((4,4), img.size, "Wrong collage size when using 4 2x2 PIL images without coordinates")

    def test_collage_with_coords(self):
        """ Tests basic collage composition"""
        collage = Collage()

        # Create a 2x2 pixel image
        img = Image.new(mode="RGB", size=(2,2), color=(255, 255, 255))
        collage.addImage(img)

        # Create a 2x2 pixel image
        img = Image.new(mode="RGB", size=(2, 2), color=(200, 200, 200))
        # Add it with coordinates
        collage.addImage(img, (1, 1))

        self.assertEqual(collage.getSize(), (3, 3), "Collage wrong growth when using coordinates")

        # Get a temporary filename
        collageFn = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        print("Collage with coordinates file %s" % collageFn.name)
        collage.save(collageFn)

        # Assertions
        img = Image.open(collageFn)
        self.assertEqual((3,3), img.size, "Wrong collage size when using 2 2x2 PIL images with coordinates")

    def test_collage_with_tiles(self):

        collage = Collage()

        # Add one tile
        collage.addImageFn(self.dataset.getFile(DSKeys.TILEIMAGE1))
        collage.addImageFn(self.dataset.getFile(DSKeys.TILEIMAGE2))

        # Get a temporary filename
        collageFn = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        print("Tiles collage file at %s" % collageFn.name)
        collage.save(collageFn)

        # Assertions
        img = Image.open(collageFn)
        self.assertEqual((512*2, 512), img.size, "Wrong collage size when using atlas jpg as tiles")
    def test_tile_parsing(self):

        # Get x and y of the tile, base on the dm file
        h, w, x,y = EPUParser.getTileCoordinates(self.dataset.getFile(DSKeys.TILE1DM))

        self.assertEqual((h, w, x, y), (907, 907, 1592,1592), 'Tile coordinates extraction is wrong')

    def test_tile_mrc_to_jpg(self):

        # Get a temporary filename
        tileJpg = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)

        EPUParser.convertMrc2Jpg(self.dataset.getFile(DSKeys.TILEMRC1), tileJpg.name)

        print("MRC tile converted to jpg at %s" % tileJpg.name)

        # Assertions
        img = Image.open(tileJpg)
        self.assertEqual((4096 , 4096), img.size, "Wrong collage size when using atlas jpg as tiles")

    def test_createHRAtlas(self):

        # Get a temporary filename
        fullAtlasJpg = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)

        EPUParser.createHRAtlas(self.dataset.getFile(DSKeys.ATLAS_DIR), fullAtlasJpg.name)

        print("Full JPG atlas at %s" % fullAtlasJpg.name)

        # Assertions
        img = Image.open(fullAtlasJpg)

        ratio = 4096/907
        expectedDimensions = int(3184 * ratio) + 4096

        self.assertEqual((expectedDimensions, expectedDimensions), img.size, "Wrong collage size when using atlas jpg as tiles")