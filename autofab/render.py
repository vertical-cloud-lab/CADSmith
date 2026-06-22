"""Render STL files to PNG images for vision agent inspection.

Uses VTK for proper Phong-shaded 3D rendering with smooth surface
normals, specular highlights, and no visible triangle mesh edges.

Produces a three-view composite image:
  - Left:   Isometric view (elev=35, azim=45)
  - Center: High-angle rear view (elev=65, azim=220) — reveals top-face
            features like holes, bores, cavities
  - Right:  Low front profile (elev=10, azim=0) — shows vertical profile,
            wall heights, gear spacing, slots
"""

import os
import numpy as np


def render_stl_to_png(stl_path: str, png_path: str, title: str = "") -> str:
    """Render an STL file to a three-view composite PNG.

    Three complementary views are placed side-by-side in a single image:
    isometric (left), high-angle rear (center), and front profile (right).

    Args:
        stl_path: Path to the STL file.
        png_path: Output PNG path.
        title: Optional title (unused, kept for API compatibility).

    Returns:
        The png_path on success.
    """
    import vtk

    # Read STL
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)
    reader.Update()

    # Compute smooth normals, splitting at sharp edges
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(30.0)
    normals.SplittingOn()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.Update()

    # Compute camera framing from mesh bounds
    bounds = normals.GetOutput().GetBounds()
    center = [
        (bounds[0] + bounds[1]) / 2,
        (bounds[2] + bounds[3]) / 2,
        (bounds[4] + bounds[5]) / 2,
    ]
    extent = max(
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    )

    def _make_actor():
        """Create a Phong-shaded actor from the STL normals pipeline."""
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.45, 0.68, 0.95)  # Light blue
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(20)
        actor.GetProperty().SetAmbient(0.2)
        actor.GetProperty().SetDiffuse(0.8)
        actor.GetProperty().SetInterpolationToPhong()
        return actor

    def _setup_camera(renderer, elev, azim, zoom=0.85):
        """Position camera at given elevation/azimuth angles."""
        distance = extent * 2.5
        elev_rad = np.radians(elev)
        azim_rad = np.radians(azim)
        cam_x = center[0] + distance * np.cos(elev_rad) * np.cos(azim_rad)
        cam_y = center[1] + distance * np.cos(elev_rad) * np.sin(azim_rad)
        cam_z = center[2] + distance * np.sin(elev_rad)
        camera = renderer.GetActiveCamera()
        camera.SetPosition(cam_x, cam_y, cam_z)
        camera.SetFocalPoint(*center)
        camera.SetViewUp(0, 0, 1)
        renderer.ResetCamera()
        camera.Zoom(zoom)

    # View 1 (left): Isometric — overall shape
    ren1 = vtk.vtkRenderer()
    ren1.AddActor(_make_actor())
    ren1.SetBackground(1.0, 1.0, 1.0)
    ren1.SetViewport(0, 0, 1 / 3, 1.0)
    _setup_camera(ren1, 35, 45)

    # View 2 (center): High-angle rear — top-face features
    ren2 = vtk.vtkRenderer()
    ren2.AddActor(_make_actor())
    ren2.SetBackground(1.0, 1.0, 1.0)
    ren2.SetViewport(1 / 3, 0, 2 / 3, 1.0)
    _setup_camera(ren2, 65, 220)

    # View 3 (right): Low front profile — vertical profile
    ren3 = vtk.vtkRenderer()
    ren3.AddActor(_make_actor())
    ren3.SetBackground(1.0, 1.0, 1.0)
    ren3.SetViewport(2 / 3, 0, 1.0, 1.0)
    _setup_camera(ren3, 10, 0)

    # Offscreen render window
    render_window = vtk.vtkRenderWindow()
    render_window.SetOffScreenRendering(1)
    render_window.AddRenderer(ren1)
    render_window.AddRenderer(ren2)
    render_window.AddRenderer(ren3)
    render_window.SetSize(2400, 800)
    render_window.Render()

    # Write PNG at 2x resolution
    os.makedirs(os.path.dirname(png_path) if os.path.dirname(png_path) else ".", exist_ok=True)
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(render_window)
    w2i.SetScale(2)
    w2i.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(png_path)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()

    render_window.Finalize()

    return png_path


# Standard isometric viewpoints (elevation, azimuth) in degrees. The elevation
# of ~35.264 deg is the true isometric angle; the four azimuths look in from
# each corner so every face of an assembly is covered across the set.
ISO_ANGLES = (
    ("front_right", 35.264, 45),
    ("back_right", 35.264, 135),
    ("back_left", 35.264, 225),
    ("front_left", 35.264, 315),
    ("top_down", 80.0, 45),
    ("low_front", 12.0, 0),
)


def render_stl_iso_views(
    stl_path: str,
    out_dir: str,
    prefix: str = "iso",
    angles=ISO_ANGLES,
    contact_sheet: str | None = None,
) -> list:
    """Render an STL from several isometric angles to individual PNGs.

    Each angle in ``angles`` produces a standalone Phong-shaded PNG, and an
    optional combined contact sheet tiles them into a single image. This is
    intended for inspecting a full assembly from many directions at once.

    Args:
        stl_path: Path to the STL file.
        out_dir: Directory to write the per-angle PNGs into (created if absent).
        prefix: Filename prefix for each per-angle PNG (``<prefix>_<name>.png``).
        angles: Iterable of ``(name, elevation_deg, azimuth_deg)`` viewpoints.
        contact_sheet: If given, also write a single tiled PNG to this path.

    Returns:
        A list of the per-angle PNG paths written, in order.
    """
    import vtk

    angles = list(angles)
    os.makedirs(out_dir, exist_ok=True)

    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)
    reader.Update()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(30.0)
    normals.SplittingOn()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.Update()

    bounds = normals.GetOutput().GetBounds()
    center = [
        (bounds[0] + bounds[1]) / 2,
        (bounds[2] + bounds[3]) / 2,
        (bounds[4] + bounds[5]) / 2,
    ]
    extent = max(
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    )

    def _make_actor():
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.45, 0.68, 0.95)
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(20)
        actor.GetProperty().SetAmbient(0.2)
        actor.GetProperty().SetDiffuse(0.8)
        actor.GetProperty().SetInterpolationToPhong()
        return actor

    def _setup_camera(renderer, elev, azim, zoom=0.85):
        distance = extent * 2.5
        elev_rad = np.radians(elev)
        azim_rad = np.radians(azim)
        cam_x = center[0] + distance * np.cos(elev_rad) * np.cos(azim_rad)
        cam_y = center[1] + distance * np.cos(elev_rad) * np.sin(azim_rad)
        cam_z = center[2] + distance * np.sin(elev_rad)
        camera = renderer.GetActiveCamera()
        camera.SetPosition(cam_x, cam_y, cam_z)
        camera.SetFocalPoint(*center)
        camera.SetViewUp(0, 0, 1)
        renderer.ResetCamera()
        camera.Zoom(zoom)

    def _render_single(elev, azim, png_path):
        renderer = vtk.vtkRenderer()
        renderer.AddActor(_make_actor())
        renderer.SetBackground(1.0, 1.0, 1.0)
        _setup_camera(renderer, elev, azim)

        rw = vtk.vtkRenderWindow()
        rw.SetOffScreenRendering(1)
        rw.AddRenderer(renderer)
        rw.SetSize(1000, 1000)
        rw.Render()

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(rw)
        w2i.SetScale(2)
        w2i.Update()

        writer = vtk.vtkPNGWriter()
        writer.SetFileName(png_path)
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()
        rw.Finalize()

    written = []
    for name, elev, azim in angles:
        png_path = os.path.join(out_dir, f"{prefix}_{name}.png")
        _render_single(elev, azim, png_path)
        written.append(png_path)

    if contact_sheet and written:
        _tile_pngs(written, contact_sheet)

    return written


def _tile_pngs(png_paths: list, out_path: str, cols: int = 3) -> str:
    """Tile equally sized PNGs into a single contact-sheet PNG."""
    import math

    import vtk

    n = len(png_paths)
    cols = min(cols, n)
    rows = int(math.ceil(n / cols))

    readers = []
    for p in png_paths:
        r = vtk.vtkPNGReader()
        r.SetFileName(p)
        r.Update()
        readers.append(r)

    dims = readers[0].GetOutput().GetDimensions()
    tile_w, tile_h = dims[0], dims[1]

    blank = vtk.vtkImageCanvasSource2D()
    blank.SetScalarTypeToUnsignedChar()
    blank.SetNumberOfScalarComponents(3)
    blank.SetExtent(0, tile_w - 1, 0, tile_h - 1, 0, 0)
    blank.SetDrawColor(255, 255, 255)
    blank.FillBox(0, tile_w - 1, 0, tile_h - 1)
    blank.Update()

    append = vtk.vtkImageAppend()
    append.SetAppendAxis(1)  # stack rows bottom-to-top
    for row in range(rows - 1, -1, -1):
        row_append = vtk.vtkImageAppend()
        row_append.SetAppendAxis(0)  # left-to-right
        for col in range(cols):
            idx = row * cols + col
            if idx < n:
                row_append.AddInputData(readers[idx].GetOutput())
            else:
                row_append.AddInputData(blank.GetOutput())
        row_append.Update()
        append.AddInputData(row_append.GetOutput())
    append.Update()

    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".",
                exist_ok=True)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(out_path)
    writer.SetInputData(append.GetOutput())
    writer.Write()
    return out_path
