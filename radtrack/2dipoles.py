# -*- coding: utf-8 -*-
"""Simulation of SR from 2 dipole edges

"""
from __future__ import absolute_import, division, print_function

from pykern.pkdebug import pkdc, pkdp
from pykern import pkarray

# Must be after srw_params import
import srwlib
from array import array
import uti_plot

# Initial coordinates of particle trajectory through the ID
part = srwlib.SRWLParticle()
part.x = 0.0 #beam.partStatMom1.x
part.y = 0.0 #beam.partStatMom1.y
part.xp = 0.0 #beam.partStatMom1.xp
part.yp = 0.0 #beam.partStatMom1.yp
part.gamma = 0.064/0.51099890221e-03 #Relative Energy beam.partStatMom1.gamma #
part.z = -0.0  #zcID #- 0.5*magFldCnt.MagFld[0].rz
part.relE0 = 1 #Electron Rest Mass
part.nq = -1 #Electron Charge
    
L_bend=0.05
L_drift=0.02
L_total=0.2 #2*L_bend+L_drift
bend1=srwlib.SRWLMagFldM(_G=-0.85, _m=1, _n_or_s='n', _Leff=L_bend, _Ledge=0.01)
bend2=srwlib.SRWLMagFldM(_G=0.85, _m=1, _n_or_s='n', _Leff=L_bend, _Ledge=0.01)
drift1 = srwlib.SRWLMagFldM(_G=0.0,_m=1, _n_or_s='n', _Leff=L_drift) #Drift
"""
       :param _G: field parameter [T] for dipole, [T/m] for quadrupole (negative means defocusing for x), [T/m^2] for sextupole, [T/m^3] for octupole
        :param _m: multipole order 1 for dipole, 2 for quadrupoole, 3 for sextupole, 4 for octupole
        :param _n_or_s: normal ('n') or skew ('s')
        :param _Leff: effective length [m]
        :param _Ledge: "soft" edge length for field variation from 10% to 90% [m]; G/(1 + ((z-zc)/d)^2)^2 fringe field dependence is assumed
"""
print('OK1')

arZero = array('d', [0]*3)
#arZero = array('d', [0]*1)
arZc = array('d', [-L_bend/2-L_drift/2, 0, L_bend/2+L_drift/2])
#arZc = array('d', [-0.035, 0, 0.035])
#arZc = array('d', [-L_bend])
magFldCnt = srwlib.SRWLMagFldC() #Container
magFldCnt.allocate(3) #Magnetic Field consists of 1 part
magFldCnt = srwlib.SRWLMagFldC([bend1, drift1, bend2], arZero, arZero, arZc)
#magFldCnt = srwlib.SRWLMagFldC([bend1], arZero, arZero, arZc)
"""
        :param _arMagFld: magnetic field structures array
        :param _arXc: horizontal center positions of magnetic field elements in arMagFld array [m]
        :param _arYc: vertical center positions of magnetic field elements in arMagFld array [m]
        :param _arZc: longitudinal center positions of magnetic field elements in arMagFld array [m]
"""
print('OK2')
arPrecPar = [1]  

#Definitions and allocation for the Trajectory waveform
# number of trajectory points along longitudinal axis
npTraj = 10001
partTraj = srwlib.SRWLPrtTrj()
print('OK3')
partTraj.partInitCond = part
partTraj.allocate(npTraj, True)
partTraj.ctStart = -L_total/2
partTraj.ctEnd = L_total/2 
print(partTraj)
print(magFldCnt)
partTraj = srwlib.srwl.CalcPartTraj(partTraj, magFldCnt, arPrecPar)
print('OK4')
ctMesh = [partTraj.ctStart, partTraj.ctEnd, partTraj.np]

uti_plot.uti_plot1d(partTraj.arX, ctMesh, ['ct [m]', 'Horizontal Position [m]'])
uti_plot.uti_plot1d(partTraj.arY, ctMesh, ['ct [m]', 'Vertical Position [m]'])
uti_plot.uti_plot1d(partTraj.arXp, ctMesh, ['ct [m]', 'Horizontal angle [rad]'])

uti_plot.uti_plot_show()
print('done')

#***********Electron Beam
elecBeam = srwlib.SRWLPartBeam()
elecBeam.Iavg = 0.1 #Average Current [A]
elecBeam.partStatMom1.x = part.x #Initial Transverse Coordinates (initial Longitudinal Coordinate will be defined later on) [m]
elecBeam.partStatMom1.y = part.y
elecBeam.partStatMom1.z = part.z #Initial Longitudinal Coordinate (set before the ID)
elecBeam.partStatMom1.xp = part.xp #Initial Relative Transverse Velocities
elecBeam.partStatMom1.yp = part.yp
elecBeam.partStatMom1.gamma = part.gamma #Relative Energy


wfr2 = srwlib.SRWLWfr() #For intensity distribution at fixed photon energy
wfr2.allocate(1, 401, 401) #Numbers of points vs Photon Energy, Horizontal and Vertical Positions
wfr2.mesh.zStart = 0.3 #Longitudinal Position [m] at which SR has to be calculated
wfr2.mesh.eStart = 2.1 #Initial Photon Energy [eV]
wfr2.mesh.eFin = 2.1 #Final Photon Energy [eV]
wfr2.mesh.xStart = -0.01 #Initial Horizontal Position [m]
wfr2.mesh.xFin = 0.01 #Final Horizontal Position [m]
wfr2.mesh.yStart = -0.01 #Initial Vertical Position [m]
wfr2.mesh.yFin = 0.01 #Final Vertical Position [m]
wfr2.partBeam = elecBeam

meth = 2 #SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
relPrec = 0.01 #relative precision
zStartInteg = partTraj.ctStart #0 #longitudinal position to start integration (effective if < zEndInteg)
zEndInteg =  partTraj.ctEnd #0 #longitudinal position to finish integration (effective if > zStartInteg)
npTraj = 2000 #Number of points for trajectory calculation 
useTermin = 0 #Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
sampFactNxNyForProp = 0 #sampling factor for adjusting nx, ny (effective if > 0)
arPrecPar = [meth, relPrec, zStartInteg, zEndInteg, npTraj, useTermin, sampFactNxNyForProp]

srwlib.srwl.CalcElecFieldSR(wfr2, 0, magFldCnt, arPrecPar)
print('done')
print('   Extracting Intensity from calculated Electric Field ... ', end='')
arI2 = array('f', [0]*wfr2.mesh.nx*wfr2.mesh.ny) #"flat" array to take 2D intensity data
srwlib.srwl.CalcIntFromElecField(arI2, wfr2, 6, 0, 3, wfr2.mesh.eStart, 0, 0)

uti_plot.uti_plot2d(arI2, [1000*wfr2.mesh.xStart, 1000*wfr2.mesh.xFin, wfr2.mesh.nx], 
[1000*wfr2.mesh.yStart, 1000*wfr2.mesh.yFin, wfr2.mesh.ny], 
['Horizontal Position [mm]', 'Vertical Position [mm]', 
'Intensity at ' + str(wfr2.mesh.eStart) + ' eV'])

#arI1 = array('f', [0]*wfr2.mesh.nx)
#uti_plot1d(arI1, [wfr1.mesh.eStart, wfr1.mesh.eFin, wfr1.mesh.ne], 
#['Photon Energy [eV]', 'Intensity [ph/s/.1%bw/mm^2]', 'On-Axis Spectrum'])

uti_plot.uti_plot_show()
print('done')