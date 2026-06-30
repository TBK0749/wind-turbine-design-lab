# Onshape Workflow Manual

Wind Turbine Design Lab exports an Onshape package so students can rebuild a
selected blade in CAD before creating an STL for 3D printing. This manual walks
through the workflow slowly, assuming the user is new to Onshape.

This export is not a finished STL. It is a CAD reference package: it gives the
blade table, 2D outlines, and airfoil section profiles. Students still need to
build the 3D part in Onshape, check the hub connection, and export STL from
Onshape.

## 1. Files in the downloaded ZIP

Click **Download Onshape package** in the app, then unzip the file. You should
see these files:

| File | Use |
| --- | --- |
| `blade_geometry.csv` | Main table: section, position, chord, twist, airfoil, and role. |
| `airfoil_sections.csv` | Airfoil metadata and recommended Reynolds-number ranges. |
| `blade_planform.dxf` | Top-view blade outline in centimetres. Use it as an outline check. |
| `section_profiles/section_XX_*.dxf` | One ready-to-insert DXF per blade section. Use these for the main workflow. |
| `section_profiles/README.md` | List of the individual section DXF files and their chord/twist values. |
| `section_profiles.dxf` | Combined profile overview. Use it only as a visual reference. |
| `design_metadata.json` | Simulator settings saved with the export. |
| `onshape_build_guide.md` | Short build notes included inside the export. |

For the first Onshape build, keep `blade_geometry.csv` open beside Onshape. It
is the map for where every airfoil section belongs.

## 2. Read the geometry table first

Open `blade_geometry.csv`. The important columns are:

| Column | Meaning |
| --- | --- |
| `Section` | Root-to-tip section number. |
| `Position (cm)` | Distance from the turbine center along the blade radius. |
| `Chord (cm)` | Airfoil width from leading edge to trailing edge. |
| `Twist (deg)` | Rotation angle for that section. |
| `Airfoil` | Airfoil profile assigned to that section. |
| `Role` | Plain-language reason for using that airfoil there. |

Example:

```text
Section,Position (cm),Chord (cm),Twist (deg),Airfoil
1 (Root),6.0,9.0,20.0,NACA 4418
2,14.0,7.5,15.0,SG6040
3,24.0,5.8,10.0,SG6043
4,34.0,4.2,6.0,SG6043
5,43.0,3.0,2.0,NACA 2412
6 (Tip),50.0,1.8,0.0,E387
```

The table positions are measured from the rotor center. In CAD it is usually
easier to start the blade at the first section. If section 1 is at 6 cm and
section 6 is at 50 cm, then the CAD station offsets from section 1 are:

| Section | Table position | CAD offset from section 1 |
| --- | ---: | ---: |
| 1 | 6 cm | 0 cm |
| 2 | 14 cm | 8 cm |
| 3 | 24 cm | 18 cm |
| 4 | 34 cm | 28 cm |
| 5 | 43 cm | 37 cm |
| 6 | 50 cm | 44 cm |

Formula:

```text
CAD offset = section position - root section position
```

## 3. Create a new Onshape document

1. Open Onshape.
2. Create a new Document.
3. Open a Part Studio.
4. Use centimetres as the working unit when importing DXF files.

If a sketch imports much too large or much too small, the unit was probably
wrong. Delete the import and insert it again with centimetres.

## 4. Import the top-view planform

The planform is a top-view blade outline. It is useful as a visual guide, but it
is not the main Loft input.

1. Start a Sketch on the Top plane.
2. Insert or import `blade_planform.dxf`.
3. Choose centimetres if Onshape asks for units.
4. Keep this sketch visible as a reference.

Use this file to check whether the final blade outline looks similar to the
simulator's top-view design.

## 5. Create section planes

Create one plane for each blade section. The planes should be perpendicular to
the blade length direction.

For the example table above:

| Plane name | Offset from first/root section |
| --- | ---: |
| `S1 Root` | 0 cm |
| `S2` | 8 cm |
| `S3` | 18 cm |
| `S4` | 28 cm |
| `S5` | 37 cm |
| `S6 Tip` | 44 cm |

The actual numbers must come from your own `blade_geometry.csv`.

### What S1 Root means in Onshape

When this manual says **use the Right plane as S1 Root**, it means:

```text
Do not create a new plane for section 1.
The existing Right plane is section 1 / root.
```

In the Part Studio feature tree, expand **Default geometry**. You should see:

```text
Origin
Top
Front
Right
```

Use `Right` as the first root section plane. Later, when you sketch the first
airfoil profile, create that sketch directly on `Right`.

### Create the offset planes for S2 to S6

1. If a failed Plane dialog is open, click the red `X` to cancel it.
2. Expand **Default geometry** in the left feature tree.
3. Click the **Plane** tool.
4. Set the plane type to **Offset**.
5. Click the `Entities` box.
6. Select the existing `Right` plane from the feature tree or from the graphics area.
7. Change the distance from the default value, often `1 in`, to the required centimetre value.
8. For S2, type `8 cm`.
9. Click the green check mark.

Repeat the same process using `Right` as the base plane every time:

| New plane | Base plane to select | Offset distance |
| --- | --- | ---: |
| `S2` | `Right` | `8 cm` |
| `S3` | `Right` | `18 cm` |
| `S4` | `Right` | `28 cm` |
| `S5` | `Right` | `37 cm` |
| `S6 Tip` | `Right` | `44 cm` |

Important: do not leave the distance as `1 in`. Type the centimetre unit
directly, such as `8 cm`, `18 cm`, or `44 cm`.

If the new plane appears on the wrong side, use **Flip normal** in the Plane
dialog.

After creating each plane, rename it immediately. Clear names make Loft much
easier.

### Common plane creation error

If Onshape shows this message:

```text
Offset plane requires a plane, circle, ellipse, or arc to offset from.
```

The `Entities` box is still empty. You clicked the Plane tool, but you did not
select a base plane yet.

Fix:

```text
Plane tool
-> Offset
-> click Entities
-> click Right plane
-> type 8 cm
-> green check
```

For this workflow:

```text
Right plane = S1 Root
Offset 8 cm from Right = S2
Offset 18 cm from Right = S3
Offset 28 cm from Right = S4
Offset 37 cm from Right = S5
Offset 44 cm from Right = S6 Tip
```

## 6. Place airfoil profiles on the planes

Use the individual files inside the `section_profiles/` folder. The folder
contains one ready-to-insert DXF per blade section. Each file contains one
airfoil only, scaled to the correct chord, centred near the sketch origin, and
pre-rotated by the section twist angle.

For example:

| Plane | Insert this DXF |
| --- | --- |
| `S1 Root` | `section_profiles/section_01_root_NACA4418.dxf` |
| `S2` | `section_profiles/section_02_SG6040.dxf` |
| `S3` | `section_profiles/section_03_SG6043.dxf` |
| `S4` | `section_profiles/section_04_SG6043.dxf` |
| `S5` | `section_profiles/section_05_NACA2412.dxf` |
| `S6 Tip` | `section_profiles/section_06_tip_E387.dxf` |

These filenames are examples from one preset. Your package may use different
airfoil names, so always check `section_profiles/README.md` or
`blade_geometry.csv`.

This is the beginner workflow:

1. Create a Sketch on plane `S1 Root`.
2. Insert `section_profiles/section_01_root_NACA4418.dxf`.
3. Choose centimetres if Onshape asks for units.
4. Confirm the sketch.
5. Create a Sketch on plane `S2`.
6. Insert the section 2 DXF file.
7. Repeat from root to tip.

With the individual section DXFs, you do not need to delete the other sections
and you usually do not need to manually rotate twist. The individual files are
already prepared for that section.

Do not use `section_profiles.dxf` as the main beginner workflow. That combined
file is kept only as an overview/reference drawing because it contains all
sections together.

## 7. Apply twist correctly

Twist is the local rotation of each airfoil section.

The individual `section_profiles/section_XX_*.dxf` files are already pre-rotated
by the twist angle in `blade_geometry.csv`. For the beginner workflow, insert
the individual section file and do not rotate it again.

For each sketch in the beginner workflow:

| Section | Twist handling |
| --- | --- |
| Section 1 | Already applied in the section 1 DXF file |
| Section 2 | Already applied in the section 2 DXF file |
| Section 3 | Already applied in the section 3 DXF file |
| Section 4 | Already applied in the section 4 DXF file |
| Section 5 | Already applied in the section 5 DXF file |
| Section 6 | Already applied in the section 6 DXF file |

Use the twist values in `blade_geometry.csv` for checking only. Do not rotate
the individual DXF files again unless you intentionally edit the CAD model.

Keep the rotation direction consistent. If the Loft appears twisted backward,
undo, reverse the rotation direction, and try again.

## 8. Align the profiles before Loft

Loft works best when all profiles share a consistent reference point.

Pick one alignment method and use it for every section:

- align each profile by chord midpoint; or
- align each profile by leading edge; or
- align each profile by trailing edge.

For classroom blades, chord midpoint alignment is usually easiest. Leading-edge
alignment can also work, but do not mix alignment methods section by section.

Before Loft, check:

- every sketch has exactly one closed airfoil profile;
- profiles are ordered from root to tip;
- the same side of the airfoil faces the same direction on every plane;
- twist is applied in the intended direction.

## 9. Create the 3D blade with Loft

1. Start the Loft feature.
2. Choose **Solid** if each profile is a closed region.
3. Select the section sketches in order:
   - section 1 root profile;
   - section 2 profile;
   - section 3 profile;
   - section 4 profile;
   - section 5 profile;
   - section 6 tip profile.
4. Preview the shape.
5. If the blade twists strangely, cancel and check profile alignment and order.
6. Accept the Loft.

If Solid Loft fails, try Surface Loft first. If Surface Loft works but Solid Loft
does not, at least one profile may not be a clean closed region.

## 10. Add the hub connection

The simulator exports the blade geometry, not the final hub. Students must add a
real mount that matches their generator shaft and competition rules.

Common classroom approach:

1. Create a cylinder for the hub.
2. Add holes or shaft adapter geometry to match the generator.
3. Extend or thicken the blade root so it joins the hub safely.
4. Fillet the root connection if possible.
5. Check that the full rotor diameter does not exceed the rule limit.

For a 1 m diameter rule, the final rotor radius must be no more than 50 cm from
the center to the farthest blade tip.

## 11. Create three blades

After one blade and hub connection are correct:

1. Use Circular Pattern.
2. Select the blade body or blade feature.
3. Use the hub axis as the rotation axis.
4. Set instance count to `3`.
5. The blades should be spaced 120 degrees apart.

Check that the three-blade pattern does not overlap the hub, shaft, or frame.

## 12. Export STL from Onshape

When the CAD model is ready:

1. Right-click the finished Part or Assembly.
2. Choose Export.
3. Select STL.
4. Use millimetres if your slicer expects millimetres.
5. Open the STL in your slicer.
6. Check print orientation, supports, wall thickness, and root strength.

Always inspect the STL before printing. A successful Onshape export does not
guarantee the part is strong enough for testing.

## 13. Troubleshooting

| Problem | Likely cause | Fix |
| --- | --- | --- |
| DXF imports at the wrong size | Wrong import unit | Reimport using centimetres. |
| Loft fails | Profile is not closed or contains extra curves | Clean the sketch; leave one closed profile per section. |
| Loft twists into a knot | Profiles selected out of order or aligned inconsistently | Select root to tip; align all profiles by the same reference point. |
| Blade looks mirrored | Profile orientation is flipped on one or more planes | Flip or rotate the affected sketch. |
| Blade outline does not match planform | Profiles are shifted sideways | Use `blade_planform.dxf` as a top-view reference and realign profiles. |
| Final part is too large | Rotor diameter or unit conversion issue | Check radius and units before exporting STL. |
| Root breaks easily | Hub connection too thin | Add root reinforcement, fillets, or a thicker hub mount. |

## 14. Recommended beginner workflow

For the first successful build, do not try to optimize everything.

1. Load the **Easy CAD / Easy Print** preset in the simulator.
2. Download the Onshape package.
3. Build only one blade first.
4. Use chord midpoint alignment for every section.
5. Loft the blade.
6. Add a simple hub connector.
7. Export STL.
8. Print one small test if possible.
9. Return to the simulator and improve one variable at a time.

## 15. What the simulator does not do yet

The current project does not automatically create:

- a finished Onshape document;
- a complete parametric CAD model;
- a print-ready STL;
- supports, slicer settings, or infill settings;
- structural safety verification.

The export is intended to reduce manual copying errors and make CAD rebuilding
more consistent. Real wind-tunnel testing is still required for final
calibration.

## References

- Onshape Help: Insert DXF or DWG into a sketch - <https://cad.onshape.com/help/Content/Sketch/insert_dwg_or_dxf.htm>
- Onshape Help: Loft - <https://cad.onshape.com/help/Content/PartStudio/loft.htm>
