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
st.markdown(
    """
    <style>
        [data-testid="stMainBlockContainer"] {
            max-width: 100%;
            padding-left: 0.5rem;
            padding-right: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

alt.data_transformers.disable_max_rows()

CHART_TEXT_COLOR = "#E5E7EB"


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

# Franchise labels and point shapes are also shown, so color is not the
# only way users have to distinguish the franchises.
FRANCHISE_COLORS = {
    "MCU": "#D9A400",
    "Star Wars": "#1597B8",
    "Wizarding World": "#7E57C2",
    "Middle Earth": "#2E8B57",
    "Jurassic Park": "#D95F4B"
}



GENRE_COLORS = {
    "Action": "#D9A400",
    "Adventure": "#D97706",
    "Sci-Fi": "#1597B8",
    "Fantasy": "#7E57C2",
    "Drama": "#2E8B57",
    "Comedy": "#D95F4B"
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def franchise_color_scale():
    return alt.Scale(
        domain=list(FRANCHISE_COLORS.keys()),
        range=list(FRANCHISE_COLORS.values())
    )





def safe_name(value, fallback="Not available"):
    return fallback if pd.isna(value) else str(value)


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
    """Clean movie rows and create dashboard-friendly fields."""
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

    # The CSV also contains lookup rows after the real movie rows.
    movies = movies[
        movies["MovieID"].notna()
        & movies["FranchiseID"].notna()
        & movies["Lifetime Gross"].notna()
    ].copy()

    movies["MovieID"] = movies["MovieID"].astype(int)
    movies["FranchiseID"] = movies["FranchiseID"].astype(int)
    movies["Franchise"] = movies["FranchiseID"].map(FRANCHISE_MAP)
    movies = movies[movies["Franchise"].notna()].copy()

    movies["Budget ($M)"] = movies["Budget"] / 1_000_000
    movies["Lifetime Gross ($M)"] = movies["Lifetime Gross"] / 1_000_000

    # Return on Budget = lifetime gross divided by production budget.
    # Invalid and zero budgets are left blank instead of creating infinity.
    movies["Return on Budget"] = (
        movies["Lifetime Gross"]
        .div(movies["Budget"].where(movies["Budget"] > 0))
    )

    movies["Audience Rating"] = movies["VoteAvg"]
    movies["ReleaseDate"] = pd.to_datetime(
        movies["ReleaseDate"],
        errors="coerce"
    )

    return movies


@st.cache_data
def clean_genre_data(df, movies):
    """Extract genre lookup rows and connect them to movie rows."""
    try:
        movie_id_text = df["MovieID"].astype(str)
        genre_start = df.index[movie_id_text.eq("MovieGenreID")][0] + 1
        genre_end = df.index[movie_id_text.eq("FranchiseId")][0]

        # In this lookup section:
        # Title column = MovieID
        # Lifetime Gross column = Genre
        genres = df.loc[
            genre_start:genre_end - 1,
            ["Title", "Lifetime Gross"]
        ].copy()

        genres.columns = ["MovieID", "Genre"]
        genres["MovieID"] = pd.to_numeric(
            genres["MovieID"],
            errors="coerce"
        )

        genres = genres[
            genres["MovieID"].notna()
            & genres["Genre"].notna()
        ].copy()

        genres["MovieID"] = genres["MovieID"].astype(int)

        movie_lookup = movies[
            ["MovieID", "Title", "Franchise", "Year"]
        ].drop_duplicates()

        return genres.merge(
            movie_lookup,
            on="MovieID",
            how="inner"
        )

    except (IndexError, KeyError, TypeError):
        return pd.DataFrame(
            columns=["MovieID", "Genre", "Title", "Franchise", "Year"]
        )


# --------------------------------------------------
# Load data
# --------------------------------------------------
uploaded_file = st.sidebar.file_uploader(
    "Upload MovieFranchises.csv",
    type=["csv"]
)

raw_df = load_raw_data(uploaded_file)

if raw_df is None:
    st.title("Movie Franchise Dashboard")
    st.warning(
        "Upload MovieFranchises.csv in the sidebar, or place it "
        "in the same folder as streamlit_app.py."
    )
    st.stop()

movies = clean_movie_data(raw_df)
movie_genres = clean_genre_data(raw_df, movies)


# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------
st.sidebar.title("Explore the Data")
st.sidebar.caption(
    "Adjust the filters below. Every chart and takeaway updates."
)

all_franchises = sorted(movies["Franchise"].dropna().unique())

selected_franchises = st.sidebar.multiselect(
    "Franchises",
    options=all_franchises,
    default=all_franchises,
    help="Choose one or more franchises to compare."
)

min_year = int(movies["Year"].min())
max_year = int(movies["Year"].max())

year_range = st.sidebar.slider(
    "Release year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
    help="Only movies released during this period will be included."
)

metric_choice = st.sidebar.selectbox(
    "Franchise comparison metric",
    [
        "Lifetime Gross ($M)",
        "Budget ($M)",
        "Return on Budget",
        "Audience Rating"
    ],
    index=0
)

show_genres = st.sidebar.checkbox(
    "Show genre breakdown",
    value=True
)

show_table = st.sidebar.checkbox(
    "Show filtered data table",
    value=False
)

st.sidebar.divider()
st.sidebar.caption(
    f"Active years: **{year_range[0]}–{year_range[1]}**"
)

filtered = movies[
    movies["Franchise"].isin(selected_franchises)
    & movies["Year"].between(year_range[0], year_range[1])
].copy()

if filtered.empty:
    st.warning(
        "No movies match the current filters. Widen the year range "
        "or select more franchises."
    )
    st.stop()


# --------------------------------------------------
# Header and instructions
# --------------------------------------------------
st.title("Movie Franchise Performance Dashboard")
st.write(
    "Compare how major movie franchises perform across revenue, "
    "budget, audience ratings, release years, and return on budget."
)

st.info(
    "**How to explore:** Use the sidebar filters, hover over any chart "
    "for exact values, and click a franchise bar to focus every connected "
    "chart. Double-click the chart background to clear the selection.",
    icon="🧭"
)


# --------------------------------------------------
# KPI summary
# --------------------------------------------------
total_gross = filtered["Lifetime Gross ($M)"].sum()
valid_returns = filtered["Return on Budget"].dropna()
avg_return = valid_returns.mean()
avg_rating = filtered["Audience Rating"].mean()
movie_count = len(filtered)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Movies Shown",
    f"{movie_count}"
)

kpi2.metric(
    "Total Lifetime Gross",
    f"${total_gross:,.0f}M"
)

kpi3.metric(
    "Average Return on Budget",
    f"{avg_return:.1f}x" if pd.notna(avg_return) else "N/A",
    help="Lifetime gross divided by production budget."
)

kpi4.metric(
    "Average Audience Rating",
    f"{avg_rating:.2f} / 5" if pd.notna(avg_rating) else "N/A"
)


# --------------------------------------------------
# Franchise summary and key takeaways
# --------------------------------------------------
franchise_summary = (
    filtered.groupby("Franchise", as_index=False)
    .agg(
        **{
            "Lifetime Gross ($M)": (
                "Lifetime Gross ($M)",
                "sum"
            ),
            "Budget ($M)": (
                "Budget ($M)",
                "sum"
            ),
            "Return on Budget": (
                "Return on Budget",
                "mean"
            ),
            "Audience Rating": (
                "Audience Rating",
                "mean"
            ),
            "Movies": (
                "Title",
                "count"
            )
        }
    )
)

highest_gross_row = franchise_summary.loc[
    franchise_summary["Lifetime Gross ($M)"].idxmax()
]

valid_franchise_returns = franchise_summary.dropna(
    subset=["Return on Budget"]
)

best_return_row = (
    valid_franchise_returns.loc[
        valid_franchise_returns["Return on Budget"].idxmax()
    ]
    if not valid_franchise_returns.empty
    else None
)

valid_franchise_ratings = franchise_summary.dropna(
    subset=["Audience Rating"]
)

best_rating_row = (
    valid_franchise_ratings.loc[
        valid_franchise_ratings["Audience Rating"].idxmax()
    ]
    if not valid_franchise_ratings.empty
    else None
)

st.subheader("Key Takeaways")

takeaway1, takeaway2, takeaway3 = st.columns(3)

with takeaway1:
    st.metric(
        "Highest Total Gross",
        safe_name(highest_gross_row["Franchise"]),
        f"${highest_gross_row['Lifetime Gross ($M)']:,.0f}M"
    )

with takeaway2:
    if best_return_row is not None:
        st.metric(
            "Best Average Return",
            safe_name(best_return_row["Franchise"]),
            f"{best_return_row['Return on Budget']:.2f}x"
        )
    else:
        st.metric("Best Average Return", "N/A")

with takeaway3:
    if best_rating_row is not None:
        st.metric(
            "Highest Audience Rating",
            safe_name(best_rating_row["Franchise"]),
            f"{best_rating_row['Audience Rating']:.2f} / 5"
        )
    else:
        st.metric("Highest Audience Rating", "N/A")


# --------------------------------------------------
# Connected charts
# --------------------------------------------------
click_franchise = alt.selection_point(
    fields=["Franchise"],
    empty=True,
    name="ClickFranchise"
)

metric_title_map = {
    "Lifetime Gross ($M)": "Total Lifetime Gross ($M)",
    "Budget ($M)": "Total Budget ($M)",
    "Return on Budget": "Average Return on Budget",
    "Audience Rating": "Average Audience Rating (out of 5)"
}

metric_format_map = {
    "Lifetime Gross ($M)": ",.0f",
    "Budget ($M)": ",.0f",
    "Return on Budget": ".2f",
    "Audience Rating": ".2f"
}

franchise_bar = (
    alt.Chart(franchise_summary)
    .mark_bar(cornerRadiusEnd=5)
    .encode(
        y=alt.Y(
            "Franchise:N",
            sort="-x",
            title=None,
            axis=alt.Axis(
                labelLimit=125,
                labelPadding=4
            )
        ),
        x=alt.X(
            f"{metric_choice}:Q",
            title=metric_title_map[metric_choice],
            axis=alt.Axis(
                format=metric_format_map[metric_choice]
            )
        ),
        color=alt.Color(
            "Franchise:N",
            scale=franchise_color_scale(),
            legend=None
        ),
        opacity=alt.condition(
            click_franchise,
            alt.value(1),
            alt.value(0.3)
        ),
        tooltip=[
            alt.Tooltip(
                "Franchise:N",
                title="Franchise"
            ),
            alt.Tooltip(
                "Movies:Q",
                title="Movies",
                format=","
            ),
            alt.Tooltip(
                "Lifetime Gross ($M):Q",
                title="Total gross ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Budget ($M):Q",
                title="Total budget ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Return on Budget:Q",
                title="Average return",
                format=".2f"
            ),
            alt.Tooltip(
                "Audience Rating:Q",
                title="Avg. rating (out of 5)",
                format=".2f"
            )
        ]
    )
    .add_params(click_franchise)
    .properties(
        title=f"{metric_title_map[metric_choice]} by Franchise",
        width=530,
        height=390
    )
)

budget_scatter = (
    alt.Chart(filtered)
    .mark_circle(
        size=130,
        filled=True,
        opacity=0.82,
        stroke="white",
        strokeWidth=0.7
    )
    .encode(
        x=alt.X(
            "Budget ($M):Q",
            title="Budget ($M)"
        ),
        y=alt.Y(
            "Lifetime Gross ($M):Q",
            title="Lifetime Gross ($M)"
        ),
        color=alt.Color(
            "Franchise:N",
            scale=franchise_color_scale(),
            legend=alt.Legend( title="Franchise", orient="top", direction="horizontal", columns=5 )
        ),

        tooltip=[
            alt.Tooltip(
                "Title:N",
                title="Movie"
            ),
            alt.Tooltip(
                "Franchise:N",
                title="Franchise"
            ),
            alt.Tooltip(
                "Year:Q",
                title="Year",
                format=".0f"
            ),
            alt.Tooltip(
                "Budget ($M):Q",
                title="Budget ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Lifetime Gross ($M):Q",
                title="Lifetime gross ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Return on Budget:Q",
                title="Return on budget",
                format=".2f"
            ),
            alt.Tooltip(
                "Audience Rating:Q",
                title="Rating (out of 5)",
                format=".2f"
            )
        ]
    )
    .transform_filter(click_franchise)
    .properties(
        title="Budget vs. Lifetime Gross",
        width=530,
        height=390
    )
)

release_year_chart = (
    alt.Chart(filtered)
    .mark_circle(
        size=100,
        filled=True,
        opacity=0.82,
        stroke="white",
        strokeWidth=0.7
    )
    .encode(
        x=alt.X(
            "Year:Q",
            title="Release Year",
            scale=alt.Scale(zero=False)
        ),
        y=alt.Y(
            "Lifetime Gross ($M):Q",
            title="Lifetime Gross ($M)"
        ),
        color=alt.Color(
            "Franchise:N",
            scale=franchise_color_scale(),
            legend=None
        ),

        tooltip=[
            alt.Tooltip(
                "Title:N",
                title="Movie"
            ),
            alt.Tooltip(
                "Franchise:N",
                title="Franchise"
            ),
            alt.Tooltip(
                "Year:Q",
                title="Year",
                format=".0f"
            ),
            alt.Tooltip(
                "Lifetime Gross ($M):Q",
                title="Lifetime gross ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Audience Rating:Q",
                title="Rating (out of 5)",
                format=".2f"
            )
        ]
    )
    .transform_filter(click_franchise)
    .properties(
        title="Lifetime Gross by Release Year",
        width=530,
        height=350
    )
)

rating_scatter = (
    alt.Chart(filtered)
    .mark_circle(
        size=100,
        filled=True,
        opacity=0.82,
        stroke="white",
        strokeWidth=0.7
    )
    .encode(
        x=alt.X(
            "Audience Rating:Q",
            title="Audience Rating (out of 5)",
            scale=alt.Scale(domain=[0, 5])
        ),
        y=alt.Y(
            "Lifetime Gross ($M):Q",
            title="Lifetime Gross ($M)"
        ),
        color=alt.Color(
            "Franchise:N",
            scale=franchise_color_scale(),
            legend=None
        ),

        tooltip=[
            alt.Tooltip(
                "Title:N",
                title="Movie"
            ),
            alt.Tooltip(
                "Franchise:N",
                title="Franchise"
            ),
            alt.Tooltip(
                "Audience Rating:Q",
                title="Rating (out of 5)",
                format=".2f"
            ),
            alt.Tooltip(
                "Lifetime Gross ($M):Q",
                title="Lifetime gross ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Return on Budget:Q",
                title="Return on budget",
                format=".2f"
            )
        ]
    )
    .transform_filter(click_franchise)
    .properties(
        title="Audience Rating vs. Lifetime Gross",
        width=530,
        height=350
    )
)

roi_source = filtered[
    filtered["Return on Budget"].notna()
].copy()

return_chart = (
    alt.Chart(roi_source)
    .transform_filter(click_franchise)
    .transform_window(
        ReturnRank="rank(Return on Budget)",
        sort=[
            alt.SortField(
                "Return on Budget",
                order="descending"
            )
        ]
    )
    .transform_filter("datum.ReturnRank <= 10")
    .mark_bar(cornerRadiusEnd=5)
    .encode(
        x=alt.X(
            "Return on Budget:Q",
            title="Return on Budget (Lifetime Gross ÷ Budget)"
        ),
        y=alt.Y(
            "Title:N",
            sort="-x",
            title=None,
            axis=alt.Axis(labelLimit=280)
        ),
        color=alt.Color(
            "Franchise:N",
            scale=franchise_color_scale(),
            legend=None
        ),
        tooltip=[
            alt.Tooltip(
                "Title:N",
                title="Movie"
            ),
            alt.Tooltip(
                "Franchise:N",
                title="Franchise"
            ),
            alt.Tooltip(
                "Return on Budget:Q",
                title="Return on budget",
                format=".2f"
            ),
            alt.Tooltip(
                "Budget ($M):Q",
                title="Budget ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Lifetime Gross ($M):Q",
                title="Lifetime gross ($M)",
                format=",.0f"
            ),
            alt.Tooltip(
                "Audience Rating:Q",
                title="Rating (out of 5)",
                format=".2f"
            )
        ]
    )
    .properties(
        title="Top 10 Movies by Return on Budget",
        height=340
    )
)

st.subheader("Connected Franchise View")
st.caption(
    "Click one franchise in the first chart to update every chart below."
)

top_row = alt.hconcat(
    franchise_bar,
    budget_scatter,
    spacing=18
).resolve_scale(
    color="independent"
)

middle_row = alt.hconcat(
    release_year_chart,
    rating_scatter,
    spacing=18
).resolve_scale(
    color="independent"
)

coordinated_dashboard = (
    alt.vconcat(
        top_row,
        middle_row,
        return_chart,
        spacing=28,
        center=False
    )
    .configure_view(
        strokeWidth=0
    )
    .configure_axis(
        labelFontSize=15,
        titleFontSize=17,
        labelFontWeight="bold",
        titleFontWeight="bold",
        labelColor=CHART_TEXT_COLOR,
        titleColor=CHART_TEXT_COLOR,
        labelPadding=8,
        titlePadding=12
    )
    .configure_title(
        fontSize=20,
        fontWeight="bold",
        anchor="start",
        color=CHART_TEXT_COLOR,
        offset=12
    )
    .configure_legend(
        labelFontSize=14,
        titleFontSize=15,
        labelFontWeight="bold",
        titleFontWeight="bold",
        labelColor=CHART_TEXT_COLOR,
        titleColor=CHART_TEXT_COLOR,
        symbolSize=120
    )
)

st.altair_chart(
    coordinated_dashboard,
    use_container_width=True,
    theme=None
)


# --------------------------------------------------
# Genre section
# --------------------------------------------------
if show_genres and not movie_genres.empty:
    st.subheader("Genre Breakdown")
    st.caption(
        "The genre view follows both the franchise and release-year filters."
    )

    # Filter genre tags by the exact movies currently visible.
    filtered_movie_ids = filtered["MovieID"].unique()

    filtered_genres = movie_genres[
        movie_genres["MovieID"].isin(filtered_movie_ids)
    ].copy()

    if filtered_genres.empty:
        st.info(
            "No genre tags are available for the current selection."
        )
    else:
        genre_counts = (
            filtered_genres
            .groupby(
                ["Franchise", "Genre"],
                as_index=False
            )
            .size()
            .rename(columns={"size": "Count"})
        )

        genre_counts["Total Tags"] = (
            genre_counts
            .groupby("Franchise")["Count"]
            .transform("sum")
        )

        genre_counts["Percent"] = (
            genre_counts["Count"]
            / genre_counts["Total Tags"]
            * 100
        )

        genre_chart = (
            alt.Chart(genre_counts)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Franchise:N",
                    title=None
                ),
                x=alt.X(
                    "Count:Q",
                    stack="normalize",
                    title="Share of Genre Tags",
                    axis=alt.Axis(format="%")
                ),
                color=alt.Color(
                    "Genre:N",
                    scale=alt.Scale(
                        domain=list(GENRE_COLORS.keys()),
                        range=list(GENRE_COLORS.values())
                    ),
                    legend=alt.Legend(title="Genre")
                ),
                tooltip=[
                    alt.Tooltip(
                        "Franchise:N",
                        title="Franchise"
                    ),
                    alt.Tooltip(
                        "Genre:N",
                        title="Genre"
                    ),
                    alt.Tooltip(
                        "Count:Q",
                        title="Genre tags"
                    ),
                    alt.Tooltip(
                        "Percent:Q",
                        title="Share",
                        format=".1f"
                    )
                ]
            )
            .properties(
                height=290,
                title="Genre Mix by Franchise"
            )
            .configure_view(strokeWidth=0)
            .configure_axis(
                labelFontSize=15,
                titleFontSize=17,
                labelFontWeight="bold",
                titleFontWeight="bold",
                labelColor=CHART_TEXT_COLOR,
                titleColor=CHART_TEXT_COLOR,
                labelPadding=8,
                titlePadding=12
            )
            .configure_title(
                fontSize=20,
                fontWeight="bold",
                anchor="start",
                color=CHART_TEXT_COLOR,
                offset=12
            )
            .configure_legend(
                labelFontSize=14,
                titleFontSize=15,
                labelFontWeight="bold",
                titleFontWeight="bold",
                labelColor=CHART_TEXT_COLOR,
                titleColor=CHART_TEXT_COLOR,
                symbolSize=120
            )
        )

        st.altair_chart(
            genre_chart,
            use_container_width=True
        )


# --------------------------------------------------
# Data table
# --------------------------------------------------
if show_table:
    with st.expander(
        "View filtered movie data",
        expanded=False
    ):
        display_cols = [
            "Title",
            "Franchise",
            "Year",
            "Studio",
            "Rating",
            "Runtime",
            "Budget ($M)",
            "Lifetime Gross ($M)",
            "Return on Budget",
            "Audience Rating",
            "VoteCount"
        ]

        table = (
            filtered[display_cols]
            .sort_values(
                "Lifetime Gross ($M)",
                ascending=False
            )
            .copy()
            .rename(
                columns={
                    "Audience Rating": "Audience Rating (out of 5)",
                    "VoteCount": "Vote Count"
                }
            )
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Budget ($M)": st.column_config.NumberColumn(
                    format="$%.1fM"
                ),
                "Lifetime Gross ($M)": st.column_config.NumberColumn(
                    format="$%.1fM"
                ),
                "Return on Budget": st.column_config.NumberColumn(
                    format="%.2fx"
                ),
                "Audience Rating (out of 5)": st.column_config.NumberColumn(
                    format="%.2f"
                ),
                "Vote Count": st.column_config.NumberColumn(
                    format="%d"
                )
            }
        )


# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption(
    "Return on Budget represents lifetime gross divided by production "
    "budget. Results are based on the franchises, years, and movies "
    "currently selected."
)
