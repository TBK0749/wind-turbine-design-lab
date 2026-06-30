"""Create CAD-friendly export packages for rebuilding blade designs in Onshape."""

from __future__ import annotations

import csv
import json
import re
from io import BytesIO, StringIO
from math import cos, radians, sin
from zipfile import ZIP_DEFLATED, ZipFile

from windlab.airfoil_geometry import airfoil_profile_points
from windlab.models import BladeSection, SimulationInput
from windlab.section_airfoils import get_section_airfoil

ONSHAPE_LOFT_PROFILE_POINT_COUNT = 36


def _fallback_airfoil_name(inputs: SimulationInput) -> str:
    """Map broad airfoil families to a section-level profile for CAD exports."""

    if inputs.airfoil_type == "Flat plate / Foam board":
        return "Flat plate"
    if inputs.airfoil_type == "Symmetric airfoil":
        return "NACA 0012"
    if inputs.airfoil_type == "Cambered plate":
        return "NACA 2412"
    return "NACA 4412"


def _sections_for_export(inputs: SimulationInput) -> tuple[BladeSection, ...]:
    """Return explicit sections, or derive a two-station blade from simple inputs."""

    if inputs.blade_sections:
        return inputs.blade_sections

    airfoil_name = _fallback_airfoil_name(inputs)
    airfoil = get_section_airfoil(airfoil_name)
    return (
        BladeSection(
            position_m=max(inputs.hub_radius_m, 0.001),
            chord_m=inputs.root_chord_m,
            twist_angle_deg=inputs.twist_angle_deg,
            airfoil_name=airfoil.name,
            airfoil_role=airfoil.role,
        ),
        BladeSection(
            position_m=inputs.rotor_radius_m,
            chord_m=inputs.tip_chord_m,
            twist_angle_deg=0.0,
            airfoil_name=airfoil.name,
            airfoil_role=airfoil.role,
        ),
    )


def _section_label(index: int, section_count: int) -> str:
    if index == 0:
        return "1 (Root)"
    if index == section_count - 1:
        return f"{section_count} (Tip)"
    return str(index + 1)


def _csv_text(rows: list[list[str | float | int]]) -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def blade_geometry_csv(inputs: SimulationInput) -> str:
    """Return the blade geometry table in centimetres for CAD reference."""

    sections = _sections_for_export(inputs)
    rows: list[list[str | float | int]] = [
        ["Section", "Position (cm)", "Chord (cm)", "Twist (deg)", "Airfoil", "Role"],
    ]
    for index, section in enumerate(sections):
        rows.append(
            [
                _section_label(index, len(sections)),
                round(section.position_m * 100.0, 3),
                round(section.chord_m * 100.0, 3),
                round(section.twist_angle_deg, 3),
                section.airfoil_name,
                section.airfoil_role,
            ]
        )
    return _csv_text(rows)


def airfoil_sections_csv(inputs: SimulationInput) -> str:
    """Return section-level airfoil metadata for notebook and CAD decisions."""

    sections = _sections_for_export(inputs)
    rows: list[list[str | float | int]] = [
        [
            "Section",
            "Airfoil",
            "Family",
            "Best zone",
            "Thickness (%)",
            "Recommended Re min",
            "Recommended Re max",
            "Plain-language summary",
            "Source note",
        ],
    ]
    for index, section in enumerate(sections):
        airfoil = get_section_airfoil(section.airfoil_name)
        rows.append(
            [
                _section_label(index, len(sections)),
                airfoil.name,
                airfoil.family,
                airfoil.best_zone,
                "" if airfoil.thickness_percent is None else airfoil.thickness_percent,
                airfoil.recommended_reynolds_min,
                airfoil.recommended_reynolds_max,
                airfoil.plain_language_summary,
                airfoil.source_note,
            ]
        )
    return _csv_text(rows)


def _dxf_header() -> str:
    return "0\nSECTION\n2\nENTITIES\n"


def _dxf_footer() -> str:
    return "0\nENDSEC\n0\nEOF\n"


def _dxf_text(label: str, x: float, y: float, height: float = 1.5) -> str:
    return (
        f"0\nTEXT\n8\nlabels\n10\n{x:.4f}\n20\n{y:.4f}\n30\n0.0000\n40\n{height:.4f}\n1\n{label}\n"
    )


def _dxf_polyline(
    points: list[tuple[float, float]],
    *,
    layer: str,
    closed: bool = True,
) -> str:
    body = [
        "0",
        "LWPOLYLINE",
        "8",
        layer,
        "90",
        str(len(points)),
        "70",
        "1" if closed else "0",
    ]
    for x, y in points:
        body.extend(("10", f"{x:.4f}", "20", f"{y:.4f}"))
    return "\n".join(body) + "\n"


def _safe_filename_part(value: str) -> str:
    """Return a compact filename-safe token."""

    return re.sub(r"[^A-Za-z0-9]+", "", value)


def section_profile_filename(index: int, section: BladeSection, section_count: int) -> str:
    """Return an Onshape-friendly DXF filename for one blade section."""

    section_number = index + 1
    position_label = ""
    if index == 0:
        position_label = "_root"
    elif index == section_count - 1:
        position_label = "_tip"
    airfoil = _safe_filename_part(section.airfoil_name)
    return f"section_{section_number:02d}{position_label}_{airfoil}.dxf"


def _rotate_points(
    points: list[tuple[float, float]],
    *,
    angle_deg: float,
) -> list[tuple[float, float]]:
    """Rotate profile points about the sketch origin."""

    angle_rad = radians(angle_deg)
    cos_angle = cos(angle_rad)
    sin_angle = sin(angle_rad)
    return [
        (
            x * cos_angle - y * sin_angle,
            x * sin_angle + y * cos_angle,
        )
        for x, y in points
    ]


def section_profile_dxf(
    section: BladeSection,
    *,
    index: int,
    section_count: int,
) -> str:
    """Return one scaled, centered, pre-twisted airfoil profile DXF."""

    chord_cm = section.chord_m * 100.0
    centered_points = [
        ((x - 0.5) * chord_cm, y * chord_cm)
        for x, y in airfoil_profile_points(
            section.airfoil_name,
            point_count=ONSHAPE_LOFT_PROFILE_POINT_COUNT,
        )
    ]
    points = _rotate_points(centered_points, angle_deg=section.twist_angle_deg)
    return (
        _dxf_header()
        + _dxf_polyline(points, layer=f"section_{index + 1}_profile", closed=True)
        + _dxf_footer()
    )


def individual_section_profile_dxfs(inputs: SimulationInput) -> dict[str, str]:
    """Return one ready-to-insert DXF file per blade section."""

    sections = _sections_for_export(inputs)
    return {
        section_profile_filename(index, section, len(sections)): section_profile_dxf(
            section,
            index=index,
            section_count=len(sections),
        )
        for index, section in enumerate(sections)
    }


def blade_planform_dxf(inputs: SimulationInput) -> str:
    """Return a top-view blade outline DXF in centimetres."""

    sections = _sections_for_export(inputs)
    leading_edge = [(section.position_m * 100.0, section.chord_m * 50.0) for section in sections]
    trailing_edge = [
        (section.position_m * 100.0, -section.chord_m * 50.0) for section in reversed(sections)
    ]
    outline = leading_edge + trailing_edge
    return (
        _dxf_header()
        + _dxf_text(
            "blade planform - units: cm - sketch one blade, then circular-pattern 3 blades",
            0.0,
            max(y for _, y in leading_edge) + 3.0,
        )
        + _dxf_polyline(outline, layer="blade_planform", closed=True)
        + _dxf_footer()
    )


def section_profiles_dxf(inputs: SimulationInput) -> str:
    """Return scaled airfoil profiles for each blade station as a DXF."""

    sections = _sections_for_export(inputs)
    parts = [_dxf_header()]
    y_offset = 0.0
    for index, section in enumerate(sections):
        chord_cm = section.chord_m * 100.0
        points = [
            (x * chord_cm, y_offset + y * chord_cm)
            for x, y in airfoil_profile_points(section.airfoil_name, point_count=60)
        ]
        label = (
            f"{_section_label(index, len(sections))}: {section.airfoil_name}, "
            f"chord {chord_cm:.1f} cm, twist {section.twist_angle_deg:.1f} deg"
        )
        parts.append(_dxf_text(label, 0.0, y_offset + chord_cm * 0.35, height=0.8))
        parts.append(_dxf_polyline(points, layer=f"section_{index + 1}", closed=True))
        y_offset -= max(chord_cm * 0.75, 5.0)
    parts.append(_dxf_footer())
    return "".join(parts)


def _section_profiles_readme(inputs: SimulationInput) -> str:
    """Return README text for the individual section profile folder."""

    sections = _sections_for_export(inputs)
    rows = [
        "# Individual section profile DXF files",
        "",
        "Each DXF in this folder contains one airfoil profile only.",
        "Profiles are scaled to the section chord in centimetres, centred around the",
        "sketch origin, pre-rotated by the section twist angle, and simplified to",
        "a consistent loft-safe vertex count for Onshape.",
        "",
        "Recommended Onshape workflow:",
        "",
        "1. Create or select the matching section plane.",
        "2. Start a new sketch on that plane.",
        "3. Insert the matching DXF file from this folder.",
        "4. Confirm the sketch.",
        "5. Repeat from root to tip, then Loft through the section sketches.",
        "",
        "| Section | File | Chord (cm) | Twist (deg) | Airfoil |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for index, section in enumerate(sections):
        rows.append(
            "| "
            f"{_section_label(index, len(sections))} | "
            f"`{section_profile_filename(index, section, len(sections))}` | "
            f"{section.chord_m * 100.0:.1f} | "
            f"{section.twist_angle_deg:.1f} | "
            f"{section.airfoil_name} |"
        )
    rows.extend(
        [
            "",
            "`section_profiles.dxf` in the package root is still included as an overview only.",
        ]
    )
    return "\n".join(rows) + "\n"


def _metadata(inputs: SimulationInput, design_name: str) -> dict[str, object]:
    sections = _sections_for_export(inputs)
    return {
        "design_name": design_name,
        "units": "centimetres for CSV/DXF geometry; metres for simulator metadata",
        "wind_speed_m_s": inputs.wind_speed_m_s,
        "rotor_radius_m": inputs.rotor_radius_m,
        "rotor_diameter_m": inputs.rotor_radius_m * 2.0,
        "hub_radius_m": inputs.hub_radius_m,
        "blade_count": inputs.blade_count,
        "section_count": len(sections),
        "airfoils": [section.airfoil_name for section in sections],
        "section_profile_files": list(individual_section_profile_dxfs(inputs)),
        "note": (
            "Educational CAD export. Verify dimensions, hub mounting, print orientation, "
            "and competition rules before manufacturing."
        ),
    }


def onshape_build_guide(inputs: SimulationInput, design_name: str) -> str:
    """Return a short guide for rebuilding the blade in Onshape."""

    metadata = _metadata(inputs, design_name)
    return f"""# Onshape build guide: {design_name}

This package is a CAD starting point for a classroom wind-turbine blade.

## Files

- `blade_geometry.csv` — station table: position, chord, twist, airfoil, and role.
- `airfoil_sections.csv` — airfoil metadata and Reynolds-number guidance.
- `blade_planform.dxf` — top-view blade outline in centimetres.
- `section_profiles/section_XX_*.dxf` — one ready-to-insert DXF per blade section.
- `section_profiles.dxf` — combined profile overview for reference.
- `design_metadata.json` — simulator metadata for this export.

## Suggested Onshape workflow

1. Create a new Onshape document and set the working unit to centimetres.
2. Import `blade_planform.dxf` as a sketch for the top-view blade shape.
3. On each section plane, insert the matching file from the `section_profiles/` folder.
4. The individual section DXFs are already scaled, centred, and pre-rotated by twist.
5. Loft through the section sketches, then add a hub connector that matches your
   real generator shaft.
6. Use a circular pattern for {metadata["blade_count"]} blades.
7. Check the final rotor diameter is not greater than {metadata["rotor_diameter_m"]:.2f} m.

## Beginner hub

Do not create the hub sketch on a Mate connector. Create the hub sketch on a real
plane near the root, such as `S1 Root`, `Right`, `Front`, or `Top`.

Suggested starting dimensions:

- outside hub diameter: `8 cm` to `12 cm`;
- shaft hole diameter: measured shaft plus clearance;
- hub thickness: `2 cm` to `4 cm`;
- root overlap: `0.5 cm` to `2 cm`.

Sketch two concentric circles, then Extrude the ring. Use Boolean Union if the
hub and blade are separate parts.

## Three-blade pattern

Use Circular Pattern after one blade and the hub connection look correct.

```text
Pattern type: `Part pattern`
Quantity: `3`
Angle: `360 deg`
Axis: hub cylinder or shaft-hole circular edge
```

If the package shows an extra tip plane, remember that blue section planes are
references only. Pattern actual parts, not planes.

## Export STL

1. Right-click the final rotor part in the Parts list.
2. Choose Export.
3. Export format: `STL`.
4. Choose Binary STL unless your slicer requires ASCII.
5. Use millimetres if your slicer expects millimetres.
6. Open the STL in your slicer before printing.

## Important warning

This export is not a finished certified STL. It is a controlled geometry package
to help students rebuild the design in CAD, inspect it, and prepare a printable
model. Always verify wall thickness, root reinforcement, balance, and clearance
before testing in a wind tunnel.
"""


def build_onshape_package(
    inputs: SimulationInput,
    *,
    design_name: str = "wind_turbine_design",
) -> bytes:
    """Build a ZIP file containing CAD-friendly Onshape reference files."""

    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("blade_geometry.csv", blade_geometry_csv(inputs))
        archive.writestr("airfoil_sections.csv", airfoil_sections_csv(inputs))
        archive.writestr("blade_planform.dxf", blade_planform_dxf(inputs))
        archive.writestr("section_profiles.dxf", section_profiles_dxf(inputs))
        archive.writestr("section_profiles/README.md", _section_profiles_readme(inputs))
        for filename, dxf_text in individual_section_profile_dxfs(inputs).items():
            archive.writestr(f"section_profiles/{filename}", dxf_text)
        archive.writestr(
            "design_metadata.json",
            json.dumps(_metadata(inputs, design_name), indent=2, ensure_ascii=False),
        )
        archive.writestr("onshape_build_guide.md", onshape_build_guide(inputs, design_name))
    return buffer.getvalue()
