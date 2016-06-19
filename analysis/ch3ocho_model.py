"""

"""
import numpy as np
import pyspeckit
from pyspeckit.spectrum.models import model
from pyspeckit.spectrum.models import lte_molecule
from spectral_cube import SpectralCube
from astropy import units as u
from astropy import constants
from astropy.io import fits
from astroquery.splatalogue import Splatalogue, utils

from vamdclib import nodes
from vamdclib import request
from vamdclib import specmodel

tbl = Splatalogue.query_lines(210*u.GHz, 235*u.GHz, chemical_name=' CH3OCHO ',
                              energy_max=2500, energy_type='eu_k')
freqs = np.unique(tbl['Freq-GHz'])
#vdiff = (np.array((freqs-freqs[0])/freqs[0])*constants.c).to(u.km/u.s)

# SLAIM is missing an important (10,5) transition
slaim = Splatalogue.query_lines(210*u.GHz, 235*u.GHz, chemical_name=' CH3OCHO ',
                                energy_max=2500, energy_type='eu_k',
                                line_lists=['SLAIM'],
                                show_upper_degeneracy=True)
freqs = np.array(slaim['Freq-GHz'])*u.GHz
aij = slaim['Log<sub>10</sub> (A<sub>ij</sub>)']
deg = slaim['Upper State Degeneracy']
EU = (np.array(slaim['E_U (K)'])*u.K*constants.k_B).to(u.erg).value

# CDMS doesn't have CH3OCHO!!! It has CH2(OH)CHO though
# cdmsplat_ = Splatalogue.query_lines(210*u.GHz, 235*u.GHz, chemical_name='Glycolaldehyde',
#                                     energy_max=2500, energy_type='eu_k',
#                                     line_lists=['CDMS'],
#                                     show_upper_degeneracy=True)
# cdmsplat = utils.minimize_table(cdmsplat_)
# freqs = np.array(cdmsplat['Freq'])*u.GHz
# aij = cdmsplat['log10_Aij']
# deg = cdmsplat_['Upper State Degeneracy']
# EU = (np.array(cdmsplat['EU_K'])*u.K*constants.k_B).to(u.erg).value
#ref_freq = 220.74726*u.GHz
#vdiff = (np.array(-(freqs-ref_freq)/ref_freq)*constants.c).to(u.km/u.s).value



# nl = nodes.Nodelist()
# nl.findnode('cdms')
# cdms = nl.findnode('cdms')
# 
# request = request.Request(node=cdms)
# 
# 
# # Retrieve all species from CDMS
# result = request.getspecies()
# molecules = result.data['Molecules']
# 
# ch3ocho = [x for x in molecules.values()
#          if #hasattr(x,'MolecularWeight') and
#          #(x.ChemicalName == 'Isocyanic acid') and
#          #(x.StoichiometricFormula)==('CHNO') and
#          (x.OrdinaryStructuralFormula=='CH3OCHO')
#          #x.MolecularWeight=='32'
#         ][0]
# 
# ch3ocho_inchikey = ch3ocho.InChIKey
# 
# # query everything for ch3ocho
# query_string = "SELECT ALL WHERE VAMDCSpeciesID='%s'" % ch3ocho.VAMDCSpeciesID
# request.setquery(query_string)
# result = request.dorequest()



def ch3ocho_model(xarr, vcen, width, tex, column, background=None, tbg=2.73):

    if hasattr(tex,'unit'):
        tex = tex.value
    if hasattr(tbg,'unit'):
        tbg = tbg.value
    if hasattr(column, 'unit'):
        column = column.value
    if column < 25:
        column = 10**column
    if hasattr(vcen, 'unit'):
        vcen = vcen.value
    if hasattr(width, 'unit'):
        width = width.value

    ckms = constants.c.to(u.km/u.s).value

    # assume equal-width channels
    #kwargs = dict(rest=ref_freq)
    #equiv = u.doppler_radio(**kwargs)
    channelwidth = np.abs(xarr[1].to(u.Hz, ) - xarr[0].to(u.Hz, )).value
    #velo = xarr.to(u.km/u.s, equiv).value
    freq = xarr.to(u.Hz).value # same unit as nu below
    model = np.zeros_like(xarr).value

    freqs_ = freqs.to(u.Hz).value

    #Q = specmodel.calculate_partitionfunction(result.data['States'],
    #                                          temperature=tex)[ch3ocho.Id]

    Q = (deg * np.exp(-EU*u.erg / (constants.k_B * tex*u.K))).sum()

    for A, g, nu, eu in zip(aij, deg, freqs_, EU):
        tau_per_dnu = lte_molecule.line_tau_cgs(tex,
                                                column,
                                                Q,
                                                g,
                                                nu,
                                                eu,
                                                10**A)
        width_dnu = width / ckms * nu
        s = np.exp(-(freq-(1-vcen/ckms)*nu)**2/(2*width_dnu**2))*tau_per_dnu/channelwidth
        jnu = (lte_molecule.Jnu_cgs(nu, tex)-lte_molecule.Jnu_cgs(nu, tbg))

        model = model + jnu*(1-np.exp(-s))

    if background is not None:
        return background-model
    return model

def ch3ocho_fitter():
    """
    Generator for ch3ocho fitter class
    """

    myclass = model.SpectralModel(ch3ocho_model, 4,
            parnames=['shift','width','tex','column'],
            parlimited=[(False,False),(True,False),(True,False),(True,False)],
            parlimits=[(0,0), (0,0), (0,0),(0,0)],
            shortvarnames=(r'\Delta x',r'\sigma','T_{ex}','N'),
            centroid_par='shift',
            )
    myclass.__name__ = "ch3ocho"
    
    return myclass

pyspeckit.spectrum.fitters.default_Registry.add_fitter('ch3ocho',ch3ocho_fitter(),4)

def ch3ocho_absorption_fitter():
    """
    Generator for ch3ocho absorption fitter class
    """

    myclass = model.SpectralModel(ch3ocho_model, 5,
            parnames=['shift','width','tex','column','background'],
            parlimited=[(False,False),(True,False),(True,False),(True,False),(True,False)],
            parlimits=[(0,0), (0,0), (0,0),(0,0),(0,0)],
            shortvarnames=(r'\Delta x',r'\sigma','T_{ex}','N','T_{BG}'),
            centroid_par='shift',
            )
    myclass.__name__ = "ch3ocho_absorption"
    
    return myclass

pyspeckit.spectrum.fitters.default_Registry.add_fitter('ch3ocho_absorption',ch3ocho_absorption_fitter(),5)


if __name__ == "__main__" and False:

    import glob
    import pyspeckit
    import paths
    import radio_beam

    target = 'e2nw'

    spectra = pyspeckit.Spectra(glob.glob(paths.spath("*{0}*fits".format(target))))
    beam = radio_beam.Beam.from_fits_header(spectra.header)
    # "baseline"
    spectra.data -= 0.15
    spectra.data *= beam.jtok(spectra.xarr)

    spectra.plotter()

    spectra.specfit.Registry.add_fitter('ch3ocho', ch3ocho_fitter(), 4)
    spectra.specfit(fittype='ch3ocho', guesses=[55, 4, 200, 5e15],
                    limitedmin=[True]*4, limitedmax=[True]*4, limits=[(50,70),
                                                                      (1,8),
                                                                      (20,
                                                                       1000),
                                                                      (1e13,
                                                                       1e18)])