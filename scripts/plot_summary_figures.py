#!/usr/bin/env python
"""Create manuscript summary figures from CSV result tables."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

GROUP_ORDER = ["G1_major", "G2_plus_secondary_tertiary", "G3_all_11"]
GROUP_LABELS = {
    "G1_major": "G1 major\nroads",
    "G2_plus_secondary_tertiary": "G2 + secondary/\ntertiary",
    "G3_all_11": "G3 all 11\nclasses",
}
CONTRIB_LABELS = ["G1 major", "G2−G1 added", "G3−G2 added"]
CONTRIB_COLORS = ["#4472C4", "#70AD47", "#ED7D31"]


def save(fig, stem: str):
    fig.savefig(FIGURES / f"{stem}.png", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_road_class_composition():
    counts = pd.read_csv(TABLES / "road_class_counts.csv").sort_values("share_percent")
    colors = [
        "#ED7D31" if f in {"residential", "unclassified"} else "#8FAADC"
        for f in counts["fclass"]
    ]
    fig, ax = plt.subplots(figsize=(8.4, 5.8))
    bars = ax.barh(counts["fclass"], counts["share_percent"], color=colors, edgecolor="#333333", linewidth=0.5)
    ax.set_xlabel("Share of filtered road segments (%)")
    ax.set_ylabel("")
    ax.set_title("Composition of the 11-class OSM road layer", weight="bold", pad=12)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, counts["share_percent"]):
        ax.text(value + 0.6, bar.get_y() + bar.get_height() / 2, f"{value:.2f}%",
                va="center", fontsize=8.5)
    combined = counts[counts["fclass"].isin(["residential", "unclassified"])]["share_percent"].sum()
    ax.text(0.98, 0.08, f"Residential + unclassified = {combined:.2f}%",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#FFF2CC", edgecolor="#BF9000"))
    ax.set_xlim(0, max(90, counts["share_percent"].max() + 8))
    fig.tight_layout()
    save(fig, "road_class_composition")


def plot_national_stacked_contributions():
    national = pd.read_csv(TABLES / "road_type_sensitivity_national.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.6), sharey=True)
    for ax, rice in zip(axes, ["major", "minor"]):
        sub = national[national["rice_type"] == rice]
        xlabels = []
        stacks = []
        pct_labels = []
        for radius in [1, 2]:
            r = sub[sub["radius_px"] == radius].set_index("group").loc[GROUP_ORDER]
            g1 = float(r.loc["G1_major", "road_proximity_rice_area_acres"])
            g2 = float(r.loc["G2_plus_secondary_tertiary", "road_proximity_rice_area_acres"])
            g3 = float(r.loc["G3_all_11", "road_proximity_rice_area_acres"])
            stacks.append([g1, g2 - g1, g3 - g2])
            xlabels.append("1 px\n(~30 m)" if radius == 1 else "2 px\n(~60 m)")
            pct_labels.append(float(r.loc["G3_all_11", "exposure_proportion"]) * 100)
        stacks = np.asarray(stacks) / 1_000_000
        bottom = np.zeros(len(xlabels))
        x = np.arange(len(xlabels))
        for idx, label in enumerate(CONTRIB_LABELS):
            ax.bar(x, stacks[:, idx], bottom=bottom, label=label, color=CONTRIB_COLORS[idx],
                   edgecolor="white", linewidth=0.8)
            bottom += stacks[:, idx]
        for xi, total, pct in zip(x, bottom, pct_labels):
            ax.text(xi, total + max(bottom) * 0.025, f"{total:.2f}M acres\n({pct:.2f}%)",
                    ha="center", va="bottom", fontsize=9)
        ax.set_title("Major rice" if rice == "major" else "Minor rice", weight="bold")
        ax.set_xticks(x, xlabels)
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Road-proximity rice area (million acres)")
    axes[1].legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    fig.suptitle("National contribution of added road classes", weight="bold", y=1.02)
    fig.text(0.5, -0.02, "Stack height equals G3. Orange shows the added contribution of residential and unclassified roads.",
             ha="center", fontsize=9.5)
    fig.tight_layout()
    save(fig, "national_incremental_contribution")


def plot_regional_g3_heatmap():
    regional = pd.read_csv(TABLES / "road_type_sensitivity_by_region.csv")
    g3 = regional[(regional["group"] == "G3_all_11") & (regional["region_5"] != "National")].copy()
    region_order = ["North", "Northeast", "Central", "East", "South"]
    col_keys = [("major", 1), ("major", 2), ("minor", 1), ("minor", 2)]
    col_labels = ["Major\n1 px", "Major\n2 px", "Minor\n1 px", "Minor\n2 px"]
    mat = []
    for region in region_order:
        row = []
        for rice, radius in col_keys:
            value = g3[(g3["region_5"] == region) & (g3["rice_type"] == rice) & (g3["radius_px"] == radius)]
            row.append(float(value["exposure_proportion"].iloc[0]) * 100)
        mat.append(row)
    mat = np.asarray(mat)
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    im = ax.imshow(mat, cmap="YlOrRd", vmin=0, vmax=max(30, mat.max()))
    ax.set_xticks(np.arange(len(col_labels)), col_labels)
    ax.set_yticks(np.arange(len(region_order)), region_order)
    ax.set_title("Regional G3 all-class rice-road proximity proportion", weight="bold", pad=12)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:.2f}%", ha="center", va="center",
                    fontsize=9, color="black")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Mapped rice within G3 road-proximity mask (%)")
    ax.tick_params(axis="both", length=0)
    fig.text(0.5, -0.02, "G3 includes all 11 mapped road classes; 1 px ≈30 m and 2 px ≈60 m.",
             ha="center", fontsize=9.5)
    fig.tight_layout()
    save(fig, "regional_g3_heatmap")


def main():
    plot_road_class_composition()
    plot_national_stacked_contributions()
    plot_regional_g3_heatmap()
    print(f"Created summary figures in {FIGURES}")


if __name__ == "__main__":
    main()
