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

class Collage:
    """ Class to create collages from images of same size.
    Indexes of columns and rows start at 1"""

    def __init__(self):
        self._image = None
        self._nextCoordX = 0
        self._nextCoordY = 0

    def addImageFn(self, imageFn, coord=None):
        """ Add an image (path to an image) to the collage
    :parameter imageFn: path to the image. Since using PIL internally has to be PIL compatible image
    :parameter coord: x,y tuple, if missing it will use own getNextCoord() value
    """
        # Read the new image
        newImage = Image.open(imageFn)

        self.addImage(newImage, coord)

    def addImage(self, newImage, coord=None):
        """ Adds a PIL image to the collage, if you have a filename use addImageFn()
    :parameter newImage: PIL image.
    :parameter coord: x,y tuple, if missing it will use own getNextCoord() value"""
        # If first image
        if self._image is None:
            # set the local image
            self._image = newImage
        else:
            if coord is None:
                coord = (self._nextCoordX, self._nextCoordY)
            # Paste it using coordinates
            # Since paste does not extend the image we need to create one
            width, height = self.getSize()

            # Get new image offset: size + coordinates
            newImageWith, newImageHeight = newImage.size
            newImageWith += coord[0]
            newImageHeight += coord[1]

            width = max(width, newImageWith)
            height = max(height, newImageHeight)

            # Create the new image extended in size
            newCollageImage = Image.new(self._image.mode, (width, height))
            newCollageImage.paste(self._image)
            newCollageImage.paste(newImage, coord)

            self._image = newCollageImage

        # Move nextCord
        self._moveNextCoord(newImage)

    def _moveNextCoord(self, img):
        """ Moves nextCoord to the right by img.width"""
        x, y = img.size
        self._nextCoordX += x

    def newLine(self):
        """ Moves nextCoord to the 0, bottom (height) coordinate"""
        x, y = self.getSize()
        self._nextCoordX = 0
        self._nextCoordY = y

    def getSize(self):
        """ Returns the current size of the collage"""
        return self._image.size if self._image is not None else (0,0)

    def getNextCoord(self):
        """ Returns the likely coordinates where the next image might be added
        For horizontal grow of the collage it will match image.width for x and y will be 0 unless
        newLine() is called

         :returns (x,y)  coordinates for the next image."""
        return self._nextCoordX, self._nextCoordY

    def save(self, file):
        """ Saves the collage to the file passed
        :parameter file:   A filename (string), pathlib.Path object or file object."""
        self._image.save(file)