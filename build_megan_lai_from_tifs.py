!pip install numpy xarray rioxarray rasterio scipy netCDF4


import os
import re
import glob
import numpy as np
import xarray as xr
import rioxarray as rxr
from scipy.interpolate import griddata

# ==========================================================
# PATHS
# ==========================================================
lai_dir = r"C:\Users\unesc\Desktop\2026\FAPESC\MEGANHome\GEE\GEE_MEGAN_LAI_SC_Brazil"
wrf_grid_file = r"C:\Users\unesc\Desktop\2026\FAPESC\MEGANHome\input\WRF\wrfout_d02_2019-12-31_18_00_00"
output_nc = r"C:\Users\unesc\Desktop\2026\FAPESC\MEGANHome\GEE\MEGAN_LAI_CLIM_d02_MEGAN32.nc"
qa_tif_dir = r"C:\Users\unesc\Desktop\2026\FAPESC\MEGANHome\GEE\QA_MONTHLY_TIFS_MEGAN32"

os.makedirs(qa_tif_dir, exist_ok=True)

# ==========================================================
# FIND TIFFS
# ==========================================================
pattern = os.path.join(lai_dir, "SCB_LAI_CLIM_*_MOD15A2H.tif")
files = glob.glob(pattern)

def get_month(path):
    m = re.search(r"SCB_LAI_CLIM_(\d{2})_MOD15A2H\.tif$", os.path.basename(path))
    return int(m.group(1)) if m else None

files = [(get_month(f), f) for f in files if get_month(f) is not None]
files = sorted(files, key=lambda x: x[0])

if len(files) != 12:
    raise ValueError(f"Expected 12 files, found {len(files)}")

months = [m for m, _ in files]
if months != list(range(1, 13)):
    raise ValueError(f"Expected months 1..12, got {months}")

# ==========================================================
# LOAD WRF GRID
# ==========================================================
wrf = xr.open_dataset(wrf_grid_file)

xlat = wrf["XLAT"] if "XLAT" in wrf else wrf["XLAT_M"]
xlon = wrf["XLONG"] if "XLONG" in wrf else wrf["XLONG_M"]

if "Time" in xlat.dims:
    xlat = xlat.isel(Time=0)
if "Time" in xlon.dims:
    xlon = xlon.isel(Time=0)

target_lat = xlat.values
target_lon = xlon.values
ny, nx = target_lat.shape

# ==========================================================
# REGRID HELPERS
# ==========================================================
def regrid_to_wrf(tif_path):
    da = rxr.open_rasterio(tif_path, masked=True).squeeze()
    if da.rio.crs is None:
        da = da.rio.write_crs("EPSG:4326")

    x = da["x"].values
    y = da["y"].values
    xx, yy = np.meshgrid(x, y)
    vals = da.values

    valid = np.isfinite(vals)
    pts = np.column_stack([xx[valid], yy[valid]])
    v = vals[valid]
    tpts = np.column_stack([target_lon.ravel(), target_lat.ravel()])

    out = griddata(pts, v, tpts, method="linear")
    miss = np.isnan(out)
    if np.any(miss):
        out[miss] = griddata(pts, v, tpts[miss], method="nearest")

    out = out.reshape(target_lon.shape)
    out = np.where(out < 0, 0, out)
    out = np.where(out > 10, 10, out)
    return out.astype(np.float32)

# ==========================================================
# BUILD STACK
# ==========================================================
lai_stack = np.zeros((12, ny, nx), dtype=np.float32)

for i, (month, tif_path) in enumerate(files):
    print(f"Processing month {month:02d}")
    lai_stack[i] = regrid_to_wrf(tif_path)

# ==========================================================
# WRITE NETCDF
# ==========================================================
ds = xr.Dataset(
    data_vars={
        "LAI": (("month", "south_north", "west_east"), lai_stack)
    },
    coords={
        "month": np.arange(1, 13, dtype=np.int32),
        "south_north": np.arange(ny, dtype=np.int32),
        "west_east": np.arange(nx, dtype=np.int32),
        "XLAT": (("south_north", "west_east"), target_lat.astype(np.float32)),
        "XLONG": (("south_north", "west_east"), target_lon.astype(np.float32)),
    },
    attrs={
        "title": "Monthly LAI climatology on WRF d02 grid",
        "source": "MODIS/061/MOD15A2H exported from Google Earth Engine",
        "target_model": "MEGAN 3.2",
    }
)

ds["LAI"].attrs.update({
    "long_name": "Leaf Area Index",
    "units": "m2 m-2"
})

ds["XLAT"].attrs["units"] = "degrees_north"
ds["XLONG"].attrs["units"] = "degrees_east"

encoding = {
    "LAI": {"zlib": True, "complevel": 4, "_FillValue": -9999.0, "dtype": "float32"},
    "XLAT": {"zlib": True, "complevel": 4, "dtype": "float32"},
    "XLONG": {"zlib": True, "complevel": 4, "dtype": "float32"},
}

ds.to_netcdf(output_nc, format="NETCDF4", encoding=encoding)
print(f"Wrote: {output_nc}")

# ==========================================================
# OPTIONAL QA TIFS
# ==========================================================
for i in range(12):
    month = i + 1
    qa = xr.DataArray(
        lai_stack[i],
        dims=("y", "x"),
        coords={"y": np.arange(ny), "x": np.arange(nx)},
        name="LAI"
    )
    qa.rio.write_crs("EPSG:4326", inplace=True)
    qa_path = os.path.join(qa_tif_dir, f"LAI_month_{month:02d}_d02_QA.tif")
    qa.rio.to_raster(qa_path)

print("QA GeoTIFFs written.")