# Methodology — MEGAN 3.2 Project Configuration (Santa Catarina, Brazil)

## Scientific basis
This workflow follows the MEGAN framework described by Guenther et al. (2006, 2012), in a WRF-driven regional setup aligned with BRAIN-style input data use and Hoinaski et al. (2024) configuration goals.

## Core equation
For each species and grid cell:

\[
E = EF_v \times LAI \times \gamma_{LAI} \times \left(LDF\times\gamma_{T,light}\times\gamma_P + (1-LDF)\times\gamma_{TI}\right)
\]

Where:
- \(E\): emission rate (\(\mu g\ m^{-2}\ h^{-1}\))
- \(EF_v\): vegetation-weighted emission factor
- \(LAI\): leaf area index
- \(\gamma_{LAI}\): LAI activity factor
- \(\gamma_{T,light}\): light-dependent temperature factor
- \(\gamma_P\): PPFD response factor
- \(\gamma_{TI}\): light-independent temperature factor
- \(LDF\): light dependence fraction per species

Regional standard assumptions used:
- \(\gamma_{SM}=1\) (no soil-moisture stress)
- \(\rho=1\) (canopy loss/production factor)

## Meteorology and radiative processing
1. Read hourly WRF fields (`T2`, `SWDOWN`, `U10`, `V10`, `Q2`, `PSFC`, `XLAT`, `XLONG`).
2. Convert shortwave to PPFD: `PPFD = SWDOWN × 2.25` (\(\mu mol\ m^{-2}\ s^{-1}\)).
3. Compute rolling means (24 h and 240 h) for temperature and PPFD.
4. Estimate solar geometry (solar elevation, Earth–Sun correction).
5. Partition radiation and distribute through canopy layers.
6. Compute sunlit/shaded responses and gamma factors.

## Species outputs
The notebook solves internal MEGAN species and reports requested groups:
- ISOP
- MTRY (aggregated monoterpenes)
- SESQ (aggregated sesquiterpenes)
- CH3OH (from methanol class)
- HCHO (placeholder direct-emission field in simplified setup)
- CH3COOH (placeholder direct-emission field in simplified setup)
- OTHER_VOC

## Units and conversions
- Instantaneous / mean rates: \(\mu g\ m^{-2}\ h^{-1}\)
- Daily grid-cell totals: `tonnes day⁻¹ = (Σ hourly µg m⁻²) × area(m²) / 1e12`
- Period totals: `tonnes = (Σ all-hour µg m⁻²) × area(m²) / 1e12`

## Output georeferencing and CF compliance
- Conventions: `CF-1.8`
- Curvilinear coordinates: `latitude(south_north, west_east)`, `longitude(south_north, west_east)`
- CRS metadata variable: `crs` with `grid_mapping_name=latitude_longitude` and EPSG:4326/WGS84 descriptors

## Low-memory processing strategy
Recommended for 4–8 GB RAM: process WRF one timestep file at a time, update rolling buffers, aggregate immediately, and write daily outputs incrementally. This avoids loading full-year meteorology into memory.

## Uncertainties and limitations
- HCHO and CH3COOH are included as direct-emission placeholders in this simplified MEGAN setup.
- Soil moisture stress and explicit canopy chemistry are not activated.
- Accuracy depends on LAI quality, growth-form fractions, and emission-factor representativeness.

## References
- Guenther, A. et al. (2006). ACP, 6, 3181–3210. https://doi.org/10.5194/acp-6-3181-2006
- Guenther, A. et al. (2012). GMD, 5, 1471–1492. https://doi.org/10.5194/gmd-5-1471-2012
- Hoinaski, L. et al. (2024). ESSD, 16, 2385–2414. https://doi.org/10.5194/essd-16-2385-2024
