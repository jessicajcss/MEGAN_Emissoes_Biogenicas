import os
import numpy as np
import pandas as pd
import xarray as xr

base = 'C:/Users/unesc/Desktop/2026/FAPESC/MEGANHome'
mapdir = os.path.join(base, 'MEGANv3.21', 'Input', 'MAP')
megan = os.path.join(base, 'MEGAN32_d02')

lai = xr.open_dataset(os.path.join(megan, 'veg_LAIv_d02.nc'))['LAI']
gf = xr.open_dataset(os.path.join(megan, 'veg_GrowthFormFractions_d02.nc'))
eco = xr.open_dataset(os.path.join(megan, 'Veg_Ecotypes_d02.nc'))['ecotype']

ny, nx = lai.shape[1], lai.shape[2]
ids = np.arange(1, ny * nx + 1, dtype=int)

out_cols = ['gridID'] + [f'EF{i}' for i in range(1, 20)] + [f'LDF{i}' for i in range(3, 7)]
out = pd.DataFrame(np.zeros((len(ids), 24), dtype=float), columns=out_cols)
out['gridID'] = ids
out.to_csv(os.path.join(mapdir, 'OutputGridEF.SC_Brazil.csv'), index=False)

crop = (gf['crop'].values.ravel() * 100).clip(0, 100)
grass = (gf['grass'].values.ravel() * 100).clip(0, 100)
shrub = (gf['shrub'].values.ravel() * 100).clip(0, 100)
tree = (gf['tree'].values.ravel() * 100).clip(0, 100)

needl = np.zeros_like(tree)
tropi = np.zeros_like(tree)
broad = np.clip(tree, 0, 100)
herb = np.clip(grass, 0, 100)

ct = pd.DataFrame({
    'CID': ids,
    'ICELL': ids,
    'JCELl': np.ones_like(ids),
    'NEEDL': needl,
    'TROPI': tropi,
    'BROAD': broad,
    'SHRUB': shrub,
    'HERB': herb,
    'CROP': crop,
})
ct.to_csv(os.path.join(mapdir, 'CT3.SC_Brazil.csv'), index=False, float_format='%.4f')

lai_mean = lai.mean(dim=['south_north', 'west_east']).values
lai_rows = pd.DataFrame({'month': np.arange(1, 13), 'LAIv': np.round(lai_mean, 6)})
lai_rows.to_csv(os.path.join(mapdir, 'LAI3.SC_Brazil.csv'), index=False)

flat_eco = eco.values.ravel()
landtype = np.where(
    tree >= np.maximum.reduce([crop, grass, shrub]), 1,
    np.where(
        grass >= np.maximum(crop, shrub), 2,
        np.where(crop >= shrub, 3, 4)
    )
)

common = pd.DataFrame({'CID': ids, 'VALUE': flat_eco})
common.to_csv(os.path.join(mapdir, 'grid_W126.SC_Brazil.csv'), index=False, float_format='%.6f')
common.to_csv(os.path.join(mapdir, 'grid_arid.SC_Brazil.csv'), index=False, float_format='%.6f')
common.to_csv(os.path.join(mapdir, 'grid_non_arid.SC_Brazil.csv'), index=False, float_format='%.6f')
common.to_csv(os.path.join(mapdir, 'grid_FERT.SC_Brazil.csv'), index=False, float_format='%.6f')
common.to_csv(os.path.join(mapdir, 'grid_NITROGEN.SC_Brazil.csv'), index=False, float_format='%.6f')
pd.DataFrame({'CID': ids, 'VALUE': landtype}).to_csv(os.path.join(mapdir, 'grid_LANDTYPE.SC_Brazil.csv'), index=False)

print('Wrote SC_Brazil CSVs to', mapdir)
print('CT3 rows:', len(ct), 'LAI3 rows:', len(lai_rows), 'OutputGridEF rows:', len(out))
print(ct.head(3).to_string(index=False))
print(lai_rows.to_string(index=False))