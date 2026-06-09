# MEGAN Biogenic Emissions — WRF-driven Offline Notebook

A single, exhaustively-documented Jupyter notebook that computes **species-specific
biogenic emissions** with the **MEGAN v2.1** algorithm framework (Guenther et al., 2012),
driven by **WRF d02 meteorology**, **MODIS LAI**, and **MapBiomas growth-form fractions**.
Outputs are CF-compliant NetCDF files (µg m⁻² h⁻¹, **tonnes day⁻¹**, **tonnes year⁻¹**)
ready for **QGIS**.

This reproduces, as closely as possible offline, the MEGAN configuration used in
**BRAIN v2** (WRF-driven, regional d02 domain over southern Brazil).

---

## 1. Quick start

```bash
# 1. Create a Python environment (conda or venv)
conda create -n megan python=3.11 -y
conda activate megan

# 2. Install dependencies
pip install numpy xarray pandas netCDF4 scipy matplotlib jupyter

# 3. Open the notebook in VS Code
code notebook/MEGAN_biogenic_emissions.ipynb

# 4. Edit the "USER CONFIGURATION" cell (Section 1) — set dates and paths
# 5. Run all cells (Run → Run All)
```

VS Code needs the **Python** and **Jupyter** extensions installed.

---

## 2. Folder / file structure

Create exactly this structure on your machine. Place your input files in the
indicated folders before running.

```
MEGAN_Biogenic_Emissions/
├── notebook/
│   └── MEGAN_biogenic_emissions.ipynb     ← the notebook (run this)
├── input/
│   ├── WRF/                               ← put your hourly wrfout_d02_* files here
│   │   ├── wrfout_d02_2020-01-01_00_00_00
│   │   ├── wrfout_d02_2020-01-01_01_00_00
│   │   └── ...
│   ├── LAI/
│   │   └── MEGAN_LAI_CLIM_d02_MEGAN32.nc  ← output of build_megan_lai_from_tifs.py
│   └── LULC/
│       └── CT3.SC_Brazil.csv              ← output of build_sc_brazil_csvs.py
├── output/                                ← generated .nc + .png appear here
├── scripts/                               ← your reference preprocessing scripts
│   ├── build_megan_lai_from_tifs.py
│   ├── build_sc_brazil_csvs.py
│   └── MEGAN_LAI_WRFd02.py                (Google Earth Engine — JavaScript)
├── docs/
└── README.md
```

---

## 3. Required input files

### 3.1 WRF meteorology (`input/WRF/`)
Hourly WRF output files for the d02 domain, **one timestep per file**, named with the
full timestamp:

```
wrfout_d02_YYYY-MM-DD_HH_00_00
```

The notebook reads these WRF variables:

| Variable | Meaning            | Units    |
|----------|--------------------|----------|
| `T2`     | 2-m temperature    | K        |
| `SWDOWN` | shortwave down     | W m⁻²    |
| `U10`,`V10` | 10-m wind       | m s⁻¹    |
| `Q2`     | 2-m mixing ratio   | kg kg⁻¹  |
| `PSFC`   | surface pressure   | Pa       |
| `XLAT`,`XLONG` | grid coords  | degrees  |

> **Source:** the BRAIN WRF dataset on Science Data Bank
> ([10.57760/sciencedb.10130](https://doi.org/10.57760/sciencedb.10130)).
>
> **Multi-timestep files:** if your WRF files contain more than one time per file,
> see Section 6 (Adapting) for the one-line change needed.

You need at least **240 hours (10 days) of WRF data *before* your `START_DATE`** as
a warm-up period, so the running 24-h and 240-h temperature/PPFD averages are valid
from day one. The notebook handles this automatically as long as the earlier files
are present in `input/WRF/`.

### 3.2 LAI climatology (`input/LAI/MEGAN_LAI_CLIM_d02_MEGAN32.nc`)
Monthly LAI climatology on the WRF d02 grid — the **direct output** of your
`build_megan_lai_from_tifs.py`. Variable `LAI`, dims `(month=12, south_north, west_east)`.

### 3.3 Growth-form fractions (`input/LULC/CT3.SC_Brazil.csv`)
MapBiomas-derived plant-functional-type fractions — the **direct output** of your
`build_sc_brazil_csvs.py`. Columns used: `NEEDL, TROPI, BROAD, SHRUB, HERB, CROP`
(values in percent, 0–100). Row order is row-major (C-order) over the WRF grid,
exactly as your script writes it.

---

## 4. What the notebook does

1. **Loads** WRF met, LAI climatology, and growth-form fractions.
2. **Derives** PPFD from `SWDOWN` (×2.25) and maintains rolling 24-h / 240-h means
   of temperature and PPFD.
3. **Computes solar geometry** (elevation, eccentricity) and **partitions** radiation
   into beam/diffuse visible & NIR, then sunlit/shade canopy PPFD by Gaussian layers.
4. **Applies the MEGAN2.1 activity factors** (γ_LAI, γ_T light-dependent,
   γ_P light-dependent, γ_TI light-independent temperature, γ_age) and the
   light-dependence-fraction (LDF) split, combined with PFT-weighted emission factors.
5. **Aggregates** hourly → daily → period totals.
6. **Writes** per-day and per-period NetCDF files (CF-1.8, EPSG:4326), plus a
   summary PNG.

### Outputs (`output/`)
| File | Content | Units |
|------|---------|-------|
| `MEGAN_emissions_YYYY-MM-DD.nc` | daily, per species: `{SPC}_rate`, `{SPC}_tonnes_per_day` | µg m⁻² h⁻¹ ; tonnes day⁻¹ |
| `MEGAN_emissions_annual_*.nc`   | period totals, per species: `{SPC}_tonnes_total`, `{SPC}_rate_mean` | tonnes ; µg m⁻² h⁻¹ |
| `emissions_summary.png`         | quick maps of key species | — |

---

## 5. Loading the results in QGIS

1. *Layer → Add Layer → Add Raster Layer* → select an output `.nc`.
2. Pick a sub-dataset (e.g. `ISOP_tonnes_total`) → *Add*.
3. CRS is **EPSG:4326** (embedded). The 2-D `latitude`/`longitude` variables provide
   correct georeferencing even on the curvilinear WRF grid.
4. *Properties → Symbology → Singleband pseudocolor* and choose a ramp (e.g. YlOrRd).

---

## 6. Adapting the notebook

All knobs live in the **Section 1 "USER CONFIGURATION"** cell:

- `START_DATE`, `END_DATE` — the simulation period (user-defined).
- `WRF_DIR`, `LAI_FILE`, `CT3_FILE`, `OUTPUT_DIR` — input/output paths.
- `WRF_PREFIX` — WRF filename prefix (default `wrfout_d02_`).
- `SPECIES_LIST` — comment out species you don't need.
- `GROWTHFORM_PFT_INDEX` (Section 3) — maps each growth form to a MEGAN PFT; adjust
  if your domain's ecology differs.

**Multi-timestep WRF files:** the reader assumes one timestep per file. If a file holds
several times, loop over `time_idx` in `read_wrf_timestep` and key the simulation on the
`Times` variable instead of the filename (the relevant code is flagged in Section 6 of
the notebook).

---

## 7. Scientific basis, simplifications & provenance

The gamma-factor equations, emission-factor tables, canopy parameters, and the LDF
combination are ported from the peer-reviewed **GEE-MEGAN** code
([Zenodo 10.5281/zenodo.15714886](https://doi.org/10.5281/zenodo.15714886);
[CodeOcean capsule 4836770](https://codeocean.com/capsule/4836770/tree/v1)),
following Guenther et al. (2006, 2012).

**Important — why this is a port, not the original code:** GEE-MEGAN sources its
meteorology from **ERA5 via Google Earth Engine** and runs in the cloud; it does *not*
ingest WRF. BRAIN, by contrast, used the **UCI MEGAN v3.2 FORTRAN** driven by WRF + MCIP.
To match the BRAIN configuration *and* run locally with no GEE/FORTRAN/MCIP, this
notebook re-implements the published MEGAN2.1 algorithms in NumPy/xarray, driven directly
by your WRF d02 meteorology.

Simplifications relative to the full driver (all standard for regional WRF-MEGAN):
1. **Leaf temperature ≈ air temperature** (no iterative leaf energy balance).
2. **γ_SM = 1.0** — soil-moisture stress not modeled (same as GEE-MEGAN default).
3. **ρ = 1.0** — canopy loss/production set to unity (same as GEE-MEGAN default).

### References
- Guenther et al. (2012), *Geosci. Model Dev.* 5, 1471–1492. https://doi.org/10.5194/gmd-5-1471-2012
- Guenther et al. (2006), *Atmos. Chem. Phys.* 6, 3181–3210. https://doi.org/10.5194/acp-6-3181-2006
- Zhang et al. (2025), *Nat. Commun.* https://doi.org/10.1038/s41467-025-63437-8
- BRAIN emissions: https://doi.org/10.57760/sciencedb.14561 · WRF met: https://doi.org/10.57760/sciencedb.10130
- MEGAN data & code: https://bai.ess.uci.edu/megan/data-and-code

---

## 8. Validation

The notebook was tested end-to-end on synthetic WRF/LAI/CT3 inputs that reproduce the
real file structures. Verified behavior:
- Runs cleanly start-to-finish; outputs are CF-1.8, georeferenced, no NaNs.
- **Diurnal physics correct:** light-dependent isoprene peaks at midday and falls to ~0
  at night; light-independent emissions (NO, low-LDF monoterpenes) persist at night and
  scale with temperature.
- Species ranking is physically sensible (isoprene dominant, then methanol/CO).

To validate against BRAIN, set `BRAIN_MEGAN_FILE` in Section 13 to a BRAIN MEGAN output
file and compare.
