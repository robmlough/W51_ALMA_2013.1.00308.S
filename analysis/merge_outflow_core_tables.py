import numpy as np
import paths
from astropy.table import Table, Column
from astropy import table
from astropy import units as u
import masscalc

outflow_tbl = Table.read(paths.tpath("outflow_co_photometry.ipac"), format='ascii.ipac')
core_velo_tbl = Table.read(paths.tpath("core_velocities.ipac"), format="ascii.ipac")
core_phot_tbl = Table.read(paths.tpath("continuum_photometry.ipac"), format='ascii.ipac')

newcol = Column([core_phot_tbl['peak_mass'][core_phot_tbl['name'] == name][0]
                 if any(core_phot_tbl['name'] == name) else np.nan
                 for name in outflow_tbl['SourceID']],
                name='CoreMass')
outflow_tbl.add_column(newcol)
outflow_tbl.write(paths.tpath('outflows_with_cores.ipac'), format='ascii.ipac')


core_phot_tbl.rename_column('name','SourceID')
cores_merge = table.join(core_velo_tbl, core_phot_tbl,)

brightest_line_flux = np.array([cores_merge[y].data for y in ('peak0','peak1','peak2','peak3')])
peak_line_flux = np.nanmax(brightest_line_flux, axis=0)
cores_merge.add_column(Column(peak_line_flux, name='PeakLineFlux', unit=cores_merge['peak0'].unit))

peak_line_brightness = (peak_line_flux*u.Jy).to(u.K, u.brightness_temperature(cores_merge['beam_area'], 220*u.GHz))
cores_merge.add_column(Column(peak_line_brightness, name='PeakLineBrightness'))

temperature_corrected_mass = Column([(masscalc.mass_conversion_factor(20)
                                      if np.isnan(row['PeakLineBrightness'])
                                      else masscalc.mass_conversion_factor(row['PeakLineBrightness']))
                                     * row['peak'] for row in cores_merge],
                                    name='T_corrected_mass',
                                    unit=u.M_sun)
cores_merge.add_column(temperature_corrected_mass)

cores_merge.write(paths.tpath('core_continuum_and_line.ipac'), format='ascii.ipac')
