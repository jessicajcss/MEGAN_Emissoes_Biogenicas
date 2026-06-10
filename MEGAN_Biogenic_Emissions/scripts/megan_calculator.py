"""Core MEGAN utility functions used by notebook outputs."""

from __future__ import annotations

import numpy as np


def megan_emission_rate(efv, lai, gamma_lai, ldf, gamma_t_light, gamma_p, gamma_ti):
    """Compute the MEGAN emission rate using the standard gamma-factor equation.

    Parameters
    ----------
    efv : array-like
        Vegetation-weighted emission factor (typically in ug m-2 h-1 at standard state).
    lai : array-like
        Leaf area index (m2 m-2).
    gamma_lai : array-like
        LAI activity factor (dimensionless).
    ldf : float or array-like
        Light dependence fraction for the species (dimensionless, 0..1).
    gamma_t_light : array-like
        Light-dependent temperature activity factor (dimensionless).
    gamma_p : array-like
        PPFD/light activity factor (dimensionless).
    gamma_ti : array-like
        Light-independent temperature activity factor (dimensionless).

    Returns
    -------
    numpy.ndarray
        Emission rate array following:
        ``E = EFv * LAI * gamma_LAI * (LDF*gamma_t_light*gamma_p + (1-LDF)*gamma_ti)``.
    """
    return efv * lai * gamma_lai * (ldf * gamma_t_light * gamma_p + (1.0 - ldf) * gamma_ti)


def derive_reporting_species(emissions_dict):
    """Aggregate internal MEGAN species into required reporting groups.

    Aggregations include:
    - ``MTRY``: summed monoterpenes (MYRC, SABI, LIMO, A_3CAR, OCIM, BPIN, APIN, OMTP)
    - ``SESQ``: summed sesquiterpenes (FARN, BCAR, OSQT)
    - ``CH3OH``: methanol proxy (MEOH)
    - ``OTHER_VOC``: residual grouped VOC classes

    ``HCHO`` and ``CH3COOH`` are returned as zeros in this simplified setup,
    because explicit direct primary emissions for these compounds are not
    represented in the internal species dictionary.
    """
    template = next(iter(emissions_dict.values()))
    zeros = np.zeros_like(template)

    def _sum(keys):
        total = np.zeros_like(template)
        for key in keys:
            total += emissions_dict.get(key, zeros)
        return total

    return {
        "ISOP": emissions_dict.get("ISOP", zeros),
        "MTRY": _sum(["MYRC", "SABI", "LIMO", "A_3CAR", "OCIM", "BPIN", "APIN", "OMTP"]),
        "SESQ": _sum(["FARN", "BCAR", "OSQT"]),
        "CH3OH": emissions_dict.get("MEOH", zeros),
        "HCHO": zeros.copy(),
        "CH3COOH": zeros.copy(),
        "OTHER_VOC": _sum(["MBO", "ACTO", "CO", "NO", "BIDER", "STRESS", "OTHER"]),
    }
