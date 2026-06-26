import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

# Load data
path = "/Users/andrewthompson/desktop/Tp_2/MovieFranchises.csv"
df = pd.read_csv(path)

# Convert needed columns to numbers
for col in ["Year", "Lifetime Gross", "FranchiseID"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Keep only movie-level rows
movies = df[
    df["Year"].notna() &
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

# Colors that match dark slide theme
bg = "#222222"       # dark background
fg = "#F3EDE4"       # light text
grid = "#555555"     # soft gridlines

colors = {
    "MCU": "#F2C94C",             # gold
    "Star Wars": "#4DCBE1",       # blue
    "Wizarding World": "#B392F0", # purple
    "Middle Earth": "#6FCF97",    # green
    "Jurassic Park": "#FF7F6E"    # coral
}

# Create figure
fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
fig.patch.set_facecolor(bg)
ax.set_facecolor(bg)

# Plot each franchise
plot_order = ["MCU", "Star Wars", "Wizarding World", "Middle Earth", "Jurassic Park"]

for franchise in plot_order:
    subset = movies[movies["Franchise"] == franchise]

    ax.scatter(
        subset["Year"],
        subset["Lifetime Gross ($M)"],
        s=85,
        alpha=0.9,
        label=franchise,
        color=colors[franchise],
        edgecolors=fg,
        linewidths=0.5
    )

# Add label for highest-grossing movie
peak = movies.loc[movies["Lifetime Gross ($M)"].idxmax()]

ax.annotate(
    peak["Title"],
    (peak["Year"], peak["Lifetime Gross ($M)"]),
    xytext=(10, 10),
    textcoords="offset points",
    color=fg,
    fontsize=10,
    bbox=dict(
        boxstyle="round,pad=0.25",
        fc="#333333",
        ec=fg,
        alpha=0.9
    )
)

# Titles and labels
ax.set_title(
    "Lifetime Gross by Release Year",
    color=fg,
    fontsize=20,
    pad=16,
    fontweight="bold"
)

ax.set_xlabel(
    "Release Year",
    color=fg,
    fontsize=14,
    labelpad=10,
    fontweight="bold"
)

ax.set_ylabel(
    "Lifetime Gross ($M)",
    color=fg,
    fontsize=14,
    labelpad=10,
    fontweight="bold"
)

# Axis settings
ax.set_xlim(1976, 2023)
ax.set_ylim(0, 3000)

ax.xaxis.set_major_locator(MultipleLocator(5))
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))

ax.tick_params(axis="x", colors=fg, labelsize=11)
ax.tick_params(axis="y", colors=fg, labelsize=11)

# Style border and grid
for spine in ax.spines.values():
    spine.set_color(fg)
    spine.set_alpha(0.6)

ax.grid(True, color=grid, alpha=0.35, linewidth=0.8)
ax.set_axisbelow(True)

# Legend
legend = ax.legend(
    title="Franchise",
    facecolor=bg,
    edgecolor=fg,
    framealpha=0.9,
    fontsize=11,
    title_fontsize=12,
    loc="upper left",
    bbox_to_anchor=(1.01, 1)
)

plt.setp(legend.get_texts(), color=fg)
plt.setp(legend.get_title(), color=fg, fontweight="bold")

plt.tight_layout()

# Save to desktop
plt.savefig(
    "/Users/andrewthompson/desktop/franchise_gross_over_time_dark.png",
    facecolor=fig.get_facecolor(),
    bbox_inches="tight"
)

plt.show()