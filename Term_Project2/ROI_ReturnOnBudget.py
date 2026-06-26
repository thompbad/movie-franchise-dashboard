import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Load data
path = "/Users/andrewthompson/desktop/TP_2/MovieFranchises.csv"
df = pd.read_csv(path)

# Convert needed columns to numbers
for col in ["Budget", "Lifetime Gross", "FranchiseID"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Keep only movie-level rows with usable budget and gross data
movies = df[
    df["Budget"].notna() &
    df["Lifetime Gross"].notna() &
    df["FranchiseID"].notna() &
    (df["Budget"] > 0)
].copy()

# Franchise ID labels
franchise_map = {
    101: "Star Wars",
    102: "Jurassic Park",
    103: "Wizarding World",
    104: "Middle Earth",
    105: "MCU"
}

movies["Franchise"] = movies["FranchiseID"].astype(int).map(franchise_map)

# Calculate ROI
movies["ROI"] = movies["Lifetime Gross"] / movies["Budget"]

# Average ROI by franchise
roi_by_franchise = (
    movies.groupby("Franchise", as_index=False)["ROI"]
    .mean()
    .sort_values("ROI", ascending=True)
)

# Dark slide theme colors
bg = "#222222"
fg = "#F3EDE4"
grid = "#555555"

colors = {
    "MCU": "#F2C94C",
    "Star Wars": "#4DCBE1",       # your Star Wars color
    "Wizarding World": "#B392F0",
    "Middle Earth": "#6FCF97",
    "Jurassic Park": "#FF7F6E"
}

bar_colors = [colors[f] for f in roi_by_franchise["Franchise"]]

# Create figure
fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
fig.patch.set_facecolor(bg)
ax.set_facecolor(bg)

# Horizontal bar chart
bars = ax.barh(
    roi_by_franchise["Franchise"],
    roi_by_franchise["ROI"],
    color=bar_colors,
    edgecolor=fg,
    linewidth=0.5
)

# Add value labels
for bar in bars:
    width = bar.get_width()
    ax.text(
        width + 0.15,
        bar.get_y() + bar.get_height() / 2,
        f"{width:.1f}x",
        va="center",
        color=fg,
        fontsize=12,
        fontweight="bold"
    )

# Titles and labels
ax.set_title(
    "Average Return on Budget by Franchise",
    color=fg,
    fontsize=20,
    pad=16,
    fontweight="bold"
)

ax.set_xlabel(
    "Average ROI: Lifetime Gross ÷ Budget",
    color=fg,
    fontsize=14,
    labelpad=10,
    fontweight="bold"
)

ax.set_ylabel(
    "",
    color=fg
)

# Format x-axis
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0f}x"))

ax.tick_params(axis="x", colors=fg, labelsize=11)
ax.tick_params(axis="y", colors=fg, labelsize=12)

# Style grid and border
for spine in ax.spines.values():
    spine.set_color(fg)
    spine.set_alpha(0.6)

ax.grid(True, axis="x", color=grid, alpha=0.35, linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()

# Save to desktop
plt.savefig(
    "/Users/andrewthompson/desktop/TP_2/roi_by_franchise_dark.png",
    facecolor=fig.get_facecolor(),
    bbox_inches="tight"
)

plt.show()