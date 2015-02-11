"""
Python class to emulate XGenesis postprocessing of GENESIS1.3 simulations.
Parses the GENESIS .out file

Copyright (c) RadiaBeam Technologies, 2015. All rights reserved.
"""
__author__ = 'swebb'
import numpy as np
from matplotlib import pyplot as plt

class RbXGenesisTInd:

    def __init__(self):
        self.file_open = False
        self.data_set = {}
        self.data_label = {}
        self.data_set['z']     = -1
        self.data_label['z'] = 'z [m]'
        self.data_set['aw']    = -1
        self.data_label['aw'] = 'a_w'
        self.data_set['QF']    = -1
        self.data_label['QF'] = 'dB/dx [T/m]'
        self.data_set['Power'] = -1
        self.data_label['Power'] = 'P [W]'
        self.data_set['Increment'] = -1
        self.data_label['Increment'] = '(1/P) dP/dz [m^-1]'
        self.data_set['p_mid'] = -1
        self.data_label['p_mid'] = '???'
        self.data_set['Phase'] = -1
        self.data_label['Phase'] = u'\u03A6 [rad]'
        self.data_set['Rad. Size'] = -1
        self.data_label['Rad. Size'] = 'RMS radiation width [m]'
        self.data_set['Far Field'] = -1
        self.data_label['Far Field'] = u'dP/d\u03A9 [W/rad^2]'
        self.data_set['Energy'] = -1
        self.data_label['Energy'] = u'(\u03B3 - \u03B3\u2080)/mc^2'
        self.data_set['Energy Spread'] = -1
        self.data_label['Energy Spread'] = u'\u03C3\u2091 [keV]'
        self.data_set['X Beam Size'] = -1
        self.data_label['X Beam Size'] = u'\u03C3_x [m]'
        self.data_set['Y Beam Size'] = -1
        self.data_label['Y Beam Size'] =  u'\u03C3_y [m]'
        self.data_set['X Centroid'] = -1
        self.data_label['X Centroid'] = '<x> [m]'
        self.data_set['Y Centroid'] = -1
        self.data_label['Y Centroid'] = '<y> [m]'
        self.data_set['Bunching'] = -1
        self.data_label['Bunching'] = u'|<exp(i \u03B8)>|'
        self.data_set['Error'] = -1
        self.data_label['Error'] = u'\u0394P/P [%]'

        self.semilog = False
        self.perrorbars = False


    def parse_output(self, filename):
        """
        Parse a GENESIS .out file
        :param filename:
        :return:
        """

        genesis_file = open(filename, 'r')
        line = genesis_file.readline()
        # Advance to find where the number of data entries are
        while not 'entries per record' in line:
            line = genesis_file.readline()
        num_steps = int(line.split()[0])
        for key in self.data_set.keys():
            self.data_set[key] = np.zeros(num_steps-1)

        first_three_keys = ['z', 'aw', 'QF']
        last_keys = ['Power', 'Increment', 'p_mid', 'Phase', 'Rad. Size',
                     'Energy', 'Bunching', 'X Beam Size', 'Y Beam Size',
                     'Error', 'X Centroid', 'Y Centroid', 'Energy Spread',
                     'Far Field']

        # Advance to the first set of data
        while not 'z[m]' in line:
            line = genesis_file.readline()


        # Read in the first three keys first
        for lineIdx in range(0, num_steps-1):
            line = genesis_file.readline()
            for idx in range(0, len(first_three_keys)-1):
                self.data_set[first_three_keys[idx]][lineIdx] = float(
                    line.split()[idx])

        while not 'power' in line:
            line = genesis_file.readline()

        for lineIdx in range(0, num_steps-1):
            line = genesis_file.readline()
            for idx in range(0, len(last_keys)):
                self.data_set[last_keys[idx]][lineIdx] = float(line.split()[
                    idx])

        genesis_file.close()


    def set_semilog(self):
        """
        Make the y-axis logarithmic for plotting
        :return:
        """
        if self.semilog == False:
            self.semilog = True
        else:
            self.semilog = False


    def set_ploterrors(self):
        """
        Plot error bars on the power
        :return:
        """
        if self.perrorbars == False:
            self.perrorbars = True
        else:
            self.perrorbars = False


    def plot_data(self, x_axis, y_axis):
        """
        Plot data from the keys given as arguments
        :param x_axis:
        :param y_axis:
        :return: plot
        """
        if not x_axis in self.data_set.keys():
            msg = 'Data type', x_axis, 'not recognized'
            Exception(msg)
        if not y_axis in self.data_set.keys():
            msg = 'Data type', y_axis, 'not recognized'
            Exception(msg)

        plt.plot(self.data_set[x_axis], self.data_set[y_axis])

        if self.perrorbars and y_axis == 'Power':
            power_error = self.data_set['Error']*self.data_set['Power']/100.
            plt.errorbar(self.data_set[x_axis], self.data_set[y_axis],
                            yerr=power_error, ecolor='r')

        if self.semilog:
            plt.yscale('log')

        plt.xlabel(self.data_label[x_axis])
        plt.ylabel(self.data_label[y_axis])
        plt.tight_layout()
        plt.show()