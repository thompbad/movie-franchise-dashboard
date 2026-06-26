import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# Load data
path = "/Users/andrewthompson/desktop/TP_2/MovieFranchises.csv"
df = pd.read_csv(path)

# Find the genre section of the CSV
genre_start = df.index[df["MovieID"].astype(str).eq("MovieGenreID")][0] + 1
genre_end = df.index[df["MovieID"].astype(str).eq("FranchiseId")][0]

# In the genre section:
# Title column = MovieID
# Lifetime Gross column = Genre
genres = df.loc[genre_start:genre_end - 1, ["Title", "Lifetime Gross"]].copy()
genres.columns = ["MovieID", "Genre"]

# Clean genre data
genres["MovieID"] = pd.to_numeric(genres["MovieID"], errors="coerce")
genres = genres[genres["MovieID"].notna() & genres["Genre"].notna()]

# Count genre tags
genre_counts = (
    genres["Genre"]
    .value_counts()
    .sort_values(ascending=True)
)

# Dark slide theme colors
bg = "#222222"
fg = "#F3EDE4"
grid = "#555555"

# Use colors that match the rest of your deck
bar_colors = [
    "#B392F0",
    "#6FCF97",
    "#FF7F6E",
    "#4DCBE1",
    "#F2994A",
    "#F2C94C"
]

# If there are more genres than colors, repeat colors
bar_colors = (bar_colors * 10)[:len(genre_counts)]

# Create figure
fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
fig.patch.set_facecolor(bg)
ax.set_facecolor(bg)

# Horizontal bar chart
bars = ax.barh(
    genre_counts.index,
    genre_counts.values,
    color=bar_colors,
    edgecolor=fg,
    linewidth=0.5
)

# Add count labels
for bar in bars:
    width = bar.get_width()
    ax.text(
        width + 0.5,
        bar.get_y() + bar.get_height() / 2,
        int(width),
        va="center",
        color=fg,
        fontsize=12,
        fontweight="bold"
    )

# Titles and labels
ax.set_title(
    "Genre Tags in the Dataset",
    color=fg,
    fontsize=20,
    pad=16,
    fontweight="bold"
)

ax.set_xlabel(
    "Number of Genre Tags",
    color=fg,
    fontsize=14,
    labelpad=10,
    fontweight="bold"
)

ax.set_ylabel("")

# Axis formatting
ax.xaxis.set_major_locator(MultipleLocator(10))

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
    "/Users/andrewthompson/desktop/TP_2/genre_tags_dark.png",
    facecolor=fig.get_facecolor(),
    bbox_inches="tight"
)

plt.show()