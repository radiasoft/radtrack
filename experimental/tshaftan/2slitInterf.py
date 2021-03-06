import srwlib
import srwl_bl

srwblParam = [

    ['name', 's', 'Two-Slit Interferometer Example', 'simulation name'],

#---Data Folder
    ['fdir', 's', '', 'folder (directory) name for reading-in input and saving output data files'],

#---Electron Beam
    ['ebm_nm', 's', 'ESRF Low Beta', 'standard electron beam name'],
    ['ebm_nms', 's', '', 'standard electron beam name suffix: e.g. can be Day1, Final'],
    ['ebm_i', 'f', 0.2, 'electron beam current [A]'],
    ['ebm_de', 'f', 0.0, 'electron beam average energy deviation [GeV]'],
    ['ebm_x', 'f', 0.0, 'electron beam initial average horizontal position [m]'],
    ['ebm_y', 'f', 0.0, 'electron beam initial average vertical position [m]'],
    ['ebm_z', 'f', 0., 'electron beam initial average longitudinal position [m]'],
    ['ebm_dr', 'f', -1.22925, 'electron beam longitudinal drift [m] to be performed before a required calculation'],

#---Undulator
    ['und_bx', 'f', 0.0, 'undulator horizontal peak magnetic field [T]'],
    ['und_by', 'f', 0.7, 'undulator vertical peak magnetic field [T]'],
    ['und_phx', 'f', 0.0, 'initial phase of the horizontal magnetic field [rad]'],
    ['und_phy', 'f', 0.0, 'initial phase of the vertical magnetic field [rad]'],
    ['und_b2e', '', '', 'estimate undulator fundamental photon energy (in [eV]) for the amplitude of sinusoidal magnetic field defined by und_b or und_bx, und_by', 'store_true'],
    ['und_e2b', '', '', 'estimate undulator field amplitude (in [T]) for the photon energy defined by w_e', 'store_true'],
    ['und_per', 'f', 0.033, 'undulator period [m]'],
    ['und_len', 'f', 2.3265, 'undulator length [m]'],
    ['und_zc', 'f', 0., 'undulator center longitudinal position [m]'],
    ['und_sx', 'i', 1, 'undulator horizontal magnetic field symmetry vs longitudinal position'],
    ['und_sy', 'i', -1, 'undulator vertical magnetic field symmetry vs longitudinal position'],

#---Calculation Types
    #Single-Electron Spectrum vs Photon Energy
    ['ss', '', '', 'calculate single-e spectrum vs photon energy', 'store_true'],
    ['ss_ei', 'f', 100.0, 'initial photon energy [eV] for single-e spectrum vs photon energy calculation'],
    ['ss_ef', 'f', 8000.0, 'final photon energy [eV] for single-e spectrum vs photon energy calculation'],
    ['ss_ne', 'i', 10000, 'number of points vs photon energy for single-e spectrum vs photon energy calculation'],
    ['ss_x', 'f', 0.0, 'horizontal position [m] for single-e spectrum vs photon energy calculation'],
    ['ss_y', 'f', 0.0, 'vertical position [m] for single-e spectrum vs photon energy calculation'],
    ['ss_meth', 'i', 1, 'method to use for single-e spectrum vs photon energy calculation: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"'],
    ['ss_prec', 'f', 0.01, 'relative precision for single-e spectrum vs photon energy calculation (nominal value is 0.01)'],
    ['ss_pol', 'i', 6, 'polarization component to extract after spectrum vs photon energy calculation: 0- Linear Horizontal, 1- Linear Vertical, 2- Linear 45 degrees, 3- Linear 135 degrees, 4- Circular Right, 5- Circular Left, 6- Total'],
    ['ss_mag', 'i', 1, 'magnetic field to be used for single-e spectrum vs photon energy calculation: 1- approximate, 2- accurate'],
    ['ss_fn', 's', 'res_spec_se.dat', 'file name for saving calculated single-e spectrum vs photon energy'],
    ['ss_pl', 's', '', 'plot the resulting single-e spectrum in a graph: ""- dont plot, "e"- show plot vs photon energy'],

    #Multi-Electron Spectrum vs Photon Energy (taking into account e-beam emittance, energy spread and collection aperture size)
    ['sm', '', '', 'calculate multi-e spectrum vs photon energy', 'store_true'],
    ['sm_ei', 'f', 100.0, 'initial photon energy [eV] for multi-e spectrum vs photon energy calculation'],
    ['sm_ef', 'f', 40000.0, 'final photon energy [eV] for multi-e spectrum vs photon energy calculation'],
    ['sm_ne', 'i', 10000, 'number of points vs photon energy for multi-e spectrum vs photon energy calculation'],
    ['sm_x', 'f', 0.0, 'horizontal center position [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_rx', 'f', 0.001, 'range of horizontal position / horizontal aperture size [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_nx', 'i', 1, 'number of points vs horizontal position for multi-e spectrum vs photon energy calculation'],
    ['sm_y', 'f', 0.0, 'vertical center position [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_ry', 'f', 0.001, 'range of vertical position / vertical aperture size [m] for multi-e spectrum vs photon energy calculation'],
    ['sm_ny', 'i', 1, 'number of points vs vertical position for multi-e spectrum vs photon energy calculation'],
    ['sm_mag', 'i', 1, 'magnetic field to be used for calculation of multi-e spectrum spectrum or intensity distribution: 1- approximate, 2- accurate'],
    ['sm_hi', 'i', 1, 'initial UR spectral harmonic to be taken into accountfor multi-e spectrum vs photon energy calculation'],
    ['sm_hf', 'i', 15, 'final UR spectral harmonic to be taken into accountfor multi-e spectrum vs photon energy calculation'],
    ['sm_prl', 'f', 1.0, 'longitudinal integration precision parameter for multi-e spectrum vs photon energy calculation'],
    ['sm_pra', 'f', 1.0, 'azimuthal integration precision parameter for multi-e spectrum vs photon energy calculation'],
    ['sm_type', 'i', 1, 'calculate flux (=1) or flux per unit surface (=2)'],
    ['sm_pol', 'i', 6, 'polarization component to extract after calculation of multi-e flux or intensity: 0- Linear Horizontal, 1- Linear Vertical, 2- Linear 45 degrees, 3- Linear 135 degrees, 4- Circular Right, 5- Circular Left, 6- Total'],
    ['sm_fn', 's', 'res_spec_me.dat', 'file name for saving calculated milti-e spectrum vs photon energy'],
    ['sm_pl', 's', '', 'plot the resulting spectrum-e spectrum in a graph: ""- dont plot, "e"- show plot vs photon energy'],
    #to add options for the multi-e calculation from "accurate" magnetic field

    #Power Density Distribution vs horizontal and vertical position
    ['pw', '', '', 'calculate SR power density distribution', 'store_true'],
    ['pw_x', 'f', 0.0, 'central horizontal position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_rx', 'f', 0.015, 'range of horizontal position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_nx', 'i', 100, 'number of points vs horizontal position for calculation of power density distribution'],
    ['pw_y', 'f', 0.0, 'central vertical position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_ry', 'f', 0.015, 'range of vertical position [m] for calculation of power density distribution vs horizontal and vertical position'],
    ['pw_ny', 'i', 100, 'number of points vs vertical position for calculation of power density distribution'],
    ['pw_pr', 'f', 1.0, 'precision factor for calculation of power density distribution'],
    ['pw_meth', 'i', 1, 'power density computation method (1- "near field", 2- "far field")'],
    ['pw_zst', 'f', 0., 'initial longitudinal position along electron trajectory of power density distribution (effective if pow_sst < pow_sfi)'],
    ['pw_zfi', 'f', 0., 'final longitudinal position along electron trajectory of power density distribution (effective if pow_sst < pow_sfi)'],
    ['pw_mag', 'i', 1, 'magnetic field to be used for power density calculation: 1- approximate, 2- accurate'],
    ['pw_fn', 's', 'res_pow.dat', 'file name for saving calculated power density distribution'],
    ['pw_pl', 's', '', 'plot the resulting power density distribution in a graph: ""- dont plot, "x"- vs horizontal position, "y"- vs vertical position, "xy"- vs horizontal and vertical position'],

    #Single-Electron Intensity distribution vs horizontal and vertical position
    ['si', '', '', 'calculate single-e intensity distribution (without wavefront propagation through a beamline) vs horizontal and vertical position', 'store_true'],
    #Single-Electron Wavefront Propagation
    ['ws', '', '', 'calculate single-electron (/ fully coherent) wavefront propagation', 'store_true'],
    #Multi-Electron (partially-coherent) Wavefront Propagation
    ['wm', '', '', 'calculate multi-electron (/ partially coherent) wavefront propagation', 'store_true'],

    ['w_e', 'f', 4240.0, 'photon energy [eV] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ef', 'f', -1., 'final photon energy [eV] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ne', 'i', 1, 'number of points vs photon energy for calculation of intensity distribution'],
    ['w_x', 'f', 0.0, 'central horizontal position [m] for calculation of intensity distribution'],
    ['w_rx', 'f', 0.0008, 'range of horizontal position [m] for calculation of intensity distribution'],
    ['w_nx', 'i', 100, 'number of points vs horizontal position for calculation of intensity distribution'],
    ['w_y', 'f', 0.0, 'central vertical position [m] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ry', 'f', 0.001, 'range of vertical position [m] for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_ny', 'i', 100, 'number of points vs vertical position for calculation of intensity distribution'],
    ['w_smpf', 'f', 1.0, 'sampling factor for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_meth', 'i', 1, 'method to use for calculation of intensity distribution vs horizontal and vertical position'],
    ['w_prec', 'f', 0.01, 'relative precision for calculation of intensity distribution vs horizontal and vertical position'],
    ['si_pol', 'i', 6, 'polarization component to extract after calculation of intensity distribution: 0- Linear Horizontal, 1- Linear Vertical, 2- Linear 45 degrees, 3- Linear 135 degrees, 4- Circular Right, 5- Circular Left, 6- Total'],
    ['si_type', 'i', 0, 'type of a characteristic to be extracted after calculation of intensity distribution: 0- Single-Electron Intensity, 1- Multi-Electron Intensity, 2- Single-Electron Flux, 3- Multi-Electron Flux, 4- Single-Electron Radiation Phase, 5- Re(E): Real part of Single-Electron Electric Field, 6- Im(E): Imaginary part of Single-Electron Electric Field, 7- Single-Electron Intensity, integrated over Time or Photon Energy'],
    ['w_mag', 'i', 1, 'magnetic field to be used for calculation of intensity distribution vs horizontal and vertical position: 1- approximate, 2- accurate'],

    ['si_fn', 's', 'res_int_se.dat', 'file name for saving calculated single-e intensity distribution (without wavefront propagation through a beamline) vs horizontal and vertical position'],
    ['ws_fni', 's', 'res_int_pr_se.dat', 'file name for saving propagated single-e intensity distribution vs horizontal and vertical position'],
    ['ws_pl', 's', '', 'plot the resulting intensity distributions in graph(s): ""- dont plot, "x"- vs horizontal position, "y"- vs vertical position, "xy"- vs horizontal and vertical position'],

    ['wm_nm', 'i', 100000, 'number of macro-electrons (coherent wavefronts) for calculation of multi-electron wavefront propagation'],
    ['wm_na', 'i', 5, 'number of macro-electrons (coherent wavefronts) to average on each node for parallel (MPI-based) calculation of multi-electron wavefront propagation'],
    ['wm_ns', 'i', 5, 'saving periodicity (in terms of macro-electrons / coherent wavefronts) for intermediate intensity at multi-electron wavefront propagation calculation'],
    ['wm_ch', 'i', 0, 'type of a characteristic to be extracted after calculation of multi-electron wavefront propagation: #0- intensity (s0); 1- four Stokes components; 2- mutual intensity cut vs x; 3- mutual intensity cut vs y'],
    ['wm_ap', 'i', 0, 'switch specifying representation of the resulting Stokes parameters: coordinate (0) or angular (1)'],
    ['wm_x0', 'f', 0, 'horizontal center position for mutual intensity cut calculation'],
    ['wm_y0', 'f', 0, 'vertical center position for mutual intensity cut calculation'],
    ['wm_ei', 'i', 0, 'integration over photon energy is required (1) or not (0); if the integration is required, the limits are taken from w_e, w_ef'],
    ['wm_rm', 'i', 1, 'method for generation of pseudo-random numbers for e-beam phase-space integration: 1- standard pseudo-random number generator, 2- Halton sequences, 3- LPtau sequences (to be implemented)'],
    ['wm_fni', 's', 'res_int_pr_me.dat', 'file name for saving propagated multi-e intensity distribution vs horizontal and vertical position'],

    #to add options
    ['op_r', 'f', 30.0, 'longitudinal position of the first optical element [m]'],
]

appParam = [
    ['mag_type', 's', 'u', 'source type, (u) undulator, (m) multipole'],
#---Multipole
    ['mp_field', 'f', 0.4, 'field parameter [T] for dipole, [T/m] for quadrupole (negative means defocusing for x), [T/m^2] for sextupole, [T/m^3] for octupole'],
    ['mp_order', 'i', 1, 'multipole order 1 for dipole, 2 for quadrupoole, 3 for sextupole, 4 for octupole'],
    ['mp_distribution', 's', 'n', 'normal (n) or skew (s)'],
    ['mp_len', 'f', 3.0, 'effective length [m]'],
    ['mp_zc', 'f', 0., 'multipole center longitudinal position [m]'],
#---User Defined Electron Beam
    ['ueb', 'i', 0, 'Use user defined beam'],
    ['ueb_e', 'f', 6.03, 'energy [GeV]'],
    ['ueb_sig_e', 'f', 0.001, 'RMS energy spread'],
    ['ueb_emit_x', 'f', 4e-09, 'horizontal emittance [m]'],
    ['ueb_beta_x', 'f', 0.35, 'horizontal beta-function [m]'],
    ['ueb_alpha_x', 'f', 0.0, 'horizontal alpha-function [rad]'],
    ['ueb_eta_x', 'f', 0.031, 'horizontal dispersion function [m]'],
    ['ueb_eta_x_pr', 'f', 0.0, 'horizontal dispersion function derivative [rad]'],
    ['ueb_emit_y', 'f', 5e-12, 'vertical emittance [m]'],
    ['ueb_beta_y', 'f', 2.97, 'vertical beta-function [m]'],
    ['ueb_alpha_y', 'f', 0.0, 'vertical alpha-function [rad]'],
    ['ueb_eta_y', 'f', 0.0, 'vertical dispersion function [m]'],
    ['ueb_eta_y_pr', 'f', 0.0, 'vertical dispersion function derivative [rad]'],
]

def setup_magnetic_field(v):
    appV = srwl_bl.srwl_uti_parse_options(appParam)

    if appV.ueb:
        srwl_bl._USER_DEFINED_EBEAM = srwl_bl.SRWLPartBeam()
        srwl_bl._USER_DEFINED_EBEAM.from_Twiss(_e=appV.ueb_e, _sig_e=appV.ueb_sig_e, _emit_x=appV.ueb_emit_x, _beta_x=appV.ueb_beta_x, _alpha_x=appV.ueb_alpha_x, _eta_x=appV.ueb_eta_x, _eta_x_pr=appV.ueb_eta_x_pr, _emit_y=appV.ueb_emit_y, _beta_y=appV.ueb_beta_y, _alpha_y=appV.ueb_alpha_y, _eta_y=appV.ueb_eta_y, _eta_y_pr=appV.ueb_eta_y_pr)

    if appV.mag_type == 'u':
        v.und_b = 1
        return None
    mag = srwlib.SRWLMagFldC();
    mag.arXc.append(0)
    mag.arYc.append(0)
    if appV.mag_type == 'm':
        mag.arMagFld.append(srwlib.SRWLMagFldM(appV.mp_field, appV.mp_order, appV.mp_distribution, appV.mp_len))
        mag.arZc.append(appV.mp_zc)
    return mag

def get_srw_params():
    return srwblParam

def get_app_params():
    return appParam

def get_beamline_optics():
    
    el = []
    pp = []
    el.append(srwlib.SRWLOptL(15.0, 15.0, 0.0, 0.0))
    pp.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])

    el.append(srwlib.SRWLOptA("r", "a", 0.01, 0.00034, 0.0, 0.0))
    pp.append([0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])

    el.append(srwlib.SRWLOptA("r", "o", 0.01, 0.0002, 0.0, 0.0))
    pp.append([0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])


    el.append(srwlib.SRWLOptD(30.0))
    pp.append([1, 1, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])

    pp.append([0, 0, 1.0, 0, 0, 1.0, 1.0, 1.0, 1.0])
    return srwlib.SRWLOptC(el, pp)


# monkey patch SRWLBeamline.set_e_beam() to allow a user defined ebeam when called from calc_all()
original_method = srwl_bl.SRWLBeamline.set_e_beam

def patched_srwl_bl_set_e_beam(self, **kwargs):
    if hasattr(srwl_bl, '_USER_DEFINED_EBEAM'):
        kwargs['_e_beam_name'] = ''
        kwargs['_e_beam'] = srwl_bl._USER_DEFINED_EBEAM
    return original_method(self, **kwargs)

srwl_bl.SRWLBeamline.set_e_beam = patched_srwl_bl_set_e_beam


def run_all_reports():
    v = srwl_bl.srwl_uti_parse_options(get_srw_params())
    mag = setup_magnetic_field(v)
    v.ss = True
    v.ss_pl = 'e'
    if isinstance(mag, srwlib.SRWLMagFldU):
        v.sm = True
        v.sm_pl = 'e'
    v.pw = True
    v.pw_pl = 'xy'
    v.si = True
    v.ws = True
    v.ws_pl = 'xy'
    op = get_beamline_optics()
    srwl_bl.SRWLBeamline(_name=v.name, _mag_approx=mag).calc_all(v, op)

run_all_reports()