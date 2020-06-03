# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Pablo Conesa (pconesa@cnb.csic.es)
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
import datetime
import os

from pwem.objects import Movie, Acquisition
from pwem.protocols import EMProtocol
from pyworkflow.mapper.sqlite import ID
from pyworkflow.protocol import Protocol, params, STATUS_NEW
from pyworkflow.utils.properties import Message

from .objects import SetOfAtlasLocations
from .parsers import EPUParser

"""
This module will provide protocols relating cryo em atlas locations with image
processing data
"""


class AtlasEPUImporter(EMProtocol):
    """ Will import atlas information and relate it to the movies"""
    _label = 'Atlas importer'

    def __init__(self, **kwargs):

        Protocol.__init__(self, **kwargs)

        self.lastCheck = datetime.datetime.now()
        self.lastIdSeen = 0
        self._moviesWithSteps = []

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):

        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('importProtocol', params.PointerParam, pointerClass='ProtImportMovies',
                      label='Import movies protocol', important=True,
                      help='Protocol used to import movies. The original '
                           'path is needed to find the atlas information')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):

        # Insert processing steps
        self._insertFunctionStep('closeStreamingStep', wait=True)

    def closeStreamingStep(self):
        """ Close output set and generate HR resolution jpg from atlas mrc"""

        parser = self._getParser()

        # For each of the atlas
        for grid, atlasFn in parser.getAllAtlas():

            # generate the all atlas images from the mrc found at any GRID folder
            parser.createLRAtlas(atlasFn, self.getAtlasJpgByGrid(grid))


    def getAtlasJpgByGrid(self, grid):
        """ returns the path of the background image (jpg) to be use as background for the viewers"""
        return self._getExtraPath(grid + "_atlas.jpg")

    def _getInputMovies(self):

        return self.importProtocol.get().outputMovies

    def generateAtlasStep(self, movieDict):

        # Movie is a dictionary, convert it to a proper movie object
        movie = Movie()
        movie.setAcquisition(Acquisition())
        movie.setAttributesFromDict(movieDict, setBasic=True,
                                    ignoreMissing=True)

        # Generate the output
        outputLocations = self._getOutputSet()

        al = self._getAtlasInfo(movie)
        if al is not None:
            outputLocations.append(al)
            outputLocations.write()
            self._store()

    def _getAtlasInfo(self, movie):

        # Get the parser
        parser = self._getParser()

        try:
            return parser.getAtlasLocation(movie)
        except Exception as e:
            print("EPU parser can't add atlas location for %s. Error: %s" % (movie.getMicName(), e))

    def _createSetOfAtlasLocation(self, suffix=''):

        return SetOfAtlasLocations.create('atlas%s.sqlite', suffix,
                                          indexes=['_index'])

    def _getOutputSet(self):

        if not hasattr(self, "outputAtlas"):
            newSet = self._createSetOfAtlasLocation()
            self._defineOutputs(outputAtlas=newSet)

            self._defineSourceRelation(self._getInputMovies(), newSet)

        return self.outputAtlas

    def _checkNewInput(self):
        # Check if there are new movies to process from the input set
        localFile = self._getInputMovies().getFileName()
        now = datetime.datetime.now()
        self.lastCheck = getattr(self, 'lastCheck', now)
        mTime = datetime.datetime.fromtimestamp(os.path.getmtime(localFile))

        # If the input movies.sqlite has not changed since our last check,
        # it does not make sense to check for new input data
        if self.lastCheck > mTime and hasattr(self, 'listOfMovies'):
            return None

        # else there are changes
        self.lastCheck = now

        newMovieIds = self._getNewMovieIds()

        if newMovieIds:
            newSteps = self._insertNewMoviesSteps(newMovieIds)

            if newSteps:
                # Get the idleStep (should be the first one)
                idleStep = self._steps[0]
                idleStep.addPrerequisites(*newSteps)
                self.updateSteps()

        # Refresh the input (state)
        self._getInputMovies().loadAllProperties()

        if self._getInputMovies().isStreamClosed():  # Unlock createOutputStep if finished all jobs
            idleStep = self._steps[0]
            if idleStep.isWaiting():
                idleStep.setStatus(STATUS_NEW)

    def _insertNewMoviesSteps(self, newMovieIds):
        """ Insert steps to find atlas information for a movie (from streaming)
        Params:
            inputMovies: input movies set to be check
        """

        steps = []
        # For each movie insert the step to process it
        for movieId in newMovieIds:
            movie = self._getInputMovies()[movieId]
            newStep = self._insertMovieStep(movie)
            if newStep:
                steps.append(newStep)
        return steps

    def _insertMovieStep(self, movie):

        """ Insert the processMovieStep for a given movie. """

        # Get the movie Id
        objId = movie.getObjId()

        if objId not in self._moviesWithSteps:

            movieDict = movie.getObjDict(includeBasic=True)
            movieStepId = self._insertFunctionStep('generateAtlasStep',
                                               movieDict, prerequisites=[])
            self._moviesWithSteps.append(movie.getObjId())
            return movieStepId

    def _getNewMovieIds(self):
        """ Load the input set of movies and create a list. """

        movies = self._getInputMovies()
        newIds = []

        # NOTE:  I'm intentionally here accessing the db object since there is
        # no method to just get the ids in the mapper or set with a where
        whereStr = "%s > %i" % (ID, self.lastIdSeen)

        mapper = movies._getMapper()
        rows = mapper.db.selectObjectsWhere(whereStr)

        for row in rows:

            newIds.append(row[ID])

        return newIds

    def _stepsCheck(self):
        # Input movie set can be loaded or None when checked for new inputs
        # If None, we load it

        self._checkNewInput()

    # -------------------------- Helper functions ------------------------------
    def _getParser(self):
        return  EPUParser(self.importProtocol.get().filesPath.get())

    # -------------------------- INFO functions --------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():

            summary.append("This protocol has associated movies with its"
                           " acquisition location.")
        return summary

    def _methods(self):
        methods = []

        return methods
