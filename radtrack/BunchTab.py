# -*- coding: utf-8 -*-
u"""Interactive window for charged particle bunches

Imports the auto-generated RbBunchInterface.py module, which is
created via pyside-uic.exe from Qt's RbBunchInterface.ui file.

Here, the window is instantiated and hooks to the production Python code are established.

:copyright: Copyright (c) 2013 RadiaBeam Technologies. All rights reserved
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import sys, re, os, math, csv

# SciPy imports
import numpy as np
from scipy import constants
import matplotlib.pyplot as plt

# PyQt4 imports
from PyQt4 import QtGui

# RadTrack imports
import radtrack.bunch.RbParticleBeam6D as beam
import radtrack.statistics.RbStatistics6D as stat
from radtrack.ui.BunchInterface import Ui_bunchInterface
from radtrack.util.unitConversion import convertUnitsStringToNumber, \
                                         convertUnitsNumber, \
                                         convertUnitsNumberToString
from radtrack.util.plotTools import scatConPlot
from radtrack.util.fileTools import fileTypeList, isSDDS, getSaveFileName

import sdds

class BunchTab(QtGui.QWidget):
    acceptsFileTypes = ['sdds', 'csv', 'out', 'bun']
    defaultTitle = 'Bunch'
    task = 'Create a particle beam'
    category = 'beams'

    def __init__(self,parent=None):       # initialization
        super(BunchTab, self).__init__(parent)
        self.ui = Ui_bunchInterface()
        self.ui.setupUi(self)

        # set default values for flags
        self.numTicks = 5
        self.myBunch = None
        self.maxParticles = 10000

        # link the simple push buttons to appropriate methods
        self.ui.aspectRatio.stateChanged.connect(self.refreshPlots)
        self.ui.generateBunch.clicked.connect(lambda : self.generateBunch(self.maxParticles))

        self.ui.particleType.currentIndexChanged.connect(self.changeMass)
        self.ui.plotType.currentIndexChanged.connect(self.refreshPlots)
        self.ui.plotTitles.stateChanged.connect(self.refreshPlots)
        self.ui.distribType.currentIndexChanged.connect(self.refreshPlots)

        # specify physical constants
        self.c     = constants.c          # speed of light [m/s]
        self.eMass   = constants.m_e    # electron mass [kG]
        self.eCharge = constants.e    # elementary charge [C]
        self.eMassEV = self.eMass*(self.c**2)/self.eCharge  # eMass [eV]

        # specify default values for all input fields
        numParticles = 800
        self.designMomentumEV = 2.e+8
        self.totalCharge = 1.e-9
        self.putParametersInGUI(numParticles)

        self.unitsPos = 'mm'
        self.unitsAngle = 'mrad'
        self.ui.unitsPos.setText(self.unitsPos)
        self.ui.unitsAngle.setText(self.unitsAngle)
        self.ui.numTicks.setText(str(self.numTicks))

        self.ui.twissTable.setEditTriggers(QtGui.QAbstractItemView.CurrentChanged)
        self.ui.twissTable.setItem(0,0,QtGui.QTableWidgetItem('0.'))
        self.ui.twissTable.setItem(1,0,QtGui.QTableWidgetItem('0.'))
        self.ui.twissTable.setItem(0,1,QtGui.QTableWidgetItem('1 m'))
        self.ui.twissTable.setItem(1,1,QtGui.QTableWidgetItem('1 m'))
        self.ui.twissTable.setItem(0,2,QtGui.QTableWidgetItem('1 micron'))
        self.ui.twissTable.setItem(1,2,QtGui.QTableWidgetItem('1 micron'))

        self.ui.twissTableZ.setEditTriggers(QtGui.QAbstractItemView.CurrentChanged)
        self.ui.twissTableZ.setItem(0,0,QtGui.QTableWidgetItem('0'))
        self.ui.twissTableZ.setItem(0,1,QtGui.QTableWidgetItem('1 mm'))
        self.ui.twissTableZ.setItem(0,2,QtGui.QTableWidgetItem('1.e-3'))

        self.ui.offsetTable.setEditTriggers(QtGui.QAbstractItemView.CurrentChanged)
        self.ui.offsetTable.setItem(0,0,QtGui.QTableWidgetItem('0 mm'))
        self.ui.offsetTable.setItem(1,0,QtGui.QTableWidgetItem('0 mm'))
        self.ui.offsetTable.setItem(2,0,QtGui.QTableWidgetItem('0 mm'))
        self.ui.offsetTable.setItem(0,1,QtGui.QTableWidgetItem('0 mrad'))
        self.ui.offsetTable.setItem(1,1,QtGui.QTableWidgetItem('0 mrad'))
        self.ui.offsetTable.setItem(2,1,QtGui.QTableWidgetItem('0 mrad'))

        for thing in [self.ui.twissTable, self.ui.twissTableZ, self.ui.offsetTable]:
            thing.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)

        # file directories
        self.parent = parent
        if self.parent is None:
            self.parent = self
            self.parent.lastUsedDirectory = os.path.expanduser('~')

        # try to make the blank plotting regions look nice
        self.erasePlots()

    def generateBunch(self, particleLimit = None):
        if self.userInputEnabled():
            errorMessage = []
            self.parent.ui.statusbar.showMessage('Generating bunch ...')

            # Get input from text boxes.
            try:
                numParticles = int(self.ui.numPtcls.text())
            except ValueError:
                numParticles = 0
            if numParticles <= 0:
                errorMessage.append(self.ui.numPtclsLabel.text().strip() + ' must be a postive number.')
            if particleLimit:
                numParticles = min(numParticles, particleLimit)

            try:
                self.designMomentumEV = convertUnitsStringToNumber(self.ui.designMomentum.text(), 'eV')
            except ValueError:
                self.designMomentumEV = 0
            if self.designMomentumEV <= 0:
                errorMessage.append(self.ui.designMomentumLabel.text().strip() + ' must be a positive value.')

            try:
                self.totalCharge = convertUnitsStringToNumber(self.ui.totalCharge.text().strip(), 'C')
            except ValueError:
                self.totalCharge = 0
            if self.totalCharge <= 0:
                errorMessage.append(self.ui.charge.text() + ' must be a positive value.')

            if errorMessage:
                QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                        'Input Error' + ('s' if len(errorMessage) > 1 else ''),
                        '\n'.join(errorMessage),
                        QtGui.QMessageBox.Ok,
                        self).exec_()
                self.parent.ui.statusbar.clearMessage()
                self.myBunch = None
                return

            beta0gamma0 = self.designMomentumEV / self.eMassEV
            gamma0 = math.sqrt(beta0gamma0**2 + 1.)
            beta0 = beta0gamma0 / gamma0

            # get input from the table of Twiss parameters
            self.twissAlphaX = convertUnitsStringToNumber(self.ui.twissTable.item(0,0).text(), '')
            self.twissAlphaY = convertUnitsStringToNumber(self.ui.twissTable.item(1,0).text(), '')
            self.twissBetaX  = convertUnitsStringToNumber(self.ui.twissTable.item(0,1).text(), 'm/rad')
            self.twissBetaY  = convertUnitsStringToNumber(self.ui.twissTable.item(1,1).text(), 'm/rad')
            self.twissEmitNX = convertUnitsStringToNumber(self.ui.twissTable.item(0,2).text(), 'm*rad')
            self.twissEmitNY = convertUnitsStringToNumber(self.ui.twissTable.item(1,2).text(), 'm*rad')

            if self.ui.longTwissFlag.currentText() == "alpha-bct-dp":
                self.twissAlphaZ = convertUnitsStringToNumber(self.ui.twissTableZ.item(0,0).text(), '')
                self.bctRms = convertUnitsStringToNumber(self.ui.twissTableZ.item(0,1).text(), 'm')
                self.dPopRms  = float(self.ui.twissTableZ.item(0,2).text())

                self.twissEmitNZ = (self.bctRms/beta0) * self.dPopRms / math.sqrt(1.+self.twissAlphaZ**2)
                self.twissBetaZ  = (self.bctRms/beta0) / self.dPopRms * math.sqrt(1.+self.twissAlphaZ**2)

            # Get input from the table of phase space offsets
            self.offsetX  = convertUnitsStringToNumber(self.ui.offsetTable.item(0,0).text(), 'm')
            self.offsetY  = convertUnitsStringToNumber(self.ui.offsetTable.item(1,0).text(), 'm')
            self.offsetT  = convertUnitsStringToNumber(self.ui.offsetTable.item(2,0).text(), 'm')
            self.offsetXP = convertUnitsStringToNumber(self.ui.offsetTable.item(0,1).text(), 'rad')
            self.offsetYP = convertUnitsStringToNumber(self.ui.offsetTable.item(1,1).text(), 'rad')
            self.offsetPT = convertUnitsStringToNumber(self.ui.offsetTable.item(2,1).text(), 'rad')*beta0gamma0

            # instantiate the particle bunch
            self.myBunch = beam.RbParticleBeam6D(numParticles)
            self.myBunch.setDesignMomentumEV(self.designMomentumEV)
            self.myBunch.setTotalCharge(self.totalCharge)
            self.myBunch.setMassEV(self.eMassEV)

            # specify the distribution flag and extent
            self.myDist = self.myBunch.getDistribution6D()
            self.myDist.setDistributionType(self.ui.distribType.currentText().lower())
            self.myDist.setMaxRmsFactor(3.)

            # specify the Twiss parameters
            self.myBunch.setTwissParamsByName2D(self.twissAlphaX,self.twissBetaX,
                                                self.twissEmitNX/beta0gamma0,'twissX')
            self.myBunch.setTwissParamsByName2D(self.twissAlphaY,self.twissBetaY,
                                                self.twissEmitNY/beta0gamma0,'twissY')
            self.myBunch.setTwissParamsByName2D(self.twissAlphaZ,self.twissBetaZ,
                                                self.twissEmitNZ,'twissZ')

            # create the distribution
            self.myBunch.makeParticlePhaseSpace6D(beta0gamma0)

            # offset the distribution
            if self.offsetX  != 0.:
                self.myDist.offsetDistribComp(self.offsetX,  0)
            if self.offsetXP != 0.:
                self.myDist.offsetDistribComp(self.offsetXP, 1)
            if self.offsetY  != 0.:
                self.myDist.offsetDistribComp(self.offsetY,  2)
            if self.offsetYP != 0.:
                self.myDist.offsetDistribComp(self.offsetYP, 3)
            if self.offsetT  != 0.:
                self.myDist.offsetDistribComp(self.offsetT,  4)
            if self.offsetPT != 0.:
                self.myDist.offsetDistribComp(self.offsetPT, 5)

        # generate the plots
        if particleLimit:
            self.refreshPlots()

        self.parent.ui.statusbar.clearMessage()

    def refreshPlots(self,internal=False):
        self.parent.ui.statusbar.showMessage('Redrawing plots ...')
        self.erasePlots()

        # nothing to plot, if beam hasn't been initialized
        if not self.myBunch:
            self.parent.ui.statusbar.clearMessage()
            return

        # get the specified units for plotting
        self.unitsPos = self.ui.unitsPos.text()
        self.unitsAngle = self.ui.unitsAngle.text()

        # get the number of tick marks
        self.numTicks = int(self.ui.numTicks.text())

        # create local pointer to particle array
        tmp6 = randomSampleOfBunch(
                self.myBunch.getDistribution6D().getPhaseSpace6D().getArray6D(),
                min(self.maxParticles, int(self.ui.numPtcls.text())))

        numParticles = tmp6.shape[1]

        nLevels = 5 + int(math.pow(numParticles, 0.33333333))
        nDivs = 10 + int(math.pow(numParticles, 0.2))

        # generate the four plots
        self.plotXY( convertUnitsNumber(tmp6[0,:], 'm', self.unitsPos),
                     convertUnitsNumber(tmp6[2,:], 'm', self.unitsPos),
                     nDivs, nLevels)

        self.plotXPX(convertUnitsNumber(tmp6[0,:], 'm', self.unitsPos),
                     convertUnitsNumber(tmp6[1,:], 'rad', self.unitsAngle),
                     nDivs, nLevels)

        self.plotYPY(convertUnitsNumber(tmp6[2,:], 'm', self.unitsPos),
                     convertUnitsNumber(tmp6[3,:], 'rad', self.unitsAngle),
                     nDivs, nLevels)

        self.plotSDP(convertUnitsNumber(tmp6[4,:], 'm', self.unitsPos),
                     tmp6[5,:],
                     nDivs, nLevels)

        self.parent.ui.statusbar.clearMessage()


    def plotGenericBefore(self, hData, vData, _canvas, nDivs, nLevels):
        _canvas.ax.clear()
        scatConPlot(self.ui.plotType.currentText().lower(), 'linear', hData, vData, _canvas.ax, nDivs, nLevels)
        _canvas.ax.xaxis.set_major_locator(plt.MaxNLocator(self.numTicks))
        _canvas.ax.yaxis.set_major_locator(plt.MaxNLocator(self.numTicks))

    def plotGenericAfter(self, _canvas, title):
        if self.ui.plotTitles.isChecked():
            _canvas.ax.set_title(title)
        _canvas.fig.set_facecolor('w')
        _canvas.fig.tight_layout()
        _canvas.draw()


    def plotXY(self, hData, vData, nDivs, nLevels):
        self.plotGenericBefore(hData, vData, self.ui.xyPlot.canvas, nDivs, nLevels)
        if self.ui.aspectRatio.isChecked():
            self.ui.xyPlot.canvas.ax.set_aspect('equal', 'datalim')
        else:
            self.ui.xyPlot.canvas.ax.set_aspect('auto', 'datalim')
        self.ui.xyPlot.canvas.ax.set_xlabel('x ['+self.unitsPos+']')
        self.ui.xyPlot.canvas.ax.set_ylabel('y ['+self.unitsPos+']')

        self.plotGenericAfter(self.ui.xyPlot.canvas, 'Cross-Section')

    def plotXPX(self, hData, vData, nDivs, nLevels):
        self.plotGenericBefore(hData, vData, self.ui.xpxPlot.canvas, nDivs, nLevels)
        self.ui.xpxPlot.canvas.ax.set_xlabel('x ['+self.unitsPos+']')
        self.ui.xpxPlot.canvas.ax.set_ylabel("x' ["+self.unitsAngle+']')
        self.plotGenericAfter(self.ui.xpxPlot.canvas, 'Horizontal')

    def plotYPY(self, hData, vData, nDivs, nLevels):
        self.plotGenericBefore(hData, vData, self.ui.ypyPlot.canvas, nDivs, nLevels)
        self.ui.ypyPlot.canvas.ax.set_xlabel('y ['+self.unitsPos+']')
        self.ui.ypyPlot.canvas.ax.set_ylabel("y' ["+self.unitsAngle+']')
        self.plotGenericAfter(self.ui.ypyPlot.canvas, 'Vertical')

    def plotSDP(self, hData, vData, nDivs, nLevels):
        self.plotGenericBefore(hData, vData, self.ui.tpzPlot.canvas, nDivs, nLevels)
        self.ui.tpzPlot.canvas.ax.set_xlabel('s ['+self.unitsPos+']')
        self.ui.tpzPlot.canvas.ax.set_ylabel('p [beta*gamma]')
        self.plotGenericAfter(self.ui.tpzPlot.canvas, 'Longitudinal')

    def erasePlots(self):
        plots = [self.ui.xyPlot, self.ui.xpxPlot, self.ui.ypyPlot, self.ui.tpzPlot]

        for plot in plots:
            plot.canvas.ax.clear()

        if self.ui.plotTitles.isChecked():
            self.ui.xyPlot.canvas.ax.set_title('Cross-Section')
            self.ui.xpxPlot.canvas.ax.set_title('Horizontal')
            self.ui.ypyPlot.canvas.ax.set_title('Vertical')
            self.ui.tpzPlot.canvas.ax.set_title('Longitudinal')

        self.ui.xyPlot.canvas.ax.set_xlabel('x ['+self.unitsPos+']')
        self.ui.xyPlot.canvas.ax.set_ylabel('y ['+self.unitsPos+']')

        self.ui.xpxPlot.canvas.ax.set_xlabel('x ['+self.unitsPos+']')
        self.ui.xpxPlot.canvas.ax.set_ylabel("x' ["+self.unitsAngle+']')

        self.ui.ypyPlot.canvas.ax.set_xlabel('y ['+self.unitsPos+']')
        self.ui.ypyPlot.canvas.ax.set_ylabel("y' ["+self.unitsAngle+']')

        self.ui.tpzPlot.canvas.ax.set_xlabel('s ['+self.unitsPos+']')
        self.ui.tpzPlot.canvas.ax.set_ylabel('p []')


        for plot in plots:
            plot.canvas.ax.axis([-1., 1., -1., 1.])
            plot.canvas.fig.set_facecolor('w')
            plot.canvas.fig.tight_layout()
            plot.canvas.draw()

    # calculate the Twiss parameters
    def calculateTwiss(self):
        # nothing to do, if beam hasn't been initialized
        if not self.myBunch:
            return
        
        # let the bunch object to the heavy lifting
        self.myBunch.calcTwissParams6D()

        # now ask for the results
        self.twissX = self.myBunch.getTwissParamsByName2D('twissX')
        self.twissY = self.myBunch.getTwissParamsByName2D('twissY')
        self.twissZ = self.myBunch.getTwissParamsByName2D('twissZ')

        self.twissAlphaX = self.twissX.getAlphaRMS()
        self.twissAlphaY = self.twissY.getAlphaRMS()
        self.twissAlphaZ = self.twissZ.getAlphaRMS()

        self.twissBetaX = self.twissX.getBetaRMS()
        self.twissBetaY = self.twissY.getBetaRMS()
        self.twissBetaZ = self.twissZ.getBetaRMS()

        # load Twiss parameters into window for user to see
        self.ui.twissTable.setItem(0,0,QtGui.QTableWidgetItem("{:.5e}".format(self.twissAlphaX)))
        self.ui.twissTable.setItem(1,0,QtGui.QTableWidgetItem("{:.5e}".format(self.twissAlphaY)))
        self.ui.twissTable.setItem(0,1,QtGui.QTableWidgetItem("{:.5e}".format(self.twissBetaX)))
        self.ui.twissTable.setItem(1,1,QtGui.QTableWidgetItem("{:.5e}".format(self.twissBetaY)))

        # need the design momentum in order to handle the longitudinal phase space
        self.designMomentumEV = self.myBunch.getDesignMomentumEV()
        beta0gamma0 = self.designMomentumEV / self.eMassEV
        gamma0 = math.sqrt(beta0gamma0**2 + 1.)
        beta0 = beta0gamma0 / gamma0

        if self.ui.longTwissFlag.currentText() == "alpha-bct-dp":
            self.twissAlphaZ = self.twissZ.getAlphaRMS()
            self.twissBetaZ = self.twissZ.getBetaRMS()
            self.twissEmitNZ = self.twissZ.getEmitRMS()

            self.bctRms = beta0*math.sqrt(self.twissEmitNZ*self.twissBetaZ)
            twissGammaZ = (1.+self.twissAlphaZ**2) / self.twissBetaZ
            self.dPopRms = math.sqrt(self.twissEmitNZ*twissGammaZ)

            self.ui.twissTableZ.setItem(0,0,QtGui.QTableWidgetItem("{:.5e}".format(self.twissAlphaZ)))
            self.ui.twissTableZ.setItem(0,1,QtGui.QTableWidgetItem("{:.5e}".format(self.bctRms)))
            self.ui.twissTableZ.setItem(0,2,QtGui.QTableWidgetItem("{:.5e}".format(self.dPopRms)))

        # get average values
        avgArray = stat.calcAverages6D(self.myBunch.getDistribution6D().getPhaseSpace6D().getArray6D())

        # load offsets into window for user to see
        self.ui.offsetTable.setItem(0,0,QtGui.QTableWidgetItem("{:.5e}".format(avgArray[0])))
        self.ui.offsetTable.setItem(1,0,QtGui.QTableWidgetItem("{:.5e}".format(avgArray[2])))
        self.ui.offsetTable.setItem(2,0,QtGui.QTableWidgetItem("{:.5e}".format(avgArray[4])))
        self.ui.offsetTable.setItem(0,1,QtGui.QTableWidgetItem("{:.5e}".format(avgArray[1])))
        self.ui.offsetTable.setItem(1,1,QtGui.QTableWidgetItem("{:.5e}".format(avgArray[3])))
        self.ui.offsetTable.setItem(2,1,QtGui.QTableWidgetItem("{:.5e}".format(avgArray[5])))

        # obtain top-level parameters
        self.designMomentumEV = self.myBunch.getDesignMomentumEV()
        numParticles = self.myBunch.getDistribution6D().getPhaseSpace6D().getNumParticles()

        # load values into window for user to see
        self.putParametersInGUI(numParticles)

        # normalize the emittance here
        self.twissEmitNX = self.twissX.getEmitRMS() * beta0gamma0
        self.twissEmitNY = self.twissY.getEmitRMS() * beta0gamma0
        self.twissEmitNZ = self.twissZ.getEmitRMS() * beta0gamma0
        self.ui.twissTable.setItem(0,2,QtGui.QTableWidgetItem("{:.5e}".format(self.twissEmitNX)))
        self.ui.twissTable.setItem(1,2,QtGui.QTableWidgetItem("{:.5e}".format(self.twissEmitNY)))


    def importFile(self, fileName = None):
        """Allow importing from CSV or SDDS"""
        # use Qt file dialog
        if not fileName:
            fileName = QtGui.QFileDialog.getOpenFileName(self, "Import particle file",
                    self.parent.lastUsedDirectory, fileTypeList(self.acceptsFileTypes))

            # if user cancels out, do nothing
            if not fileName:
                return

        self.parent.lastUsedDirectory = os.path.dirname(fileName)

        if os.path.basename(fileName).startswith(self.parent.tabPrefix):
            if fileName.split('+')[-1].split('.')[0] == 'False':
                self.disableInput()
        else:
            self.disableInput()


        if re.search('\.csv$', fileName, re.IGNORECASE):
            self.readFromCSV(fileName)
        else:
            self.readFromSDDS(fileName)

        self.calculateTwiss()
        self.refreshPlots()
        self.ui.tpzPlot.canvas.ax.set_xlabel('t [s]')
        self.ui.tpzPlot.canvas.ax.set_ylabel('p [beta*gamma]')
        self.ui.tpzPlot.canvas.draw()


    def readFromSDDS(self, fileName):
        if not isSDDS(fileName):
            QtGui.QMessageBox.warning(self, 'Error Importing File', fileName + ' is not an SDDS file.')
            return

        # index is always zero...?
        sddsIndex = 0

        # initialize sdds.sddsdata.pyd library (Windows only) with data file
        if sdds.sddsdata.InitializeInput(sddsIndex, fileName) != 1:
            sdds.sddsdata.PrintErrors(1)

        # get parameter names
        paramNames = sdds.sddsdata.GetParameterNames(sddsIndex)

        # give the user a look at the parameters (if any)
        finalMsgBox = None
        if not paramNames:
            message  = 'WARNING --\n\n'
            message += 'No parameters were found in your selected SDDS file!!\n\n'
            message += 'The design momentum, total beam charge, etc., will have to be manually entered.'
            finalMsgBox = QtGui.QMessageBox(self)
            finalMsgBox.setText(message)

        # get column names
        columnNames = sdds.sddsdata.GetColumnNames(sddsIndex)

        # column data has to be handled differently;
        #   it will be a 6D python array of N-D NumPy arrays
        columnData = range(len(columnNames))

        # read parameter data from the SDDS file
        # mus read particle data at the same time
        try:
            errorCode = sdds.sddsdata.ReadPage(sddsIndex)
            if errorCode != 1:
                sdds.sddsdata.PrintErrors(1)
            while errorCode > 0:
                for jLoop in range(len(columnNames)):
                    columnData[jLoop] = np.array(sdds.sddsdata.GetColumn(sddsIndex,jLoop))

                errorCode = sdds.sddsdata.ReadPage(sddsIndex)
        except Exception:
            QtGui.QMessageBox.warning(self, "Error Importing File", "The file " + fileName + " does not contain any particles.")
            return

        for parameter in ['designMomentumEV', 'totalCharge', 'eMassEV']:
            try:
                setattr(self, parameter, sdds.sddsdata.GetParameter(sddsIndex, paramNames.index(parameter)))
            except ValueError: # parameter not in list
                pass

        # get column definitions
        # units are in the 2nd column
        columnDefs = [sdds.sddsdata.GetColumnDefinition(sddsIndex,name) for name in columnNames]
        unitStrings = [cD[1] for cD in columnDefs]

        # begin deciphering the column data
        dataIndex = [-1]*6
        message = ''
        for iLoop in range(len(columnNames)):
            if columnNames[iLoop]=='x' or columnNames[iLoop]=='X':
                if dataIndex[0] >= 0:
                    message  = 'Error -- \n\n'
                    message += '  X column appears twice, for iLoop = '
                    message += str(dataIndex[0]) + ' and ' + str(iLoop)
                dataIndex[0] = iLoop
            if columnNames[iLoop]=='xp' or columnNames[iLoop]=='px' or columnNames[iLoop]=="x'":
                if dataIndex[1] >= 0:
                    message  = 'Error -- \n\n'
                    message += '  XP column appears twice, for iLoop = '
                    message += str(dataIndex[1]) + ' and ' + str(iLoop)
                dataIndex[1] = iLoop
            if columnNames[iLoop]=='y' or columnNames[iLoop]=='Y':
                if dataIndex[2] >= 0:
                    message  = 'Error -- \n\n'
                    message += '  Y column appears twice, for iLoop = '
                    message += str(dataIndex[2]) + ' and ' + str(iLoop)
                dataIndex[2] = iLoop
            if columnNames[iLoop]=='yp' or columnNames[iLoop]=='py' or columnNames[iLoop]=="y'":
                if dataIndex[3] >= 0:
                    message  = 'Error -- \n\n'
                    message += '  YP column appears twice, for iLoop = '
                    message += str(dataIndex[3]) + ' and ' + str(iLoop)
                dataIndex[3] = iLoop
            if columnNames[iLoop]=='s' or columnNames[iLoop]=='ct' or columnNames[iLoop]=='t':
                if dataIndex[4] >= 0:
                    message  = 'Error -- \n\n'
                    message += '  S column appears twice, for iLoop = '
                    message += str(dataIndex[4]) + ' and ' + str(iLoop)
                dataIndex[4] = iLoop
            if columnNames[iLoop]=='p' or columnNames[iLoop]=='pt' or columnNames[iLoop]=='dp':
                if dataIndex[5] >= 0:
                    message  = 'Error -- \n\n'
                    message += '  DP column appears twice, for iLoop = '
                    message += str(dataIndex[5]) + ' and ' + str(iLoop)
                dataIndex[5] = iLoop

            if message:
                msgBox = QtGui.QMessageBox()
                msgBox.setText(message)
                msgBox.exec_()
                return

        # initial validation of the column data
        if any([d < 0 for d in dataIndex]):
            msgBox = QtGui.QMessageBox()
            message  = 'ERROR --\n\n'
            message += '  Not all of the data columns could be correctly interpreted!\n'
            message += '  These are the column headings that were parsed from the file:\n'
            message += '    ' + str(columnNames) + '\n\n'
            try:
                message += 'The parsing logic failed on: ' + columnNames[iLoop] + '\n'
                message += 'The code is looking for [x, xp, y, yp, s, dp] or something similar.'
            except UnboundLocalError:
                message += 'No data found\n'
            msgBox.setText(message)
            msgBox.exec_()
            return

        # check for unspecified units, and set them to default value
        # if the units are specified, but incorrect, the problem is detected below
        defaultUnits = ['m', 'rad', 'm', 'rad', 'm', 'm$be$nc']
        for iLoop in range(6):
            if not unitStrings[iLoop]:
                unitStrings[iLoop] = defaultUnits[dataIndex[iLoop]]

        # check that all data columns are the same length
        numElements = [len(col) for col in columnData]

        if any([n != numElements[0] for n in numElements]):
            msgBox = QtGui.QMessageBox()
            message  = 'ERROR --\n\n'
            message += '  Not all of the data columns have the same length!\n'
            message += '  Here is the number of elements found in each column:\n'
            message += '    ' + str(numElements) + '\n\n'
            message += 'Please try again with a valid particle file.'
            msgBox.setText(message)
            msgBox.exec_()
            return

        # now we know the number of macro-particles
        numParticles = numElements[0]

        # close the SDDS particle file
        if sdds.sddsdata.Terminate(sddsIndex) != 1:
            sdds.sddsdata.PrintErrors(1)

        # instantiate the particle bunch
        self.myBunch = beam.RbParticleBeam6D(numParticles)
        self.designMomentumEV = convertUnitsStringToNumber(self.ui.designMomentum.text(), 'eV')
        self.myBunch.setDesignMomentumEV(self.designMomentumEV)
        self.myBunch.setMassEV(self.eMassEV)

        # all seems to be well, so load particle data into local array,
        #   accounting for any non-standard physical units
        tmp6 = np.array([columnData[dataIndex[i]] for i in range(6)])
        #check for negative energy means p is relative
        relativeMomentum = any(n<0 for n in tmp6[5,:])

        # load particle array into the phase space object
        self.myBunch.getDistribution6D().getPhaseSpace6D().setArray6D(tmp6)
        if relativeMomentum:
            self.myBunch.getDistribution6D().multiplyDistribComp(self.designMomentumEV,5)
            self.myBunch.getDistribution6D().offsetDistribComp(self.designMomentumEV,5)
        else: 
            self.designMomentumEV=self.myBunch.getDistribution6D().calcAverages6D()[5]*self.myBunch.eMassEV
            self.myBunch.setDesignMomentumEV(self.designMomentumEV)

        self.totalCharge = numParticles*self.eCharge
        self.putParametersInGUI(numParticles)

        # plot the results
        if finalMsgBox is not None:
            finalMsgBox.show()


    def putParametersInGUI(self, numParticles):
        # post top-level parameters to GUI
        self.ui.numPtcls.setText(str(numParticles))
        self.ui.designMomentum.setText(convertUnitsNumberToString(self.designMomentumEV, 'eV', 'MeV'))
        self.ui.totalCharge.setText(convertUnitsNumberToString(self.totalCharge, 'C', 'nC'))

    def readFromCSV(self, fileName):
        # check whether this is a RadTrack generated CSV file
        with open(fileName) as fileObject:
            csvReader = csv.reader(fileObject, delimiter=str(','))
            for lineNumber, rawData in enumerate(csvReader, 1):
                # make sure this file follows the RadTrack format
                if lineNumber == 1:
                    if rawData[0] != 'RadTrack':
                        msgBox = QtGui.QMessageBox()
                        message  = 'ERROR --\n\n'
                        message += '  The selected CSV file was not generated by RadTrack.\n'
                        message += '  Please select another file.\n\n'
                        msgBox.setText(message)
                        msgBox.exec_()
                        return
                # ignore the 2nd line
                elif lineNumber == 2:
                    continue
                # 3rd line contains the parametic data
                elif lineNumber == 3:
                    self.designMomentumEV = float(rawData[0])
                    self.totalCharge = float(rawData[1])
                    break # don't read beyond the first three lines

        # load file into temporary data array
        tmp6 = np.loadtxt(fileName,dtype=float,skiprows=5,delimiter=',',unpack=True)

        # check whether the particle data is 6D
        arrayShape = np.shape(tmp6)
        numDimensions = arrayShape[0]
        if numDimensions != 6:
            msgBox = QtGui.QMessageBox()
            message  = 'ERROR --\n\n'
            message += '  Particle data in the selected CSV file is not 6D!\n'
            message += '  Please select another file.\n\n'
            msgBox.setText(message)
            msgBox.exec_()
            return

        # store the number of particles read from the file
        numParticles = arrayShape[1]

        # instantiate the particle bunch
        self.myBunch = beam.RbParticleBeam6D(numParticles)
        self.myBunch.setDesignMomentumEV(self.designMomentumEV)
        self.myBunch.setMassEV(self.eMassEV)

        # load particle array into the phase space object
        self.myBunch.getDistribution6D().getPhaseSpace6D().setArray6D(tmp6)

        self.putParametersInGUI(numParticles)


    def exportToFile(self, fileName = None):
        if not fileName:
            fileName = getSaveFileName(self, ['sdds', 'csv'])
            if not fileName:
                return

        if os.path.basename(fileName).startswith(self.parent.tabPrefix):
            name, ext = os.path.splitext(fileName)
            fileName = name + '+' + str(self.userInputEnabled()) + ext
            with open(fileName, 'w'):
                pass # create file in case no data to be saved

        if self.userInputEnabled():
            self.generateBunch() # save all particles

        if fileName.lower().endswith('csv'):
            self.saveToCSV(fileName)
        else:
            self.saveToSDDS(fileName)


    def saveToCSV(self, fileName = None):
        if not fileName:
            fileName = getSaveFileName(self, 'csv')
            if not fileName:
                return

        # make sure the top-level parameters are up-to-date
        self.designMomentumEV = convertUnitsStringToNumber(self.ui.designMomentum.text(), 'eV')
        self.totalCharge = convertUnitsStringToNumber(self.ui.totalCharge.text(), 'C')

        # create a header to identify this as a RadTrack file
        h1 = 'RadTrack,Copyright 2012-2014 by RadiaBeam Technologies LLC - All rights reserved (C)\n '
        # names of the top-level parameters
        h2 = 'p0 [eV],Q [C],mass [eV]\n '
        # values of the top-level parameters
        h3 = str(self.designMomentumEV)+','+str(self.totalCharge)+','+str(self.eMassEV)+'\n '
        # label the columns
        h4 = 'x,xp,y,yp,s,dp\n '
        # specify the units
        h5 = '[m],[rad],[m],[rad],[m],[rad]'
        # assemble the full header
        myHeader = h1 + h2 + h3 + h4 + h5

        # write particle data into the file
        
        # create local pointer to particle array
        userNumberOfParticles = int(self.ui.numPtcls.text())
        tmp6 = randomSampleOfBunch(self.myBunch.getDistribution6D().getPhaseSpace6D().getArray6D(), userNumberOfParticles)
        np.savetxt(fileName, tmp6.transpose(), fmt=str('%1.12e'), delimiter=',', comments='', header=myHeader)

    def saveToSDDS(self, sddsFileName = None):
        if not sddsFileName:
            sddsFileName = getSaveFileName(self, 'sdds')
            if not sddsFileName:
                return

        mySDDS = sdds.SDDS(0)
        mySDDS.description[0] = "RadTrack"
        mySDDS.description[1] = "Copyright 2013-2015 by RadiaBeam Technologies. All rights reserved."
        mySDDS.parameterName = ["designMomentumEV", "totalCharge", "eMassEV"]
        mySDDS.parameterData = [[self.designMomentumEV],
                                [self.totalCharge],
                                [self.eMassEV]]
        mySDDS.parameterDefinition = [["","","","",mySDDS.SDDS_DOUBLE,""],
                                      ["","","","",mySDDS.SDDS_DOUBLE,""],
                                      ["","","","",mySDDS.SDDS_DOUBLE,""]]
        mySDDS.columnName = ["x", "xp", "y", "yp", "t", "p"]

        try:
            tmp6 = self.myBunch.getDistribution6D().getPhaseSpace6D().getArray6D()

            if not self.userInputEnabled():
                tmp6 = randomSampleOfBunch(tmp6, int(self.ui.numPtcls.text()))
            
            #crude check, fails if bunch is shorter than 10 microns    
            if any(n>1e-5 for n in tmp6[4,:]):
                for i,t in enumerate(tmp6[4,:]):
                    tmp6[4,i]=t/self.c

            mySDDS.columnData = [ [list(tmp6[i,:])] for i in range(6)]

        except AttributeError: # myBunch is None
            mySDDS.columnData = [ [[]] for i in range(6)]

        mySDDS.columnDefinition = [["","m",  "","",mySDDS.SDDS_DOUBLE,0],
                                   ["","","","",mySDDS.SDDS_DOUBLE,0],
                                   ["","m",  "","",mySDDS.SDDS_DOUBLE,0],
                                   ["","","","",mySDDS.SDDS_DOUBLE,0],
                                   ["","s",  "","",mySDDS.SDDS_DOUBLE,0],
                                   ["","m_ec","","",mySDDS.SDDS_DOUBLE,0]]
        mySDDS.save(sddsFileName)

    def disableInput(self):
        for thing in [self.ui.twissTable, self.ui.twissTableZ, self.ui.offsetTable]:
            thing.setEnabled(False)

    def userInputEnabled(self):
        return self.ui.twissTable.isEnabled()
        
    def changeMass(self):
        name = self.ui.particleType.currentText()
        if name in ['Electron','Positron']:
            self.eMass=constants.m_e
            self.eMassEV=constants.physical_constants['electron mass energy equivalent in MeV'][0]*1e6
        elif name == 'Proton':
            self.eMass=constants.m_p
            self.eMassEV=constants.physical_constants['proton mass energy equivalent in MeV'][0]*1e6
        elif name == 'Muon':
            self.eMass=constants.physical_constants['muon mass']
            self.eMassEV=constants.physical_constants['muon mass energy equivalent in MeV'][0]*1e6


def randomSampleOfBunch(bunch, maxParticles):
    if bunch.shape[1] > maxParticles:
        return bunch[:, np.random.choice(bunch.shape[1], maxParticles, replace = False)]
    else:
        return bunch


def main():
    app = QtGui.QApplication(sys.argv)
    myapp = BunchTab()
    myapp.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
