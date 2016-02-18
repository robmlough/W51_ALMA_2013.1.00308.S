import numpy as np
from astropy import units as u
from astropy import log
import paths
import pyregion
from astropy.io import fits
from astropy.table import Table,Column
import masscalc
import radio_beam

regions = pyregion.open(paths.rpath('cores.reg'))

contfile = fits.open(paths.dpath('w51_spw3_continuum_r0_mulstiscale.image.fits'))
data = contfile[0].data
beam = radio_beam.Beam.from_fits_header(paths.dpath('w51_spw3_continuum_r0_mulstiscale.image.fits'))

results = {}
units = {'peak':u.Jy/u.beam,
         'sum':u.Jy/u.beam,
         'npix':u.dimensionless_unscaled,
         'beam_area':u.sr,
         'peak_mass':u.M_sun,
         'peak_col':u.cm**-2}

for reg in regions:
    if 'text' not in reg.attr[1]:
        continue

    shreg = pyregion.ShapeList([reg])
    name = reg.attr[1]['text']
    log.info(name)

    mask = shreg.get_mask(hdu=contfile[0])

    results[name] = {'peak': data[mask].max(),
                     'sum': data[mask].sum(),
                     'npix': mask.sum(),
                     'beam_area': beam.sr,
                    }
    results[name]['peak_mass'] = masscalc.mass_conversion_factor()*results[name]['peak']
    results[name]['peak_col'] = masscalc.col_conversion_factor()*results[name]['peak']

# invert the table to make it parseable by astropy...
# (this shouldn't be necessary....)
results_inv = {'name':{}}
columns = {'name':[]}
for k,v in results.items():
    results_inv['name'][k] = k
    columns['name'].append(k)
    for kk,vv in v.items():
        if kk in results_inv:
            results_inv[kk][k] = vv
            columns[kk].append(vv)
        else:
            results_inv[kk] = {k:vv}
            columns[kk] = [vv]

for c in columns:
    if c in units:
        columns[c] = columns[c] * units[c]

tbl = Table([Column(data=columns[k],
                    name=k)
             for k in ['name','peak','sum','npix','beam_area','peak_mass','peak_col']])

tbl.sort('peak_mass')
tbl.write(paths.tpath("continuum_photometry.ipac"), format='ascii.ipac')
