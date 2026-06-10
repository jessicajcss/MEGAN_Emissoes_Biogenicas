# MEGAN_Biogenic_Emissions

Production-style notebook workflow for biogenic emissions over Santa Catarina (Brazil), using WRF meteorology, MODIS LAI climatology, MapBiomas growth forms, and MEGAN gamma-factor equations.

## Deliverables in this folder
- `notebook.ipynb` (main notebook)
- `notebook/MEGAN_biogenic_emissions.ipynb` (same content, alternate path)
- `requirements.txt`
- `environment.yml`
- `docs/methodology.md`
- `scripts/` helper modules

## Run in VS Code
```bash
cd MEGAN_Biogenic_Emissions
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebook.ipynb
```

## Run in Colab
1. Upload/extract this folder to Colab workspace or Google Drive.
2. Open `notebook.ipynb`.
3. Run all cells (the notebook has a Colab bootstrap cell).

## Input directories expected
```
input/
├── WRF/
│   ├── wrfout_d02_YYYY-MM-DD_HH_00_00
│   └── wrf_2019_list.txt   # optional
├── LAI/
│   └── MEGAN_LAI_CLIM_d02_MEGAN32.nc
├── LULC/
│   └── CT3.SC_Brazil.csv
└── EF/
    ├── EFv240120.csv
    ├── SpeciationTree230921.csv
    ├── SpeciationShrub230822.csv
    ├── SpeciationHerb230822.csv
    └── SpeciationCrop230822.csv
```

## Output files
- `output/MEGAN_emissions_YYYY-MM-DD.nc`
- `output/MEGAN_emissions_annual_YYYYMMDD_YYYYMMDD.nc`
- `output/emissions_summary.png`

## Recommended strategy for low-memory machines (4–8 GB RAM)
Use `WRF_SOURCE_MODE='local'` and process hourly WRF files one at a time (default behavior). This is more stable than bulk download/unzip workflows.

## EPSG/CRS notes
Outputs include:
- `Conventions = CF-1.8`
- 2-D `latitude` and `longitude`
- `crs` variable with WGS84 / EPSG:4326 metadata

## Scientific references
- Guenther et al. (2006): https://doi.org/10.5194/acp-6-3181-2006
- Guenther et al. (2012): https://doi.org/10.5194/gmd-5-1471-2012
- Hoinaski et al. (2024): https://doi.org/10.5194/essd-16-2385-2024
