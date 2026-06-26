import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter

# Load data
path = "/Users/andrewthompson/desktop/TP_2/MovieFranchises.csv"
df = pd.read_csv(path)

# --------------------------------------------------
# 1. Find genre section BEFORE converting columns
# --------------------------------------------------
genre_start = df.index[df["MovieID"].astype(str).eq("MovieGenreID")][0] + 1
genre_end = df.index[df["MovieID"].astype(str).eq("FranchiseId")][0]

# In the genre section:
# Title column = MovieID
# Lifetime Gross column = Genre
genres = df.loc[genre_start:genre_end - 1, ["Title", "Lifetime Gross"]].copy()
genres.columns = ["MovieID", "Genre"]

genres["MovieID"] = pd.to_numeric(genres["MovieID"], errors="coerce")
genres = genres[genres["MovieID"].notna() & genres["Genre"].notna()]
genres["MovieID"] = genres["MovieID"].astype(int)

# --------------------------------------------------
# 2. Clean movie-level data
# --------------------------------------------------
df["MovieID_num"] = pd.to_numeric(df["MovieID"], errors="coerce")
df["FranchiseID_num"] = pd.to_numeric(df["FranchiseID"], errors="coerce")

movies = df[
    df["MovieID_num"].notna() &
    df["FranchiseID_num"].notna()
].copy()

movies["MovieID"] = movies["MovieID_num"].astype(int)
movies["FranchiseID"] = movies["FranchiseID_num"].astype(int)

franchise_map = {
    101: "Star Wars",
    102: "Jurassic Park",
    103: "Wizarding World",
    104: "Middle Earth",
    105: "MCU"
}

movies["Franchise"] = movies["FranchiseID"].map(franchise_map)

movies = movies[movies["Franchise"].notna()][["MovieID", "Title", "Franchise"]]

# --------------------------------------------------
# 3. Merge movies with genres
# --------------------------------------------------
movie_genres = genres.merge(movies, on="MovieID", how="inner")

genre_by_franchise = (
    movie_genres
    .groupby(["Franchise", "Genre"])
    .size()
    .reset_index(name="Count")
)

pivot = genre_by_franchise.pivot(
    index="Franchise",
    columns="Genre",
    values="Count"
).fillna(0)

franchise_order = ["MCU", "Star Wars", "Wizarding World", "Middle Earth", "Jurassic Park"]
pivot = pivot.loc[franchise_order]

# Convert counts to percentages within each franchise
pivot_percent = pivot.div(pivot.sum(axis=1), axis=0) * 100

# --------------------------------------------------
# 4. Dark theme colors
# --------------------------------------------------
bg = "#222222"
fg = "#F3EDE4"
grid = "#555555"

genre_colors = {
    "Action": "#F2C94C",
    "Adventure": "#F2994A",
    "Sci-Fi": "#4DCBE1",
    "Fantasy": "#B392F0",
    "Drama": "#6FCF97",
    "Comedy": "#FF7F6E"
}

colors = [genre_colors.get(genre, "#AAAAAA") for genre in pivot_percent.columns]

# --------------------------------------------------
# 5. Create percent stacked bar chart
# --------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7), dpi=200)
fig.patch.set_facecolor(bg)
ax.set_facecolor(bg)

pivot_percent.plot(
    kind="barh",
    stacked=True,
    color=colors,
    edgecolor=bg,
    linewidth=0.8,
    ax=ax
)

# Title and labels
ax.set_title(
    "Genre Mix by Franchise",
    color=fg,
    fontsize=20,
    pad=16,
    fontweight="bold"
)

ax.set_xlabel(
    "Percent of Genre Tags",
    color=fg,
    fontsize=14,
    labelpad=10,
    fontweight="bold"
)

ax.set_ylabel("")

# Axis settings
ax.set_xlim(0, 100)
ax.xaxis.set_major_locator(MultipleLocator(20))
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x)}%"))

ax.tick_params(axis="x", colors=fg, labelsize=11)
ax.tick_params(axis="y", colors=fg, labelsize=12)

# Grid and border
for spine in ax.spines.values():
    spine.set_color(fg)
    spine.set_alpha(0.6)

ax.grid(True, axis="x", color=grid, alpha=0.35, linewidth=0.8)
ax.set_axisbelow(True)

# Legend
legend = ax.legend(
    title="Genre",
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
    "/Users/andrewthompson/desktop/TP_2/genre_mix_by_franchise_percent_dark.png",
    facecolor=fig.get_facecolor(),
    bbox_inches="tight"
)

plt.show()