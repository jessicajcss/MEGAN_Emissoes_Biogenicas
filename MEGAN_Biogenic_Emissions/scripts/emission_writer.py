"""CF-1.8 NetCDF writer helpers (EPSG:4326)."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import xarray as xr


def _add_crs(ds: xr.Dataset):
    ds["crs"] = xr.DataArray(
        np.int32(0),
        attrs={
            "grid_mapping_name": "latitude_longitude",
            "semi_major_axis": 6378137.0,
            "inverse_flattening": 298.257223563,
            "epsg_code": "EPSG:4326",
            "spatial_ref": "EPSG:4326",
        },
    )


def write_species_dataset(outpath, species_data, grid_area, xlat, xlon, conventions="CF-1.8"):
    ny, nx = xlat.shape
    ds = xr.Dataset()
    ds.coords["south_north"] = np.arange(ny)
    ds.coords["west_east"] = np.arange(nx)
    ds["latitude"] = (("south_north", "west_east"), xlat.astype(np.float32))
    ds["longitude"] = (("south_north", "west_east"), xlon.astype(np.float32))
    ds["grid_area"] = (("south_north", "west_east"), grid_area.astype(np.float32))
    ds["latitude"].attrs = {"units": "degrees_north", "standard_name": "latitude"}
    ds["longitude"].attrs = {"units": "degrees_east", "standard_name": "longitude"}
    for name, arr in species_data.items():
        ds[name] = (("south_north", "west_east"), arr.astype(np.float32))
        ds[name].attrs.update({"coordinates": "latitude longitude", "grid_mapping": "crs"})
    _add_crs(ds)
    ds.attrs.update({"Conventions": conventions, "history": f"Created {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC"})
    enc = {k: {"zlib": True, "complevel": 4, "dtype": "float32"} for k in ds.data_vars if k != "crs"}
    ds.to_netcdf(outpath, format="NETCDF4", encoding=enc)
    ds.close()
