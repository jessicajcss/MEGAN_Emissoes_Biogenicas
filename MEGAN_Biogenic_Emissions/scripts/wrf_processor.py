"""WRF input utilities for the MEGAN notebook workflow."""

from __future__ import annotations

import glob
import os
import re
import urllib.request
import zipfile
from datetime import datetime, timedelta

import numpy as np
import xarray as xr


WRF_DT_RE = re.compile(r"(\d{4}-\d{2}-\d{2})[_:](\d{2})[_:](\d{2})[_:](\d{2})")


def parse_wrf_datetime(text: str):
    m = WRF_DT_RE.search(text)
    if not m:
        return None
    return datetime.strptime(f"{m.group(1)} {m.group(2)}:{m.group(3)}:{m.group(4)}", "%Y-%m-%d %H:%M:%S")


def prepare_wrf_inputs(source_mode: str, wrf_dir: str, link_list_file: str, cache_dir: str, start_date: datetime, end_date: datetime, warmup_hours: int = 240) -> str:
    if source_mode == "local":
        return wrf_dir
    if source_mode != "links":
        raise ValueError("source_mode must be 'local' or 'links'")

    os.makedirs(cache_dir, exist_ok=True)
    t0 = start_date - timedelta(hours=warmup_hours)
    t1 = end_date + timedelta(hours=23)

    with open(link_list_file, "r", encoding="utf-8") as f:
        links = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]

    selected = []
    for link in links:
        dt = parse_wrf_datetime(link)
        if dt and t0 <= dt <= t1:
            selected.append((dt, link))

    for dt, link in sorted(selected):
        out_nc = os.path.join(cache_dir, f"wrfout_d02_{dt:%Y-%m-%d_%H_00_00}")
        if os.path.exists(out_nc):
            continue
        tmp = out_nc + ".download"
        urllib.request.urlretrieve(link, tmp)
        if zipfile.is_zipfile(tmp):
            with zipfile.ZipFile(tmp, "r") as zf:
                members = [m for m in zf.namelist() if "wrfout_d02_" in os.path.basename(m)]
                if not members:
                    raise RuntimeError(f"No wrfout_d02_ file in {link}")
                with zf.open(members[0]) as src, open(out_nc, "wb") as dst:
                    dst.write(src.read())
            os.remove(tmp)
        else:
            os.replace(tmp, out_nc)
    return cache_dir


def find_wrf_files(wrf_dir: str, prefix: str, start_dt: datetime, end_dt: datetime):
    files = sorted(glob.glob(os.path.join(wrf_dir, f"{prefix}*")))
    out = []
    for fp in files:
        dt = parse_wrf_datetime(os.path.basename(fp))
        if dt and start_dt <= dt <= end_dt:
            out.append((dt, fp))
    return sorted(out, key=lambda t: t[0])


def read_wrf_timestep(filepath: str):
    ds = xr.open_dataset(filepath)
    def first2d(name):
        v = ds[name]
        if "Time" in v.dims:
            v = v.isel(Time=0)
        return np.asarray(v.values, dtype=np.float64)
    out = {
        "T2": first2d("T2"),
        "SWDOWN": first2d("SWDOWN"),
        "U10": first2d("U10"),
        "V10": first2d("V10"),
        "Q2": first2d("Q2"),
        "PSFC": first2d("PSFC"),
        "XLAT": first2d("XLAT"),
        "XLONG": first2d("XLONG"),
    }
    ds.close()
    return out
