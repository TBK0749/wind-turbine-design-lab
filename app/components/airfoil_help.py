"""Student-facing explanations for airfoil choices."""

import pandas as pd
import streamlit as st

from windlab.section_airfoils import SECTION_AIRFOILS


def _display_value(value: float | None, suffix: str = "%") -> str:
    """Return a compact display value for optional airfoil metadata."""

    return "—" if value is None else f"{value:g}{suffix}"


def render_airfoil_help() -> None:
    """Explain airfoils and NACA codes in classroom language."""

    with st.expander("Airfoil Help", expanded=False):
        st.markdown(
            """
**Airfoil is the blade cross-section.** If you cut the blade and look at the
side shape, that shape is the airfoil. Its job is to turn wind into lift, and
that lift helps spin the turbine.

**Why many models?** Root sections need strength and startup torque, middle
sections produce most of the lift, and tip sections move fastest so they need
lower drag.

**How to read NACA 4418:** `4418 = 4% camber, 40% camber position, 18% thickness`.
The last two digits are especially useful for students: thicker airfoils are
stronger near the root, while thinner airfoils usually reduce drag near the tip.

The table below includes **Best zone**, camber, camber position, thickness, and
a short student meaning for each airfoil.
"""
        )

        rows = []
        for airfoil in SECTION_AIRFOILS.values():
            rows.append(
                {
                    "Airfoil": airfoil.name,
                    "Family": airfoil.family,
                    "Best zone": airfoil.best_zone,
                    "Camber": _display_value(airfoil.camber_percent),
                    "Camber position": _display_value(airfoil.camber_position_percent),
                    "Thickness": _display_value(airfoil.thickness_percent),
                    "Student meaning": airfoil.plain_language_summary,
                }
            )

        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
