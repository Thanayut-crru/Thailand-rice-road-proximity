from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#263441"
EDGE = "#526474"


def box(ax, x, y, w, h, text, face="#FFFFFF", edge=EDGE, size=9.2):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=face, edgecolor=edge,
                           linewidth=1.5, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=INK, fontsize=size, linespacing=1.3, zorder=3)


def arrow(ax, a, b, dashed=False):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13,
                                 color=EDGE, linewidth=1.4,
                                 linestyle="--" if dashed else "-", zorder=4))


fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
ax.set_xlim(0, 12)
ax.set_ylim(0, 10)
ax.axis("off")

ax.text(6, 9.62, "Road-Class Sensitivity Analysis for Rice–Road Proximity",
        ha="center", fontsize=17, fontweight="bold", color=INK)
ax.text(6, 9.28, "Thailand rice maps (2023) × OSM/Geofabrik roads (snapshot 10 June 2026)",
        ha="center", fontsize=10.5, color="#667788")

box(ax, 0.45, 7.85, 3.35, 1.05,
    "OSM road input: 11 fclass types\n1,607,087 segments\nResidential + unclassified = 91.40%",
    face="#DCECF8", edge="#5E87A8")
box(ax, 4.33, 7.85, 3.35, 1.05,
    "GCD-Rice 30 m binary maps\nMajor rice and minor rice (2023)\nEPSG:4326",
    face="#DCECF8", edge="#5E87A8")
box(ax, 8.20, 7.85, 3.35, 1.05,
    "VIIRS SVDNB Aug 2023\nTarget ~500 m grid only\nNo radiance threshold in this analysis",
    face="#FFF3DA", edge="#C08A2F")

box(ax, 0.45, 6.15, 3.35, 1.00,
    "G1 — Major roads + links\nmotorway, trunk, primary\nand corresponding link classes",
    face="#DCE8F1", edge="#355C7D", size=8.8)
box(ax, 4.33, 6.15, 3.35, 1.00,
    "G2 — Expanded network\nG1 + secondary + secondary_link\n+ tertiary",
    face="#DFE8F7", edge="#6C8EBF", size=8.8)
box(ax, 8.20, 6.15, 3.35, 1.00,
    "G3 — All 11 classes\nG2 + residential + unclassified\n(original pooled road network)",
    face="#F2DDE4", edge="#B9607C", size=8.8)

# OSM input branches into the three cumulative road-network scenarios.
ax.plot([2.125, 2.125], [7.85, 7.55], color=EDGE, linewidth=1.4, zorder=1)
ax.plot([2.125, 9.875], [7.55, 7.55], color=EDGE, linewidth=1.4, zorder=1)
for x in [2.125, 6.005, 9.875]:
    arrow(ax, (x, 7.55), (x, 7.15))

box(ax, 2.25, 4.45, 7.50, 0.95,
    "Rasterize each cumulative network on the native rice grid (all_touched=True)\n"
    "Circular binary dilation: radius 1 pixel (~30 m) and radius 2 pixels (~60 m)",
    face="#F7F7F7")
for x in [2.125, 6.005, 9.875]:
    arrow(ax, (x, 6.15), (6.0, 5.40))

box(ax, 2.25, 2.95, 7.50, 0.80,
    "road_rice = (rice = 1) AND (road buffer = 1)\n"
    "Aggregate to the VIIRS grid with Resampling.average",
    face="#FFF1C7", edge="#C6A03A")
arrow(ax, (6.0, 4.45), (6.0, 3.75))

# Rice is combined with each road mask; VIIRS supplies only the target grid.
ax.plot([6.005, 0.20, 0.20], [7.85, 7.55, 3.35], color=EDGE,
        linewidth=1.2, linestyle="--", zorder=1)
arrow(ax, (0.20, 3.35), (2.25, 3.35), dashed=True)
ax.text(0.32, 5.10, "rice mask", rotation=90, fontsize=8.5, color=EDGE,
        ha="left", va="center", backgroundcolor="white")
ax.plot([9.875, 11.80, 11.80], [7.85, 7.55, 3.35], color=EDGE,
        linewidth=1.2, linestyle="--", zorder=1)
arrow(ax, (11.80, 3.35), (9.75, 3.35), dashed=True)
ax.text(11.68, 5.10, "target grid", rotation=90, fontsize=8.5, color=EDGE,
        ha="right", va="center", backgroundcolor="white")

box(ax, 0.75, 1.35, 3.25, 0.90,
    "National and regional tables\nacres and proximity proportion",
    face="#DDEED8", edge="#6C9A5E")
box(ax, 4.38, 1.35, 3.25, 0.90,
    "Incremental contrasts\nG2 − G1 and G3 − G2",
    face="#DDEED8", edge="#6C9A5E")
box(ax, 8.00, 1.35, 3.25, 0.90,
    "Figures and 12 fraction rasters\n2 rice types × 3 groups × 2 radii",
    face="#DDEED8", edge="#6C9A5E")
for x in [2.375, 6.005, 9.625]:
    arrow(ax, (6.0, 2.95), (x, 2.25))

ax.text(6, 0.58,
        "Interpretation: road proximity is a structural proxy—not observed artificial light at night.",
        ha="center", fontsize=10.5, fontstyle="italic", color="#B34E4E",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF7F7", edgecolor="#E2B1B1"))

fig.savefig(OUT / "road_type_sensitivity_flowchart.png", dpi=600,
            bbox_inches="tight", pad_inches=0.25, facecolor="white")
fig.savefig(OUT / "road_type_sensitivity_flowchart.pdf",
            bbox_inches="tight", pad_inches=0.25, facecolor="white")
plt.close(fig)
