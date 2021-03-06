"""
Copyright (c) 2013 RadiaBeam Technologies. All rights reserved

classes for genesis propagation
"""

from __future__ import print_function, division, unicode_literals, absolute_import
from PyQt4.QtCore import Qt
from radtrack.beamlines.RbElementCommon import *
from radtrack.beamlines.RbBeamlines import BeamlineCommon
from radtrack.beamlines.RbElegantElements import collapseBeamline, expandBeamline, checkParentheses
from radtrack.util.unitConversion import convertUnitsStringToNumber, convertUnitsString
from radtrack.util.RbMath import roundSigFig
from radtrack.util.stringTools import removeWhitespace
import math
from os.path import basename
from collections import OrderedDict


class genesisElement(elementCommon):
    def componentLine(self):
        writeData = []
        for i in range(1, len(self.data)): # self.data[0] == length which is handled elsewhere
            try:
                writeData.append(str(convertUnitsStringToNumber(self.data[i], self.units[i])))
            except ValueError:
                writeData.append('0.0')

        return self.symbol + '\t' + '\t'.join(writeData)


class GenesisBeamline(BeamlineCommon):
    def elegantElement(self, momentum):
        from radtrack.beamlines.RbElegantElements import ElegantBeamline
        elegantBeamline = ElegantBeamline()
        elegantBeamline.name = self.name
        elegantBeamline.data = [element.elegantElement(momentum) for element in self.data]
        return elegantBeamline


beamlineType = GenesisBeamline
fileExtension = 'lat'

class Drift(particleDrift, genesisElement):
    symbol = 'DL'
    elementDescription = 'A drift space'
    parameterNames = ['Length']
    units = ['m']
    dataType = ['double']
    parameterDescription = ['Length']

    def elegantElement(self, momentum):
        from radtrack.beamlines.RbElegantElements import DRIF
        elegant = DRIF()
        elegant.name = self.name
        elegant.data[elegant.parameterNames.index('L')] = str(self.getLength())
        return elegant

class Solenoid(genesisElement, solenoidPic):
    symbol = 'SL'
    elementDescription = 'A solenoid manget'
    parameterNames = ['Length', 'KS']
    units = ['m', 'rad/m', 'T', 'm', 'm', 'm']
    dataType = ['double', 'double']
    parameterDescription = ['Length', 'Geometric Strength, -Bs/(B*Rho)']

    def elegantElement(self, momentum):
        from radtrack.beamlines.RbElegantElements import SOLE
        elegant = SOLE()
        elegant.name = self.name
        elegant.data[elegant.parameterNames.index('L')] = str(self.getLength())
        elegant.data[elegant.parameterNames.index('KS')] = self.data[1]
        return elegant

class Quadrupole(genesisElement, magnetPic):
    symbol = 'QF'
    elementDescription = 'A quadrupole magnet'
    parameterNames = ['Length', 'Field Gradient']
    units = ['m', 'T/m']
    dataType = ['double', 'double']
    parameterDescription = ['Length', 'Field Gradient']
    color = Qt.red

    def elegantElement(self, momentum):
        from radtrack.beamlines.RbElegantElements import QUAD
        elegant = QUAD()
        elegant.name = self.name
        elegant.data[elegant.parameterNames.index('L')] = str(self.getLength())
        speedOfLight = 299792458
        elegant.data[elegant.parameterNames.index('K1')] = str(speedOfLight*float(self.data[1])/momentum)
        return elegant

class Undulator(genesisElement, undulatorPic):
    symbol = 'AW'
    elementDescription = 'A wiggler or undulator for damping or excitation of the beam'
    parameterNames = ['Length', 'AW0']
    units = ['m', '']
    dataType = ['double', 'double']
    parameterDescription = ['Length', 'Dimensionless strength parameter']

    def elegantElement(self, momentum):
        from radtrack.beamlines.RbElegantElements import WIGGLER
        elegant = WIGGLER()
        elegant.name = self.name
        elegant.data[elegant.parameterNames.index('L')] = str(self.getLength())
        elegant.data[elegant.parameterNames.index('K')] = self.data[1]
        return elegant

classDictionary = dict()
genesisClassDictionary = dict()

for key in list(globals()):
    if hasattr(globals()[key], 'elementDescription'):
        classDictionary[key] = globals()[key]
        genesisClassDictionary[classDictionary[key].symbol] = globals()[key]

advancedNames = []

def fileImporter(fileName):
    lines = []

    with open(fileName) as file:
        while True:
            line = file.readline()
            if not line:
                break

            if not line.startswith('!'):
                lines.append(line)
            else:
                if line.upper().find('LOOP') != -1 and line.find('=') != -1:
                    try:
                        loops = int(line.split('=')[1])
                    except ValueError:
                        raise IOError('Invalid LOOP count in Genesis file: ' + line)
                    repeatedLines = []
                    line = file.readline()
                    while line.find('ENDLOOP') == -1:
                        repeatedLines.append(line)
                        line = file.readline()
                        if not line:
                            raise IOError('!LOOP = ' + str(loops) + ' not terminated with !ENDLOOP')
                    if not line.startswith('!'):
                        raise IOError('ENDLOOP command needs to start with "!"')

                    lines.extend(repeatedLines * loops)

                else:
                    raise IOError('Invalid line in Genesis file: ' + line)

    elementPosition = dict() # current spacing of elementType
    for elementType in classDictionary.values():
        elementPosition[elementType] = 0.0

    beamline = [] # list of tuples of (position, element)
    elementDictionary = OrderedDict()
    serialNumber = 0

    unitLength = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Information
        if line.startswith('?'):
            if line.upper().find('VERSION') != -1:
                continue
            if line.upper().find('UNITLENGTH') != -1:
                if not unitLength:
                    unitLength = float(line.split('=')[1])
                    continue
                else:
                    raise IOError('UNITLENGTH should only be specified once.')

            raise IOError('Invalid line in Genesis file: ' + line)

        # Command (there should be none left)
        if line.startswith('!'):
            raise IOError('Invalid line in Genesis file: ' + line)

        if not unitLength:
            raise IOError('UNITLENGTH not defined.')

        # Beam line elements
        elementType, strength, length, spacing = line.split()
        try:
            genesisType = genesisClassDictionary[elementType]
        except KeyError:
            raise IOError('Invalid line in Genesis file: ' + line)
        element = genesisType()
        element.data = [str(roundSigFig(float(length)*unitLength, 6)), strength]
        element.name = elementType + str(serialNumber)
        serialNumber += 1
        elementDictionary[element.name] = element

        distanceFromLast = float(spacing)*unitLength
        beamline.append((elementPosition[genesisType] + distanceFromLast, element))
        elementPosition[genesisType] += distanceFromLast + element.getLength()

    beamline.sort()
    beamlineWithDrifts = []
    currentPosition = 0.0
    for position, element in beamline:
        if abs(position - currentPosition) > 1e-6:
            drift = Drift()
            drift.name = 'AD' + str(serialNumber)
            serialNumber += 1
            drift.data = [str(position - currentPosition)]
            beamlineWithDrifts.append(drift)
            currentPosition += beamlineWithDrifts[-1].getLength()
            elementDictionary[drift.name] = drift
        beamlineWithDrifts.append(element)
        currentPosition += beamlineWithDrifts[-1].getLength()

    beamlineElement = GenesisBeamline()
    beamlineElement.name = 'BeamLine'
    beamlineElement.data = beamlineWithDrifts
    elementDictionary[beamlineElement.name] = beamlineElement

    return elementDictionary, None


def isInteger(x):
    return math.floor(x) == x

def fileExporter(outputFileName, elementDictionary, defaultBeamline):
    beamline = None
    if defaultBeamline:
        beamline = elementDictionary[defaultBeamline]
    else:
        for element in elementDictionary.values():
            if element.isBeamline():
                beamline = element
    if not beamline:
        if parent and basename(outputFileName).startswith(parent.tabPrefix):
            beamline = GenesisBeamline()
            beamline.data = elementDictionary.values() # save all elements in order created
        else:
            raise IOError('Cannot write file: no beam line was created.')

    unitLength = 1.0
    for element in elementDictionary.values():
        if not element.isBeamline():
            length = element.getLength()
            while not isInteger(roundSigFig(length/unitLength, 6)):
                unitLength = unitLength/10.0


    lines = []
    elementTypesWritten = [Drift] # Drifts are never written to files
    for elementType in [type(elementDictionary[elementName]) for elementName in beamline.fullElementNameList()]:
        if elementType in elementTypesWritten:
            continue
        elementTypesWritten.append(elementType)
        lines.append('### ' + elementType.__name__ + 's ###')
        currentPosition = 0.0 # position at end of current element
        lastPositionOfElement = 0.0 # position at end of previous element of same type
        for partName in beamline.fullElementNameList():
            part = elementDictionary[partName]
            lastPosition = currentPosition # position at start of current element
            currentPosition += part.getLength()
            if type(part) != elementType:
                continue
            lines.append(part.componentLine() + '\t' \
                             + str(int(round(part.getLength()/unitLength))) + '\t' \
                             + str(int(round((lastPosition - lastPositionOfElement)/unitLength))))
            lastPositionOfElement = currentPosition


    # Find loops in beamline and abbreviate them
    linesToWrite = []
    collapsedLines = collapseBeamline(lines)
    completeLine = ''
    for line in collapsedLines.split(','):
        if completeLine:
            completeLine = completeLine + ',' + line.strip()
        else:
            completeLine = line.strip()

        if not completeLine:
            continue

        if not checkParentheses(completeLine):
            continue

        if not completeLine[0] in string.digits:
            linesToWrite.append(completeLine)
            completeLine = ''
            continue

        # Expand inner loops
        count, loopedSection = completeLine.split('*', 1)
        loopedSection = expandBeamline(loopedSection)

        linesToWrite.append("! LOOP = " + count)
        linesToWrite.extend(loopedSection)
        linesToWrite.append("! ENDLOOP")
        completeLine = ''

    with open(outputFileName, "w") as outputFile:
        outputFile.write('# This Genesis file was created by RadTrack\n')
        outputFile.write('# RadTrack (c) 2013, RadiaSoft, LLC\n\n')
        outputFile.write('? VERSION = 1.0\n')
        outputFile.write('? UNITLENGTH = ' + str(unitLength) + '\n\n')

        for line in linesToWrite:
            if line.startswith('###'):
                line = '\n' + line
            outputFile.write(line + '\n')
