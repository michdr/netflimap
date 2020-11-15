import iso3166
import pandas as pd
from plotly import graph_objects as go
from rapidfuzz import process


def _slider_marks(start, stop, step, text):
    return {
        i: {"label": f"{i} {text if i else ''}"}
        for i in range(start, stop + step, step)
    }


SLIDERS = {
    "movie-len-slider": dict(
        id="movie-len-slider",
        min=0,
        max=300,
        step=1,
        value=[0, 120],
        marks=_slider_marks(0, 300, 30, "minutes"),
    ),
    "n-seasons-slider": dict(
        id="n-seasons-slider",
        min=1,
        max=25,
        step=1,
        value=[1, 6],
        marks=_slider_marks(1, 25, 3, "seasons"),
    ),
}


def get_df_country_counts_and_titles(df, n_of_tiles=5):
    summary = list()
    for c_alpha3 in iso3166.countries_by_alpha3.keys():
        country = dict()
        country["code"] = c_alpha3
        country["count"] = (
            df["country_code"].str.contains(c_alpha3).value_counts().get(True) or 0
        )
        df.country_code.fillna("", inplace=True)
        country["titles"] = ", ".join(
            df[df["country_code"].str.contains(c_alpha3)]["title"].tolist()[:n_of_tiles]
        )
        if country["count"] > n_of_tiles:
            country["titles"] += ", ..."
        summary.append(country)

    return pd.DataFrame(summary)


def get_nf_count_map(df):
    fig = go.Figure(
        data=go.Choropleth(
            locations=df["code"],
            z=df["count"],
            text=df["titles"],
            colorscale="sunset",
            autocolorscale=True,
            reversescale=True,
            marker_line_color="black",
            marker_line_width=1.0,
            colorbar_title="# of<br>Titles",
        )
    )

    fig.update_layout(
        title_text=f"Netflix: Showing {df['count'].sum()} Titles by country of production",
        geo=dict(
            showframe=True, showcoastlines=True, projection_type="equirectangular"
        ),
        autosize=True,
    )
    return fig


def display_by_visibility(visibility_state):
    return {"display": "block"} if visibility_state else {"display": "none"}


def get_participating_country_codes(df):
    return df[df["count"] > 0]["code"].tolist()


def get_dd_country_options(df):
    country_codes = get_participating_country_codes(df)
    return [
        {"label": iso3166.countries_by_alpha3.get(cc).name, "value": cc}
        for cc in country_codes
    ]


def get_df_nf_filtered(df, movie_len, n_seasons):
    # This part is a little hacky
    query_parts = [
        f"(type == 'Movie' and movie_len >= {movie_len[0]} and movie_len <= {movie_len[1]})"
        if movie_len
        else None,
        f"(type == 'TV Show' and n_seasons >= {n_seasons[0]} and n_seasons <= {n_seasons[1]})"
        if n_seasons
        else None,
    ]
    query = " or ".join([q for q in query_parts if q])
    query = query or "(type != 'Movie' and type != 'TV Show')"
    df_filtered = df.query(query)
    return df_filtered.reset_index()


def filter_text_in_nf_df(df, text, top_results=40):
    if not text:
        return df
    choices = [
        "\n".join(
            [str(r["title"]), str(r["description"]), str(r["director"]), str(r["cast"])]
        )
        for _, r in df.iterrows()
    ]
    results = process.extract(text, choices, limit=len(df))
    results.sort(key=lambda x: (-x[1]))
    result_strs = [r[0] for r in results[:top_results]]
    result_titles = [rs.split("\n")[0] for rs in result_strs]
    df_result = df.query("title == @result_titles")
    return df_result
