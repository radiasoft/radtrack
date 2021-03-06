# -*- coding: utf-8 -*-
"""SRW Tab

:copyright: Copyright (c) 2015 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkdebug import pkdc, pkdp

from radtrack.rt_qt import QtGui

from radtrack import srw_controller


class RbSrwTab(QtGui.QWidget):
    defaultTitle = 'SRW'
    acceptsFileTypes = []
    task = 'Run an SRW simulation'
    category = 'simulations'

    def __init__(self, parent):
        super(RbSrwTab, self).__init__(parent)
        self.complexity_widget = QtGui.QCheckBox(self)
        self.complexity_widget.setText('Single-Particle')
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.complexity_widget)
        self.control = srw_controller.Base()
        layout.addWidget(self.control.init_widget(self))
        self.parent = parent

    def exportToFile(self, fileName = None):
        with open(fileName, 'w'):
            pass

    def importFile(self, fileName = None):
        pass


if '__main__' == __name__:
    from radtrack import rt_qt
    rt_qt.run_app(lambda: RbSrwTab(None))
