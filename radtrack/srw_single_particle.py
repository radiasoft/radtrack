# -*- coding: utf-8 -*-
u"""Single particle SRW Pane

:copyright: Copyright (c) 2013-2015 RadiaBeam Technologies LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

import copy

from pykern import pkarray
from pykern import pkcollections
from pykern.pkdebug import pkdc, pkdp

from radtrack import srw_params

import srwlib
import uti_plot


def simulate(params, msg_callback):
    """Run a single-particle (thin) simulation and return results

    Args:
        params (OrderedMapping): map of parameters
        msg_callback (function): Called at various stages to log output

    Returns:
        OrderedMapping: results and params (see code for format)
    """
    p = pkcollections.OrderedMapping()
    for k in 'polarization', 'intensity', 'simulation_kind', 'wavefront':
        v = params[k]
        p[k] = v.value if hasattr(v, 'value') else v
    if params.radiation_source == 'UNDULATOR':
        pkcollections.mapping_merge(
        p, srw_params.to_undulator_single_particle(params.source))
    elif params.radiation_source == 'DUAL_DIPOLE':
        pkcollections.mapping_merge(
        p,srw_params.to_dipoles(params.source))
    elif params.radiation_source == 'MULTIPOLE':
        pkcollections.mapping_merge(
        p,srw_params.to_multipole(params.source))
    else:
        raise AssertionError('{}: unknown radiation_source'.format(params.radiation_source))

    p.arPrecPar = srw_params.to_precision_single_particle(params.precision)
    p.wfrE = srw_params.to_wavefront_single_particle(p.wavefront)
    p.wfrE.partBeam = srw_params.to_beam(params.beam)
    p.wfrXY = srw_params.to_wavefront_single_particle(p.wavefront)
    p.wfrXY.partBeam = srw_params.to_beam(params.beam)
    p.beam = srw_params.to_beam(params.beam)
    p.plots = []
    skv = p.simulation_kind
    if params.simulation_kind == 'E':
        msg_callback('Performing Electric Field (spectrum vs photon energy) calculation')
        srwlib.srwl.CalcElecFieldSR(p.wfrE, 0, p.magFldCnt, p.arPrecPar)
        msg_callback('Extracting Intensity from calculated Electric Field')
        p.arI1 = pkarray.new_float([0]*p.wfrE.mesh.ne)
        srwlib.srwl.CalcIntFromElecField(
            p.arI1, p.wfrE, p.polarization, p.intensity, skv, p.wfrE.mesh.eStart, 0, 0)
        p.plots.append([
            uti_plot.uti_plot1d,
            p.arI1,
            [p.wfrE.mesh.eStart, p.wfrE.mesh.eFin, p.wfrE.mesh.ne],
            ['Photon energy, eV','Spectral intensity, ph/s/0.1%BW','Intensity vs photon energy'],
        ])
    elif params.simulation_kind == 'X':
        msg_callback('Performing Electric Field (intensity vs x-coordinate) calculation')
        srwlib.srwl.CalcElecFieldSR(p.wfrXY, 0, p.magFldCnt, p.arPrecPar)
        msg_callback('Extracting Intensity from calculated Electric Field')
        p.arI1 = pkarray.new_float([0]*p.wfrXY.mesh.nx)
        srwlib.srwl.CalcIntFromElecField(p.arI1, p.wfrXY, p.polarization, p.intensity, skv, 0, p.wfrXY.mesh.xStart, 0)
        p.plots.append([
            uti_plot.uti_plot1d,
            p.arI1,
            [p.wfrXY.mesh.xStart, p.wfrXY.mesh.xFin, p.wfrXY.mesh.nx],
            ['Horizontal Position [m]','Spectral intensity, ph/s/0.1%BW','Intensity vs x-coordinate'],
        ])
    elif params.simulation_kind == 'Y':
        msg_callback('Performing Electric Field (intensity vs y-coordinate) calculation')
        srwlib.srwl.CalcElecFieldSR(p.wfrXY, 0, p.magFldCnt, p.arPrecPar)
        msg_callback('Extracting Intensity from calculated Electric Field')
        p.arI1 = pkarray.new_float([0]*p.wfrXY.mesh.ny)
        srwlib.srwl.CalcIntFromElecField(p.arI1, p.wfrXY, p.polarization, p.intensity, skv, 0, p.wfrXY.mesh.yStart, 0)
        p.plots.append([
            uti_plot.uti_plot1d,
            p.arI1,
            [p.wfrXY.mesh.yStart, p.wfrXY.mesh.yFin, p.wfrXY.mesh.ny],
            ['Vertical Position [m]','Spectral intensity, ph/s/0.1%BW','Intensity vs y-coordinate'],
        ])
    elif params.simulation_kind == 'X_AND_Y':
        msg_callback('Performing Electric Field (intensity vs x- and y-coordinate) calculation')
        #srwlib.srwl.CalcElecFieldSR(p.wfrXY, 0, p.magFldCnt, p.arPrecPar)
        print(p.magFldCnt.__dict__)
        '''
        srwlib.srwl.CalcElecFieldSR(p.wfrXY,p.beam,p.magFldCnt, p.arPrecPar)
        msg_callback('Extracting Intensity from calculated Electric Field')
        p.arI1 = pkarray.new_float([0]*p.wfrXY.mesh.nx*p.wfrXY.mesh.ny)
        srwlib.srwl.CalcIntFromElecField(p.arI1, p.wfrXY, p.polarization, p.intensity, skv, p.wfrXY.mesh.eStart, p.wfrXY.mesh.xStart, p.wfrXY.mesh.yStart)
        p.plots.append([
            uti_plot.uti_plot2d,
            p.arI1,
            [1*p.wfrXY.mesh.xStart, 1*p.wfrXY.mesh.xFin, p.wfrXY.mesh.nx],
            [1*p.wfrXY.mesh.yStart, 1*p.wfrXY.mesh.yFin, p.wfrXY.mesh.ny],
            ['Horizontal Position [m]', 'Vertical Position [m]', 'Intensity at ' + str(p.wfrXY.mesh.eStart) + ' eV'],
        ])'''

    elif params.simulation_kind == 'E_AND_X':
        msg_callback('Performing Electric Field (intensity vs energy- and x-coordinate) calculation')
        srwlib.srwl.CalcElecFieldSR(p.wfrXY, 0, p.magFldCnt, p.arPrecPar)
        msg_callback('* Extracting Intensity from calculated Electric Field')
        p.arI1 = pkarray.new_float([0]*p.wfrXY.mesh.ne*p.wfrXY.mesh.nx)
        srwlib.srwl.CalcIntFromElecField(p.arI1, p.wfrXY, p.polarization, p.intensity, skv, p.wfrXY.mesh.eStart, p.wfrXY.mesh.xStart, p.wfrXY.mesh.yStart)
        p.plots.append([
            uti_plot.uti_plot1d,
            p.arI1,
            [1*p.wfrXY.mesh.eStart, 1*p.wfrXY.mesh.eFin, p.wfrXY.mesh.ne],
            [1*p.wfrXY.mesh.xStart, 1*p.wfrXY.mesh.xFin, p.wfrXY.mesh.nx],
            ['Energy [eV]', 'Horizontal Position [m]', 'Intensity integrated from ' + str(p.wfrXY.mesh.yStart) + ' to ' + str(p.wfrXY.mesh.yFin) + ' ,m in y-coordinate'],
        ])
    elif params.simulation_kind == 'E_AND_Y':
        msg_callback('Performing Electric Field (intensity vs energy- and y-coordinate) calculation')
        srwlib.srwl.CalcElecFieldSR(p.wfrXY, 0, p.magFldCnt, p.arPrecPar)
        msg_callback('Extracting Intensity from calculated Electric Field')
        p.arI1 = pkarray.new_float([0]*p.wfrXY.mesh.ne*p.wfrXY.mesh.ny)
        srwlib.srwl.CalcIntFromElecField(p.arI1, p.wfrXY, p.polarization, p.intensity, skv, p.wfrXY.mesh.eStart, p.wfrXY.mesh.xStart, p.wfrXY.mesh.yStart)
        p.plots.append([
            uti_plot.uti_plot1d,
            p.arI1,
            [1*p.wfrXY.mesh.eStart, 1*p.wfrXY.mesh.eFin, p.wfrXY.mesh.ne],
            [1*p.wfrXY.mesh.yStart, 1*p.wfrXY.mesh.yFin, p.wfrXY.mesh.ny],
            ['Energy [eV]', 'Vertical Position [m]', 'Intensity integrated from ' + str(p.wfrXY.mesh.xStart) + ' to ' + str(p.wfrXY.mesh.xFin)+ ' ,m in x-coordinate'],
        ])
    else:
        raise AssertionError('{}: invalid p.simulation_kind'.format(params.simulation_kind))
    return p

def _trajectory(p):
    # Done specifying undulator mag field
    # Initial coordinates of particle trajectory through the ID
    part = srwlib.SRWLParticle()
    part.x = p.beam.partStatMom1.x
    part.y = p.beam.partStatMom1.y
    part.xp = p.beam.partStatMom1.xp
    part.yp = p.beam.partStatMom1.yp
    part.gamma = p.beam.partStatMom1.gamma #3/0.51099890221e-03 #Relative Energy beam.partStatMom1.gamma
    part.relE0 = 1
    part.nq = -1
    zcID = 0
    # number of trajectory points along longitudinal axis
    npTraj = 100
    #Definitions and allocation for the Trajectory waveform
    part.z = zcID #- 0.5*magFldCnt.MagFld[0].rz
    p.partTraj = srwlib.SRWLPrtTrj()
    p.partTraj.partInitCond = part
    p.partTraj.allocate(npTraj, True)
    p.partTraj.ctStart = -0.1 #-0.55 * p.und.nPer * p.und.per
    p.partTraj.ctEnd = 0.1    #0.55 * p.und.nPer * p.und.per #magFldCnt.MagFld[0].rz
    p.partTraj = srwlib.srwl.CalcPartTraj(p.partTraj, p.magFldCnt, p.arPrecPar)
    p.ctMesh = [p.partTraj.ctStart, p.partTraj.ctEnd, p.partTraj.np]

    uti_plot.uti_plot1d(p.partTraj.arX, ctMesh, ['ct [m]', 'Horizontal Position [m]'])
    uti_plot.uti_plot1d(p.partTraj.arY, ctMesh, ['ct [m]', 'Vertical Position [m]'])
    uti_plot.uti_plot1d(p.partTraj.arXp, ctMesh, ['ct [m]', 'Horizontal angle [rad]'])
    uti_plot.uti_plot_show()
    '''
    for i in range(p.partTraj.np):
        p.partTraj.arX[i] *= 1000
        p.partTraj.arY[i] *= 1000
    p.plots.append([
        uti_plot.uti_plot1d,
        p.partTraj.arX, p.ctMesh, ['ct [m]', 'Horizontal Position [mm]'],
    ])
    p.plots.append([
        uti_plot.uti_plot1d,
        p.partTraj.arY, p.ctMesh, ['ct [m]', 'Vertical Position [mm]'],
    ])
    '''
