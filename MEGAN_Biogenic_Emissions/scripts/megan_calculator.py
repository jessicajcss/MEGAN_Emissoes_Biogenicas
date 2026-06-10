"""Core MEGAN utility functions used by notebook outputs."""

from __future__ import annotations

import numpy as np


def megan_emission_rate(efv, lai, gamma_lai, ldf, gamma_t_light, gamma_p, gamma_ti):
    """E = EFv * LAI * gamma_LAI * (LDF*gamma_t_light*gamma_p + (1-LDF)*gamma_ti)."""
    return efv * lai * gamma_lai * (ldf * gamma_t_light * gamma_p + (1.0 - ldf) * gamma_ti)


def derive_reporting_species(emissions_dict):
    """Map internal species to required reporting groups."""
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
