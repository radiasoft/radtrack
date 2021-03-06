#
# This class holds an arbitrary 6D phase space distribution.
#  
# Copyright (c) 2013 RadiaBeam Technologies. All rights reserved 
# 
# SciPy imports
import numpy as np

class RbPhaseSpace6D:
    def __init__(self, numParticles):
        # set the number of macro-particles in the bunch
        # initialize the 6D phase space array
        self.setNumParticles(numParticles)

        # specify default file name
        self.fileName = 'ps6d'

        return

    def getNumParticles(self):
        return self.numParticles

    def setNumParticles(self, numParticles):
        if (numParticles > 0):
            self.numParticles = numParticles
            self.initializeArray()
        else:
            message = 'ERROR - numParticles <= 0: ' + str(numParticles)
            raise Exception(message)
        return

    def initializeArray(self):
        self.array6D = np.zeros(6*self.numParticles).reshape(6, self.numParticles)
        return

    def getFileName(self):
        return self.fileName

    def setFileName(self, fileName):
        # error handling of input data
        if (len(fileName) > 0):
            self.fileName = fileName
        else:
            message = 'fileName must have length > 0'
            raise Exception(message)
        return

    def writeArray(self):
        np.savez(self.fileName+'.npz', a=self.array6D)
        return

    def readArray(self):
        dataObject = np.load(self.fileName + '.npz')
        self.array6D = dataObject['a']
        self.checkArray6D()
        return

    def checkArray(self):
        arrayShape = np.shape(self.array6D)

        if len(arrayShape) != 2:
            message = 'Dimensionality of array6D matrix = ' + str(len(arrayShape)) + ' -- must be 2.'
            raise Exception(message)
        else:
            if arrayShape[0] != 6:
                message = 'Dimensionality of array6D = ' + str(arrayShape[0]) + ' -- must be 6.'
                raise Exception(message)
            if (arrayShape[1] < 1):
                message = 'Number of array6D points = ' + str(arrayShape[1]) + ' -- must be > 0'
                raise Exception(message)
            else:
                self.numParticles = arrayShape[1]

        return

    def getArray6D(self):
        return self.array6D

    def setArray6D(self,array6D):
        self.array6D = array6D
        return

    def getArrayX(self):
        return self.array6D[0,:]

    def getArrayXP(self):
        return self.array6D[1,:]

    def getArrayY(self):
        return self.array6D[2,:]

    def getArrayYP(self):
        return self.array6D[3,:]

    def getArrayS(self):
        return self.array6D[4,:]

    def getArrayDP(self):
        return self.array6D[5,:]
