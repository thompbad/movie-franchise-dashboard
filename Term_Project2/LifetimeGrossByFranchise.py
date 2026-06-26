import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

# Load data
path = "/Users/andrewthompson/desktop/TP_2/MovieFranchises.csv"
df = pd.read_csv(path)

# Convert needed columns to numbers
for col in ["Lifetime Gross", "FranchiseID"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Keep only movie-level rows
movies = df[
    df["Lifetime Gross"].notna() &
    df["FranchiseID"].notna()
].copy()

# Convert gross to millions
movies["Lifetime Gross ($M)"] = movies["Lifetime Gross"] / 1_000_000

# Franchise ID labels
franchise_map = {
    101: "Star Wars",
    102: "Jurassic Park",
    103: "Wizarding World",
    104: "Middle Earth",
    105: "MCU"
}

movies["Franchise"] = movies["FranchiseID"].astype(int).map(franchise_map)

# Total lifetime gross by franchise
gross_by_franchise = (
    movies.groupby("Franchise", as_index=False)["Lifetime Gross ($M)"]
    .sum()
    .sort_values("Lifetime Gross ($M)", ascending=True)
)

# Dark slide theme colors
bg = "#222222"
fg = "#F3EDE4"
grid = "#555555"

colors = {
    "MCU": "#F2C94C",
    "Star Wars": "#4DCBE1",
    "Wizarding World": "#B392F0",
    "Middle Earth": "#6FCF97",
    "Jurassic Park": "#FF7F6E"
}

bar_colors = [colors[f] for f in gross_by_franchise["Franchise"]]

# Create figure
fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
fig.patch.set_facecolor(bg)
ax.set_facecolor(bg)

# Horizontal bar chart
bars = ax.barh(
    gross_by_franchise["Franchise"],
    gross_by_franchise["Lifetime Gross ($M)"],
    color=bar_colors,
    edgecolor=fg,
    linewidth=0.5
)

# Add value labels
for bar in bars:
    width = bar.get_width()
    ax.text(
        width + 300,
        bar.get_y() + bar.get_height() / 2,
        f"${width:,.0f}M",
        va="center",
        color=fg,
        fontsize=12,
        fontweight="bold"
    )

# Title and labels
ax.set_title(
    "Total Lifetime Gross by Franchise",
    color=fg,
    fontsize=20,
    pad=16,
    fontweight="bold"
)

ax.set_xlabel(
    "Total Lifetime Gross ($M)",
    color=fg,
    fontsize=14,
    labelpad=10,
    fontweight="bold"
)

ax.set_ylabel("")

# Axis formatting
ax.xaxis.set_major_locator(MultipleLocator(5000))
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"${int(x):,}M"))

ax.tick_params(axis="x", colors=fg, labelsize=11)
ax.tick_params(axis="y", colors=fg, labelsize=12)

# Grid and border
for spine in ax.spines.values():
    spine.set_color(fg)
    spine.set_alpha(0.6)

ax.grid(True, axis="x", color=grid, alpha=0.35, linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()

# Save to desktop
plt.savefig(
    "/Users/andrewthompson/desktop/TP_2/lifetime_gross_by_franchise_dark.png",
    facecolor=fig.get_facecolor(),
    bbox_inches="tight"
)

plt.show()