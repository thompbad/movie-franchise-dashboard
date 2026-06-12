import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


# --------------------------------------------------
# Page setup
# --------------------------------------------------
st.set_page_config(
    page_title="Movie Franchise Dashboard",
    page_icon="🎬",
    layout="wide"
)

alt.data_transformers.disable_max_rows()


# --------------------------------------------------
# Color and label setup
# --------------------------------------------------
FRANCHISE_MAP = {
    101: "Star Wars",
    102: "Jurassic Park",
    103: "Wizarding World",
    104: "Middle Earth",
    105: "MCU"
}

FRANCHISE_COLORS = {
    "MCU": "#F2C94C",
    "Star Wars": "#4DCBE1",
    "Wizarding World": "#B392F0",
    "Middle Earth": "#6FCF97",
    "Jurassic Park": "#FF7F6E"
}

GENRE_COLORS = {
    "Action": "#F2C94C",
    "Adventure": "#F2994A",
    "Sci-Fi": "#4DCBE1",
    "Fantasy": "#B392F0",
    "Drama": "#6FCF97",
    "Comedy": "#FF7F6E"
}


# --------------------------------------------------
# Data loading and cleaning
# --------------------------------------------------
@st.cache_data
def load_raw_data(uploaded_file=None):
    """Load the CSV from the sidebar upload or from the app folder."""
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)

    possible_paths = [
        "MovieFranchises.csv",
        "MovieFranchises(1).csv",
        "data/MovieFranchises.csv"
    ]

    for path in possible_paths:
        if Path(path).exists():
            return pd.read_csv(path)

    return None


@st.cache_data
def clean_movie_data(df):
    """Clean movie-level rows and create clearer dashboard fields."""
    movies = df.copy()

    numeric_columns = [
        "MovieID",
        "Year",
        "Lifetime Gross",
        "Budget",
        "VoteAvg",
        "VoteCount",
        "Runtime",
        "FranchiseID"
    ]

    for col in numeric_columns:
        if col in movies.columns:
            movies[col] = pd.to_numeric(movies[col], errors="coerce")

    # Keep only the real movie rows. The CSV also contains genre/franchise lookup rows later on.
    movies = movies[
        movies["MovieID"].notna()
        & movies["FranchiseID"].notna()
        & movies["Lifetime Gross"].notna()
    ].copy()

    movies["MovieID"] = movies["MovieID"].astype(int)
    movies["FranchiseID"] = movies["FranchiseID"].astype(int)
    movies["Franchise"] = movies["FranchiseID"].map(FRANCHISE_MAP)
    movies = movies[movies["Franchise"].notna()].copy()

    # Dashboard-friendly fields
    movies["Budget ($M)"] = movies["Budget"] / 1_000_000
    movies["Lifetime Gross ($M)"] = movies["Lifetime Gross"] / 1_000_000
    movies["ROI"] = movies["Lifetime Gross"] / movies["Budget"]
    movies["Audience Rating"] = movies["VoteAvg"]
    movies["ReleaseDate"] = pd.to_datetime(movies["ReleaseDate"], errors="coerce")

    return movies


@st.cache_data
def clean_genre_data(df, movies):
    """Extract the genre lookup section from the CSV and connect it back to movie rows."""
    try:
        genre_start = df.index[df["MovieID"].astype(str).eq("MovieGenreID")][0] + 1
        genre_end = df.index[df["MovieID"].astype(str).eq("FranchiseId")][0]

        # In the genre section, the original column names do not match the values.
        # Title column = MovieID, Lifetime Gross column = Genre.
        genres = df.loc[genre_start:genre_end - 1, ["Title", "Lifetime Gross"]].copy()
        genres.columns = ["MovieID", "Genre"]

        genres["MovieID"] = pd.to_numeric(genres["MovieID"], errors="coerce")
        genres = genres[genres["MovieID"].notna() & genres["Genre"].notna()].copy()
        genres["MovieID"] = genres["MovieID"].astype(int)

        movie_lookup = movies[["MovieID", "Title", "Franchise"]].drop_duplicates()
        movie_genres = genres.merge(movie_lookup, on="MovieID", how="inner")
        return movie_genres

    except Exception:
        return pd.DataFrame(columns=["MovieID", "Genre", "Title", "Franchise"])


# --------------------------------------------------
# Load data
# --------------------------------------------------
uploaded_file = st.sidebar.file_uploader("Upload MovieFranchises.csv", type=["csv"])
raw_df = load_raw_data(uploaded_file)

if raw_df is None:
    st.title("Movie Franchise Dashboard")
    st.warning(
        "Upload MovieFranchises.csv in the sidebar, or place it in the same folder as streamlit_app.py."
    )
    st.stop()

movies = clean_movie_data(raw_df)
movie_genres = clean_genre_data(raw_df, movies)


# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------
st.sidebar.title("Dashboard Controls")

all_franchises = sorted(movies["Franchise"].dropna().unique())
selected_franchises = st.sidebar.multiselect(
    "Choose franchises",
    options=all_franchises,
    default=all_franchises
)

min_year = int(movies["Year"].min())
max_year = int(movies["Year"].max())

year_range = st.sidebar.slider(
    "Release year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1
)

metric_choice = st.sidebar.selectbox(
    "Main comparison metric",
    ["Lifetime Gross ($M)", "Budget ($M)", "ROI", "Audience Rating"],
    index=0
)

show_genres = st.sidebar.checkbox("Show genre section", value=True)
show_table = st.sidebar.checkbox("Show filtered data table", value=True)

filtered = movies[
    movies["Franchise"].isin(selected_franchises)
    & movies["Year"].between(year_range[0], year_range[1])
].copy()

if filtered.empty:
    st.warning("No movies match the current filters. Try widening the year range or selecting more franchises.")
    st.stop()


# --------------------------------------------------
# Header and KPIs
# --------------------------------------------------
st.title("Movie Franchise Performance Dashboard")
st.caption(
    "Use the sidebar filters, then click a franchise bar in the first chart to update the connected visualizations."
)

total_gross = filtered["Lifetime Gross ($M)"].sum()
avg_roi = filtered.loc[filtered["Budget ($M)"] > 0, "ROI"].mean()
avg_rating = filtered["Audience Rating"].mean()
movie_count = len(filtered)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Movies Shown", f"{movie_count}")
kpi2.metric("Total Lifetime Gross", f"${total_gross:,.0f}M")
kpi3.metric("Average ROI", f"{avg_roi:.1f}x")
kpi4.metric("Average Audience Rating", f"{avg_rating:.2f}")


# --------------------------------------------------
# Franchise summary chart with click interaction
# --------------------------------------------------
franchise_summary = (
    filtered.groupby("Franchise", as_index=False)
    .agg(
        **{
            "Lifetime Gross ($M)": ("Lifetime Gross ($M)", "sum"),
            "Budget ($M)": ("Budget ($M)", "sum"),
            "ROI": ("ROI", "mean"),
            "Audience Rating": ("Audience Rating", "mean"),
            "Movies": ("Title", "count")
        }
    )
)

click_franchise = alt.selection_point(
    fields=["Franchise"],
    empty=True,
    name="ClickFranchise"
)

franchise_bar = (
    alt.Chart(franchise_summary)
    .mark_bar(cornerRadiusEnd=5)
    .encode(
        y=alt.Y("Franchise:N", sort="-x", title=None),
        x=alt.X(f"{metric_choice}:Q", title=metric_choice),
        color=alt.Color(
            "Franchise:N",
            scale=alt.Scale(
                domain=list(FRANCHISE_COLORS.keys()),
                range=list(FRANCHISE_COLORS.values())
            ),
            legend=None
        ),
        opacity=alt.condition(click_franchise, alt.value(1), alt.value(0.35)),
        tooltip=[
            alt.Tooltip("Franchise:N", title="Franchise"),
            alt.Tooltip("Movies:Q", title="Movies", format=","),
            alt.Tooltip("Lifetime Gross ($M):Q", title="Total gross ($M)", format=",.0f"),
            alt.Tooltip("Budget ($M):Q", title="Total budget ($M)", format=",.0f"),
            alt.Tooltip("ROI:Q", title="Average ROI", format=".2f"),
            alt.Tooltip("Audience Rating:Q", title="Average audience rating", format=".2f"),
        ],
    )
    .add_params(click_franchise)
    .properties(
        title=f"{metric_choice} by Franchise",
        height=330
    )
)


# --------------------------------------------------
# Coordinated movie-level charts
# --------------------------------------------------
budget_scatter = (
    alt.Chart(filtered)
    .mark_circle(size=85, opacity=0.8)
    .encode(
        x=alt.X("Budget ($M):Q", title="Budget ($M)"),
        y=alt.Y("Lifetime Gross ($M):Q", title="Lifetime Gross ($M)"),
        color=alt.Color(
            "Franchise:N",
            scale=alt.Scale(
                domain=list(FRANCHISE_COLORS.keys()),
                range=list(FRANCHISE_COLORS.values())
            ),
            legend=alt.Legend(title="Franchise")
        ),
        tooltip=[
            alt.Tooltip("Title:N", title="Movie"),
            alt.Tooltip("Franchise:N", title="Franchise"),
            alt.Tooltip("Year:Q", title="Year", format=".0f"),
            alt.Tooltip("Budget ($M):Q", title="Budget ($M)", format=",.0f"),
            alt.Tooltip("Lifetime Gross ($M):Q", title="Lifetime gross ($M)", format=",.0f"),
            alt.Tooltip("ROI:Q", title="ROI", format=".2f"),
            alt.Tooltip("Audience Rating:Q", title="Audience rating", format=".2f"),
        ],
    )
    .transform_filter(click_franchise)
    .properties(
        title="Budget vs. Lifetime Gross",
        height=330
    )
)

release_year_chart = (
    alt.Chart(filtered)
    .mark_circle(size=75, opacity=0.85)
    .encode(
        x=alt.X("Year:Q", title="Release Year", scale=alt.Scale(zero=False)),
        y=alt.Y("Lifetime Gross ($M):Q", title="Lifetime Gross ($M)"),
        color=alt.Color(
            "Franchise:N",
            scale=alt.Scale(
                domain=list(FRANCHISE_COLORS.keys()),
                range=list(FRANCHISE_COLORS.values())
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip("Title:N", title="Movie"),
            alt.Tooltip("Franchise:N", title="Franchise"),
            alt.Tooltip("Year:Q", title="Year", format=".0f"),
            alt.Tooltip("Lifetime Gross ($M):Q", title="Lifetime gross ($M)", format=",.0f"),
            alt.Tooltip("Audience Rating:Q", title="Audience rating", format=".2f"),
        ],
    )
    .transform_filter(click_franchise)
    .properties(
        title="Lifetime Gross by Release Year",
        height=280
    )
)

rating_scatter = (
    alt.Chart(filtered)
    .mark_circle(size=75, opacity=0.85)
    .encode(
        x=alt.X("Audience Rating:Q", title="Audience Rating", scale=alt.Scale(zero=False)),
        y=alt.Y("Lifetime Gross ($M):Q", title="Lifetime Gross ($M)"),
        color=alt.Color(
            "Franchise:N",
            scale=alt.Scale(
                domain=list(FRANCHISE_COLORS.keys()),
                range=list(FRANCHISE_COLORS.values())
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip("Title:N", title="Movie"),
            alt.Tooltip("Franchise:N", title="Franchise"),
            alt.Tooltip("Audience Rating:Q", title="Audience rating", format=".2f"),
            alt.Tooltip("Lifetime Gross ($M):Q", title="Lifetime gross ($M)", format=",.0f"),
            alt.Tooltip("ROI:Q", title="ROI", format=".2f"),
        ],
    )
    .transform_filter(click_franchise)
    .properties(
        title="Audience Rating vs. Lifetime Gross",
        height=280
    )
)

roi_chart = (
    alt.Chart(filtered[filtered["Budget ($M)"] > 0])
    .mark_bar(cornerRadiusEnd=5)
    .encode(
        x=alt.X("ROI:Q", title="ROI: Lifetime Gross ÷ Budget"),
        y=alt.Y("Title:N", sort="-x", title=None),
        color=alt.Color(
            "Franchise:N",
            scale=alt.Scale(
                domain=list(FRANCHISE_COLORS.keys()),
                range=list(FRANCHISE_COLORS.values())
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip("Title:N", title="Movie"),
            alt.Tooltip("Franchise:N", title="Franchise"),
            alt.Tooltip("ROI:Q", title="ROI", format=".2f"),
            alt.Tooltip("Budget ($M):Q", title="Budget ($M)", format=",.0f"),
            alt.Tooltip("Lifetime Gross ($M):Q", title="Lifetime gross ($M)", format=",.0f"),
            alt.Tooltip("Audience Rating:Q", title="Audience rating", format=".2f"),
        ],
    )
    .transform_filter(click_franchise)
    .properties(
        title="Movie-Level Return on Budget",
        height=280
    )
)

st.subheader("Connected Franchise View")
st.write("Click a franchise in the bar chart to filter the charts next to and below it.")

top_row = alt.hconcat(franchise_bar, budget_scatter).resolve_scale(color="independent")
bottom_row = alt.hconcat(release_year_chart, rating_scatter).resolve_scale(color="independent")
coordinated_dashboard = alt.vconcat(top_row, bottom_row).configure_view(strokeWidth=0)

st.altair_chart(coordinated_dashboard, use_container_width=True)


# --------------------------------------------------
# ROI section
# --------------------------------------------------
st.subheader("Return on Budget")
st.altair_chart(roi_chart, use_container_width=True)


# --------------------------------------------------
# Genre section
# --------------------------------------------------
if show_genres and not movie_genres.empty:
    st.subheader("Genre Breakdown")

    filtered_genres = movie_genres[movie_genres["Franchise"].isin(selected_franchises)].copy()

    genre_counts = (
        filtered_genres.groupby(["Franchise", "Genre"], as_index=False)
        .size()
        .rename(columns={"size": "Count"})
    )

    genre_counts["Total Tags"] = genre_counts.groupby("Franchise")["Count"].transform("sum")
    genre_counts["Percent"] = (genre_counts["Count"] / genre_counts["Total Tags"]) * 100

    genre_chart = (
        alt.Chart(genre_counts)
        .mark_bar()
        .encode(
            y=alt.Y("Franchise:N", title=None),
            x=alt.X("Percent:Q", stack="normalize", title="Percent of Genre Tags"),
            color=alt.Color(
                "Genre:N",
                scale=alt.Scale(
                    domain=list(GENRE_COLORS.keys()),
                    range=list(GENRE_COLORS.values())
                ),
                legend=alt.Legend(title="Genre")
            ),
            tooltip=[
                alt.Tooltip("Franchise:N", title="Franchise"),
                alt.Tooltip("Genre:N", title="Genre"),
                alt.Tooltip("Count:Q", title="Genre tags"),
                alt.Tooltip("Percent:Q", title="Percent", format=".1f")
            ],
        )
        .properties(height=280, title="Genre Mix by Franchise")
    )

    st.altair_chart(genre_chart, use_container_width=True)


# --------------------------------------------------
# Data table
# --------------------------------------------------
if show_table:
    with st.expander("View filtered movie data"):
        display_cols = [
            "Title",
            "Franchise",
            "Year",
            "Studio",
            "Rating",
            "Runtime",
            "Budget ($M)",
            "Lifetime Gross ($M)",
            "ROI",
            "Audience Rating",
            "VoteCount"
        ]

        table = filtered[display_cols].sort_values("Lifetime Gross ($M)", ascending=False).copy()
        table = table.rename(columns={"VoteCount": "Vote Count"})

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# Design note for assignment explanation
# --------------------------------------------------
st.markdown(
    """
    **Interaction note:** The sidebar controls let users filter the dataset by franchise and release year.
    The franchise bar chart also supports direct clicking: selecting a franchise updates the scatterplot,
    release-year chart, audience-rating chart, and ROI chart. Tooltips are included throughout so users can
    inspect movie-level values without crowding the dashboard with labels.
    """
)