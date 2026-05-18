"""Generate diagrams of the powder-doser mount assembly.

Produces four PNGs in ``assets/powder_doser/diagrams/``:

1. ``01_assembly.png``  — labelled isometric view of the level assembly.
2. ``02_exploded.png``  — exploded view (mounting plate lifted away from
   the base plate) showing how the two parts mate.
3. ``03_tilt_sequence.png`` — three side views at 0°, 45°, 90° tilt about
   the hinge axis, showing the rotation range driven by the actuator.
4. ``04_flow_and_clearance.png`` — annotated side view of the assembly on
   a bench with a cup on a tared scale beneath the dispense point,
   showing the powder flow path.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.patches import FancyArrowPatch, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from powder_doser_mount import (  # noqa: E402
    BP_Z_TOP,
    HINGE_X,
    LEG_HEIGHT,
    MP_T,
)

STL_DIR = HERE / "stl"
OUT_DIR = HERE / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_mesh(name: str) -> trimesh.Trimesh:
    return trimesh.load_mesh(str(STL_DIR / name))


def add_mesh(ax, mesh: trimesh.Trimesh, *, color, alpha=0.9,
             edgecolor=(0.1, 0.1, 0.1), linewidth=0.15,
             translate=(0.0, 0.0, 0.0),
             rotate_y_deg: float = 0.0,
             rotate_about=(0.0, 0.0, 0.0)) -> None:
    """Render a trimesh as a Poly3DCollection."""
    verts = np.asarray(mesh.vertices, dtype=float).copy()

    if rotate_y_deg:
        theta = math.radians(rotate_y_deg)
        c, s = math.cos(theta), math.sin(theta)
        R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        about = np.asarray(rotate_about, dtype=float)
        verts = (verts - about) @ R.T + about

    verts = verts + np.asarray(translate, dtype=float)
    tris = verts[mesh.faces]

    coll = Poly3DCollection(
        tris,
        facecolor=color,
        edgecolor=edgecolor,
        linewidth=linewidth,
        alpha=alpha,
    )
    ax.add_collection3d(coll)


def setup_iso_axes(ax, *, xlim, ylim, zlim, title="",
                   elev=22, azim=-55):
    ax.set_box_aspect(
        (xlim[1] - xlim[0], ylim[1] - ylim[0], zlim[1] - zlim[0])
    )
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_zlim(*zlim)
    ax.view_init(elev=elev, azim=azim)
    ax.set_xlabel("X (auger axis) [mm]")
    ax.set_ylabel("Y (hinge axis) [mm]")
    ax.set_zlabel("Z [mm]")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)


def standard_limits():
    return (
        (-220, 60),   # x
        (-80, 80),    # y
        (-200, 40),   # z
    )


# Color palette
ORANGE = (0.90, 0.55, 0.20)
GREY = (0.70, 0.72, 0.78)
RED = (0.85, 0.20, 0.20)


# ---------------------------------------------------------------------------
# Diagram 1: Assembly
# ---------------------------------------------------------------------------

def diagram_assembly():
    mp = load_mesh("mounting_plate.stl")
    bp = load_mesh("base_plate.stl")

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    add_mesh(ax, bp, color=GREY)
    add_mesh(ax, mp, color=ORANGE)

    xlim, ylim, zlim = standard_limits()
    setup_iso_axes(ax, xlim=xlim, ylim=ylim, zlim=zlim,
                   title="Powder-doser tilt assembly (level / 0° tilt)")

    # Origin marker (dispense point)
    ax.scatter([0], [0], [0], color=RED, s=60, zorder=10)
    ax.text(6, 6, 8, "dispense\norigin (0,0,0)", color=RED, fontsize=9)

    # Hinge axis (Y line at x=HINGE_X, z=0).
    ax.plot([HINGE_X, HINGE_X], [-70, 70], [0, 0], color=RED, linewidth=1.2,
            linestyle="--")
    ax.text(HINGE_X, 72, 5, "hinge axis (Y)", color=RED, fontsize=9)

    # Labels for the two parts.
    ax.text(-10, 0, 8, "mounting plate", color=(0.6, 0.35, 0.1),
            fontsize=10, weight="bold")
    ax.text(-160, 0, BP_Z_TOP + 8, "base plate", color=(0.3, 0.3, 0.4),
            fontsize=10, weight="bold")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_assembly.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Diagram 2: Exploded view
# ---------------------------------------------------------------------------

def diagram_exploded():
    mp = load_mesh("mounting_plate.stl")
    bp = load_mesh("base_plate.stl")

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Lift the mounting plate well above its mating clevis.
    add_mesh(ax, bp, color=GREY)
    add_mesh(ax, mp, color=ORANGE, translate=(0, 0, 60))

    # Dashed line showing the assembly direction (hinge pin path).
    ax.plot([HINGE_X, HINGE_X], [0, 0], [-5, 70], color=RED, linewidth=1.2,
            linestyle=":")
    ax.text(HINGE_X + 5, 2, 40, "engage on hinge pin (Y)", color=RED,
            fontsize=9)

    xlim, ylim, zlim = standard_limits()
    zlim = (zlim[0], 120)
    setup_iso_axes(ax, xlim=xlim, ylim=ylim, zlim=zlim,
                   title="Exploded view: clevis ears straddle the base tab")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_exploded.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Diagram 3: Tilt sequence
# ---------------------------------------------------------------------------

def diagram_tilt_sequence():
    mp = load_mesh("mounting_plate.stl")
    bp = load_mesh("base_plate.stl")

    fig = plt.figure(figsize=(15, 6))

    angles = [0, 45, 90]
    for i, deg in enumerate(angles, start=1):
        ax = fig.add_subplot(1, 3, i, projection="3d")
        add_mesh(ax, bp, color=GREY)
        add_mesh(
            ax, mp, color=ORANGE,
            rotate_y_deg=deg, rotate_about=(HINGE_X, 0.0, 0.0),
        )
        # Side view (looking along +Y).
        xlim, ylim, zlim = standard_limits()
        setup_iso_axes(ax, xlim=xlim, ylim=ylim, zlim=zlim,
                       title=f"tilt = {deg}°",
                       elev=5, azim=-89)
        # Pin marker (on hinge axis).
        ax.scatter([HINGE_X], [0], [0], color=RED, s=40)

    fig.suptitle(
        "Tilt sequence about hinge axis "
        "(driven by linear actuator on rear pivot post)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_tilt_sequence.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Diagram 4: Powder flow + cup/scale clearance (2D side view)
# ---------------------------------------------------------------------------

def diagram_flow_and_clearance():
    fig, ax = plt.subplots(figsize=(12, 8))

    # Geometry summary in side view (X-Z plane, looking along +Y).
    bench_z = BP_Z_TOP - 8 - LEG_HEIGHT   # base bottom - leg height
    bp_x_front = HINGE_X - 5.0
    bp_x_rear = bp_x_front - 170.0
    bp_x_center = (bp_x_front + bp_x_rear) / 2.0

    # Bench surface.
    ax.add_patch(Rectangle((-260, bench_z - 6), 380, 6,
                           facecolor=(0.55, 0.4, 0.25), edgecolor="black"))
    ax.text(110, bench_z - 3, "bench", fontsize=9, ha="right",
            va="center")

    # Scale on bench, directly under dispense origin x=0.
    scale_w = 110
    scale_h = 22
    scale_x0 = -scale_w / 2
    ax.add_patch(Rectangle((scale_x0, bench_z), scale_w, scale_h,
                           facecolor=(0.2, 0.2, 0.2), edgecolor="black"))
    ax.text(scale_x0 + 5, bench_z + scale_h / 2, "tared scale",
            color="white", fontsize=9, va="center")

    # Cup on the scale.
    cup_top_z = bench_z + scale_h + 60
    cup_w_top = 60
    cup_w_bot = 48
    cup_poly = np.array([
        [-cup_w_top / 2, cup_top_z],
        [cup_w_top / 2, cup_top_z],
        [cup_w_bot / 2, bench_z + scale_h],
        [-cup_w_bot / 2, bench_z + scale_h],
    ])
    ax.fill(cup_poly[:, 0], cup_poly[:, 1],
            facecolor=(0.95, 0.95, 1.0), edgecolor="black", alpha=0.85)
    ax.text(cup_w_top / 2 + 4, cup_top_z - 25, "powder cup",
            fontsize=9)

    # Base plate cross-section.
    ax.add_patch(Rectangle((bp_x_rear, BP_Z_TOP - 8),
                           bp_x_front - bp_x_rear, 8,
                           facecolor=GREY, edgecolor="black"))
    ax.text(bp_x_rear + 8, BP_Z_TOP - 4, "base plate", fontsize=9,
            va="center")

    # Two legs visible (front + rear from side view).
    for cx in (bp_x_rear + 14, bp_x_front - 14):
        ax.add_patch(Rectangle((cx - 7, bench_z),
                               14, BP_Z_TOP - 8 - bench_z,
                               facecolor=GREY, edgecolor="black"))

    # Mating tab rising to the hinge axis at z=0.
    ax.add_patch(Rectangle((HINGE_X - 13, BP_Z_TOP), 26, 6 - BP_Z_TOP,
                           facecolor=GREY, edgecolor="black"))
    ax.text(HINGE_X - 16, BP_Z_TOP / 2, "mating tab\n(rises to hinge)",
            fontsize=8, ha="right", va="center")

    # Actuator pivot post.
    post_x = HINGE_X - 90
    ax.add_patch(Rectangle((post_x - 12, BP_Z_TOP), 24, 35,
                           facecolor=GREY, edgecolor="black"))
    ax.plot([post_x], [BP_Z_TOP + 28], "ko", markersize=5)
    ax.text(post_x, BP_Z_TOP + 45, "actuator pivot",
            fontsize=8, ha="center")

    # Mounting plate (side view at 0°).
    mp_x_min = HINGE_X + 20 - 65
    mp_x_max = HINGE_X + 20 + 65
    ax.add_patch(Rectangle((mp_x_min, -MP_T), mp_x_max - mp_x_min,
                           MP_T, facecolor=ORANGE, edgecolor="black"))
    # U-slot opens out +X edge.
    ax.add_patch(Rectangle((mp_x_max - 50, -MP_T), 55, MP_T,
                           facecolor="white", edgecolor="black",
                           linestyle="--"))
    ax.text(mp_x_min, 12, "mounting plate (U-slot for dispense column)",
            fontsize=9)

    # Clevis ear (one visible from this side; the other is behind).
    ax.add_patch(Rectangle((HINGE_X - 14, -28), 28, 38,
                           facecolor=ORANGE, edgecolor="black", alpha=0.7))
    ax.plot([HINGE_X], [0], "o", color=RED, markersize=8, zorder=10)
    ax.annotate("hinge pin (x=-35, z=0)",
                xy=(HINGE_X, 0), xytext=(HINGE_X - 60, 25),
                fontsize=8, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))

    # Dispense origin marker + powder flow arrow.
    ax.plot([0], [0], "o", color=RED, markersize=8, zorder=10)
    ax.annotate("dispense origin (0,0,0)",
                xy=(0, 0), xytext=(35, 22),
                fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.8))
    ax.add_patch(FancyArrowPatch(
        (0, -2), (0, cup_top_z + 2),
        arrowstyle="->", mutation_scale=18,
        color=(0.4, 0.2, 0.1), lw=1.6,
    ))
    ax.text(-4, (cup_top_z) / 2, "powder flow",
            fontsize=10, color=(0.4, 0.2, 0.1),
            ha="right", rotation=90, va="center")

    # Axes / framing.
    ax.set_xlim(-260, 130)
    ax.set_ylim(bench_z - 25, 60)
    ax.set_aspect("equal")
    ax.set_xlabel("X (auger axis) [mm]")
    ax.set_ylabel("Z [mm]")
    ax.set_title(
        "Powder flow + cup/scale clearance "
        "(side view at level tilt, looking along +Y)"
    )
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "04_flow_and_clearance.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    diagram_assembly()
    diagram_exploded()
    diagram_tilt_sequence()
    diagram_flow_and_clearance()
    print("Wrote diagrams to", OUT_DIR)
