# -*- coding: utf-8 -*-
"""
:copyright: Copyright (c) 2013-2015 RadiaBeam Technologies LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

from PyQt4 import QtCore, QtGui

from radtrack import genesis_pane
from radtrack import genesis_params
from radtrack import rt_controller
from radtrack import rt_params
from radtrack import rt_popup
from radtrack import rt_enum
from radtrack.util.simulationResultsTools import results_context_menu, add_result_file, processSimulationEndStatus
from radtrack.BunchTab import BunchTab
from pykern import pkcollections
from enum import Enum
import os, shutil, glob


class Base(rt_controller.Controller):
    """Implements contol flow for Genesis tab"""
    ACTION_NAMES = ('Undulator', 'Beam', 'Radiation', 'Particle_Loading','Mesh','Focusing', 'Time_Dependence',
        'Simulation_Control','Scan','IO_Control','Simulate')

    FILE_PREFIX = 'genesis'
    INPUT = None

    def init(self, parent_widget=None):
        self.decl = rt_params.declarations(self.FILE_PREFIX)['root']
        self.defaults = rt_params.defaults(self.FILE_PREFIX, self.decl)
        self.params = rt_params.init_params(self.defaults)
        self._view = genesis_pane.View(self, parent_widget)
        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.newStdInfo)
        self.process.readyReadStandardError.connect(self.newStdError)
        self.process.finished.connect(self.list_result_files)
        self.process.error.connect(self.display_error)

        self._view._result_text['output'].customContextMenuRequested.connect(
                lambda position : results_context_menu(self._view._result_text['output'],
                                                       self._view.parentWidget().parent,
                                                       position))

        self.w = {}
        return self._view

    def action_beam(self):
        self._pop_up('beam')

    def action_undulator(self):
        self._pop_up('undulator')

    def action_radiation(self):
        self._pop_up('radiation')

    def action_particle_loading(self):
        self._pop_up('particle_loading')

    def action_mesh(self):
        self._pop_up('mesh')

    def action_focusing(self):
        self._pop_up('focusing')

    def action_time_dependence(self):
        self._pop_up('time_dependence')

    def action_simulation_control(self):
        self._pop_up('simulation_control')

    def action_scan(self):
        self._pop_up('scan')

    def action_io_control(self):
        self._pop_up('io_control')

    def msg(self, m):
        self._view._result_text['simulation'].append(m)

    def write_simulation_file(self, fileName):
        self.w.update(genesis_params.to_beam(self.params.beam))
        self.w.update(genesis_params.to_undulator(self.params.undulator))
        self.w.update(genesis_params.to_radiation(self.params.radiation))
        self.w.update(genesis_params.to_particle_loading(self.params.particle_loading))
        self.w.update(genesis_params.to_mesh(self.params.mesh))
        self.w.update(genesis_params.to_focusing(self.params.focusing))
        self.w.update(genesis_params.to_time(self.params.time_dependence))
        self.w.update(genesis_params.to_sim_control(self.params.simulation_control))
        self.w.update(genesis_params.to_scan(self.params.scan))
        self.w.update(genesis_params.to_io_control(self.params.io_control))

        with open(fileName,'w') as f:
            if not self.INPUT:
                f.write(' $newrun \n')
                for parameter, data in self.w.items():
                    if isinstance(data, rt_enum.Enum):
                        f.write(' {}={}\n'.format(parameter, data.value))
                    elif isinstance(data, bool):
                        f.write(' ' + parameter + '=' + str(int(data)) + '\n')
                    elif isinstance(data, list):
                        f.write(' ' + parameter + '=' + ' '.join([str(x) for x in data]) + '\n')
                    elif isinstance(data, basestring) and data:
                        f.write(' ' + parameter + "='" + data + "'\n")
                    elif data:
                        f.write(' ' + parameter + "=" + str(data) + "\n")
                f.write(' $end \n')
            else:
                f.write(self.INPUT)
 
    def action_simulate(self):
        self._view._result_text['simulation'].clear()
        self.msg('Writing Genesis IN file...')
        self.write_simulation_file('genesis_run.in')
        self.msg('Finished')
        self.msg('\nRunning Genesis...')
        self.msg(self.INPUT)
        print(self.INPUT)
        self.process.start('genesis',['genesis_run.in']) # add option so files start with common name

    def list_result_files(self):
        if self.process.exitStatus() != QtCore.QProcess.NormalExit:
            processSimulationEndStatus(self.process.error(), 'Genesis', self.msg)
        else:
            self._view._result_text['output'].clear()
            self.msg('Genesis finished!')
            for output_file in glob.glob('genesis_run.*'):
                add_result_file(self._view._result_text['output'], output_file, output_file)

            for key in ['OUTPUTFILE', 'MAGOUTFILE']:
                if self.w[key]:
                    for output_file in glob.glob(self.w[key] + '*'):
                        add_result_file(self._view._result_text['output'], output_file, output_file)

    def display_error(self, error):
        processSimulationEndStatus(error, 'Genesis', self.msg)

    def decl_is_visible(self, decl):
        return True

    def iter_default_children(self, defaults):
        res = pkcollections.map_values(defaults)
        return iter(res)

    def newStdInfo(self):
        """Callback with simulation stdout text"""
        newString = str(self.process.readAllStandardOutput())
        self.msg(newString)

    def newStdError(self):
        """Callback with simulation stderr text"""
        newString = str(self.process.readAllStandardError())
        self.msg(newString)

    def name_to_action(self, name):
        """Returns button action"""
        return getattr(self, 'action_' + name.lower())

    def register_static_widget(self, widget):
        pass

    def _pop_up(self, which):
                    
        if which == 'beam':
            fromtab=which
        #elif which == 'undulator':
        #    fromtab=which
        else: fromtab=False
        pu = rt_popup.Window(
            self.defaults[which],
            self.params[which],
            controller=self,
            parent=self._view,
            tabinput=fromtab,
        )
        for i in pu._form._buttons.buttons():
            if 'Retrieve' in i.text():
                i.clicked.connect(lambda:self.from_tab('beam',pu))
        
        if pu.exec_():
            self.params[which] = pu.get_params()
            
            if self.INPUT:
                inv_to_gensis = {v:k for k,v in genesis_params.to_genesis().items()}
                in_list = self.INPUT.split('\n')
                for w,e in pu.get_params().items():
                    gkey = inv_to_gensis[w]
                    for k,v in enumerate(in_list):
                        if gkey in v:
                            if 'LOUT' in gkey:
                                in_list[k]=' ' + gkey + '=' + ' '.join([str(int(self.params[which]['output_parameters'][str(x)])) for x in e])
                            elif self.decl[which][w].py_type is bool:
                                in_list[k]=' '+gkey+'='+str(int(e))
                            elif self.decl[which][w].py_type is str:
                                in_list[k]=' '+gkey+'='+"'"+str(e)+"'"
                            else:
                                in_list[k]=' '+gkey+'='+str(e)
                            break
                if which=='io_control':
                    in_list.insert(int(len(in_list)/2)," OUTPUTFILE= '"+self.params[which]['output_filename']+"'")
                self.INPUT = ''.join(x+'\n' for x in in_list)
            if which is 'undulator' and self.params[which]['vertical_focus']+self.params[which]['horizontal_focus']!=1.0:
                box = QtGui.QMessageBox()
                box.setIcon(QtGui.QMessageBox.Warning)
                box.setText('Sum of undulator horizontal and vertical focus should equal 1.')
                box.exec_()
            elif which is 'beam' and self.params[which]['num_particle']%(4*self.params['particle_loading']['num_bins'])!= 0:
                box = QtGui.QMessageBox()
                box.setIcon(QtGui.QMessageBox.Critical)
                box.setText('Number of Particles must be a multiple of 4*Number of Bins for Phase. \n (specified in particle loading)')
                box.exec_()
            elif which is 'particle_loading' and self.params[which]['num_bins']<2*self.params['radiation']['num_harmonic']:
                box = QtGui.QMessageBox()
                box.setIcon(QtGui.QMessageBox.Warning)
                box.setText('Number of Bins must be greater than or equal to 2*Harmonic Number. (specified in radiation)')
                box.exec_()
            elif which is 'mesh' and self.params[which]['direct_grid_size'] != 0:
                box = QtGui.QMessageBox()
                box.setIcon(QtGui.QMessageBox.Information)
                box.setText('Genesis Grid Size Automation Disabled.')
                box.exec_()
                
    def from_tab(self,tabinput,pu):
        def importBunch2pu(pu,reader):
            rms = reader.myBunch.getDistribution6D().calcRmsValues6D()
            average = reader.myBunch.getDistribution6D().calcAverages6D() 
            for j in pu._form._fields.keys():
                key=j.replace('beam.','')
                if 'num' in key:
                    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getDistribution6D().getPhaseSpace6D().getNumParticles()))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'gamma' in key:
                    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getGamma0())) 
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'spread' in key:
                    pu._form._fields[j]['widget'].setText(str(rms[5]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'horizontal_width' in key:
                    pu._form._fields[j]['widget'].setText(str(rms[0]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'vertical_width' in key:
                    pu._form._fields[j]['widget'].setText(str(rms[2]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'horizontal_emittance' in key:
                    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getTwissParamsByName2D('twissX').getEmitRMS()))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'vertical_emittance' in key:
                    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getTwissParamsByName2D('twissY').getEmitRMS()))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'horizontal_alpha' in key:
                    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getTwissParamsByName2D('twissX').getAlphaRMS()))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'vertical_alpha' in key:
                    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getTwissParamsByName2D('twissY').getAlphaRMS()))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'horizontal_coord' in key:
                    pu._form._fields[j]['widget'].setText(str(average[0]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'vertical_coord' in key:
                    pu._form._fields[j]['widget'].setText(str(average[2]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'horizontal_angle' in key:
                    pu._form._fields[j]['widget'].setText(str(average[1]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                elif 'vertical_angle' in key:
                    pu._form._fields[j]['widget'].setText(str(average[3]))
                    #print(key,':',pu._form._fields[j]['widget'].text())
                #elif 'current' in key:
                #    pu._form._fields[j]['widget'].setText(str(reader.myBunch.getCurrent()))
                        
        choices = []
        for j in range(self._view.parent.parent.tabWidget.count()):
            T=self._view.parent.parent.tabWidget.tabText(j)
            if 'Transport' not in T and self._view.parent.parent.tabWidget.currentIndex() != j:
                if 'Genesis' in T or 'SRW' in T or 'Elegant' in T or 'Bunch' in T:
                    choices.append([j,T])
        box = QtGui.QMessageBox(QtGui.QMessageBox.Question, '', tabinput+'s available.\nRetrieve from which tab?')
        responses = [box.addButton(j[1], QtGui.QMessageBox.ActionRole) for j in choices] + [box.addButton(QtGui.QMessageBox.Cancel)]
        box.exec_()
        try:
            selected=choices[responses.index(box.clickedButton())]
            if 'Elegant' in selected[1]:
                if self._view.parent.parent.tabWidget.widget(selected[0]).ui.simulationResultsListWidget.count()!=0:
                    for i in range(self._view.parent.parent.tabWidget.widget(selected[0]).ui.simulationResultsListWidget.count()):
                        if 'phase space' in self._view.parent.parent.tabWidget.widget(selected[0]).ui.simulationResultsListWidget.item(i).text():
                            ops=self._view.parent.parent.tabWidget.widget(selected[0]).ui.simulationResultsListWidget.item(i).data(QtCore.Qt.UserRole).toString()
                            reader = BunchTab()
                            reader.readFromSDDS(ops)
                            reader.calculateTwiss()
                            importBunch2pu(pu,reader)
                            break
                else:
                    error=QtGui.QMessageBox()
                    error.setIcon(QtGui.QMessageBox.Critical)
                    error.setText('No Resultant Output Phase Space')
                    error.exec_()
            elif 'Bunch' in selected[1]:
                importBunch2pu(pu,self._view.parent.parent.tabWidget.widget(selected[0]))
            else:
                #inv_to_gensis = {v:k for k,v in genesis_params.to_genesis().items()}
                #print(inv_to_gensis['current'])
                #print(genesis_params.to_genesis()['current'])
                for j in pu._form._fields.keys():
                    try:
                        if tabinput == 'beam':
                            pu._form._fields[j]['widget'].setText(str(self._view.parent.parent.tabWidget.widget(selected[0]).control.params.beam[j.replace('beam.','')]))
                        elif tabinput == 'undulator': 
                            #self._form._fields[i]['widget'].setText(str(self.parent.parentWidget().parent.tabWidget.widget(choices[responses.index(box.clickedButton())][0]).control.params.radiation_source.undulator[i.replace('undulator.','')]))
                            pass
                    except KeyError:
                        pass #unmatched key(from declarations) between tabs
        except IndexError:
            return       #Cancel selected 
                      
    def get_in(self,phile):
        def param_update(key,value):
            D=genesis_params.to_genesis()
            for i in self.decl:
                try:
                    if D[key] in self.decl[i].children:
                    #compares to both rt_enum and Enum unsure of what radtrack enumerated type is so compare to both
                        if self.decl[i][D[key]].py_type in [int,float,bool]:
                            self.params[i][D[key]]=self.decl[i][D[key]].py_type(float(value.replace('D','E')))  
                        elif self.decl[i][D[key]].py_type is str:
                            self.params[i][D[key]] = value.replace("'",'')    
                            print(self.params[i][D[key]])                        
                        elif isinstance(self.params[i][D[key]],rt_enum.Enum) or isinstance(self.params[i][D[key]],Enum):
                            self.params[i][D[key]] = list(self.decl[i][D[key]].py_type)[int(float(value.replace('D','E')))]
                        elif self.decl[i][D[key]].py_type is list:
                            op_children=value.split()
                            for n,j in enumerate(self.params[i][D[key]]):
                                try:
                                    self.params[i][D[key]][j]=bool(int(op_children[n]))
                                except IndexError:
                                    print(IndexError)
                                    if n==18:
                                        error=QtGui.QMessageBox()
                                        error.setIcon(QtGui.QMessageBox.Warning)
                                        error.setText('Not enough parameters for LOUT')
                                        error.exec_()
                                    #raise RuntimeError('Not enough parameters for LOUT')
                except KeyError:
                    print(key)

        def parse(line):
            name,val=line.split('=')
            name = name.strip()
            val = val.strip().strip(',.\'"')
            param_update(name,val)

            # These parameters specify other input files. Copy them into the session directory as well.
            if name in ['MAGINFILE', 'BEAMFILE', 'RADFILE', 'DISTFILE', 'FIELDFILE', 'PARTFILE']:
                originalLocation = os.path.join(sourceDirectory, val)
                if not os.path.exists(originalLocation):
                    QtGui.QMessageBox.warning(self._view,
                                              'Missing File Reference',
                                              'The main input file references a file, ' + 
                                              val +
                                              ', that does not exist. Genesis will likely not run successfully.')
                    return
                importDestination = os.path.join(self._view.parentWidget().parent.sessionDirectory, val)
                if originalLocation == importDestination:
                    return
                if not os.path.exists(os.path.dirname(importDestination)):
                    os.makedirs(os.path.dirname(importDestination))
                if os.path.exists(importDestination):
                    os.remove(importDestination)
                shutil.copy2(originalLocation, importDestination)
                
        def sdds2ascii(philename):
            sa='sdds2plaindata {filename} genesis6D.dist -outputMode=ascii -separator="  " -column=x -column=xp -column=y -column=yp -column=t -column=p'
            sa.format(filename=philename)
            return sa

        sourceDirectory = os.path.dirname(phile.name)
        dollar = 0
        if 'in' in os.path.splitext(phile.name)[1]:
            self.INPUT = ''
            for line in phile:
                if '$' not in line:
                    if line.count(',') > 1:
                        for i in line.rstrip('\n').split(','):
                            try:
                                parse(i)
                                self.INPUT=self.INPUT+' '+i +'\n'
                            except ValueError:
                                print(i)   
                    else:
                        parse(line)  
                        self.INPUT+=line 
                else:
                    self.INPUT+=line
                    dollar+=1
                    if dollar == 2:
                        break
            self.msg(self.INPUT) 
                     
        elif 'out' in os.path.splitext(phile.name)[1]:       
            reader = BunchTab()
            reader.readFromSDDS(phile.name)
            reader.calculateTwiss()
            rms = reader.myBunch.getDistribution6D().calcRmsValues6D()
            average = reader.myBunch.getDistribution6D().calcAverages6D()
            #update in memory genesis parameters
            self.params['beam']['num_particle']=reader.myBunch.getDistribution6D().getPhaseSpace6D().getNumParticles()
            self.params['beam']['gamma']=reader.myBunch.getGamma0()
            self.params['beam']['rms_energy_spread']=rms[5]
            self.params['beam']['rms_horizontal_width']=rms[0]
            self.params['beam']['rms_vertical_width']=rms[2]
            self.params['beam']['rms_horizontal_emittance']=reader.myBunch.getTwissParamsByName2D('twissX').getEmitRMS()
            self.params['beam']['rms_vertical_emittance']=reader.myBunch.getTwissParamsByName2D('twissY').getEmitRMS()
            self.params['beam']['horizontal_alpha']=reader.myBunch.getTwissParamsByName2D('twissX').getAlphaRMS()
            self.params['beam']['vertical_alpha']=reader.myBunch.getTwissParamsByName2D('twissY').getAlphaRMS()
            self.params['beam']['horizontal_coord']=average[0]
            self.params['beam']['vertical_coord']=average[2]
            self.params['beam']['horizontal_angle']=average[1]
            self.params['beam']['vertical_angle']=average[3]
            #self.params['beam']['current']=reader.myBunch.getCurrent()
            #updates imported genesis file input parameters 
            if self.INPUT:
                inv_to_gensis = {v:k for k,v in genesis_params.to_genesis().items()}
                in_list = self.INPUT.split('\n')
                #in_list.insert(int(len(in_list)/2)," DISTFILE= '"+os.path.basename(phile.name)+"'")
                for w in self.decl['beam'].keys():
                    gkey = inv_to_gensis[w]
                    for k,v in enumerate(in_list):
                        if gkey in v:
                            in_list[k]=' '+gkey+'='+str(self.params['beam'][w])
                            break                 
                self.INPUT = ''.join(x+'\n' for x in in_list)
                self.msg(self.INPUT)

        elif 'dist' in os.path.splitext(phile.name)[1]:
            if self.INPUT:
                inv_to_gensis = {v:k for k,v in genesis_params.to_genesis().items()}
                in_list = self.INPUT.split('\n')
                in_list.insert(int(len(in_list)/2)," DISTFILE= '"+os.path.basename(phile.name)+"'")
                
                self.params['io_control']['phase_file']=os.path.basename(phile.name)
                                
                self.INPUT = ''.join(x+'\n' for x in in_list)
                self.msg(self.INPUT)            
            
