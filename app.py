from contextlib import suppress

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import dash_table
import pandas as pd
from dash.dependencies import Input, Output, State

from netflimap.helpers import (SLIDERS, display_by_visibility,
                               get_dd_country_options,
                               get_df_country_counts_and_titles,
                               get_df_nf_filtered, get_nf_count_map,
                               get_participating_country_codes)

df_netflix = pd.read_csv("data/netflix_dataset.csv")
df_country_counts_and_titles = get_df_country_counts_and_titles(df_netflix)
NF_DATATABLE_COLUMNS = [
    "show_id",
    "type",
    "title",
    "release_year",
    "duration",
    "country_code",
]

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1(
            "🎥 Netflimap - browse Netflix titles with a map 🎥",
            style={"textAlign": "center"},
        ),
        html.Div(id="df-filtered", style={"display": "none"}),
        html.Hr(),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            id="nf-map",
                            figure=get_nf_count_map(df_country_counts_and_titles),
                        ),
                        daq.BooleanSwitch(id="movies-switch", label="Movies", on=True),
                        html.Div(
                            [dcc.RangeSlider(**SLIDERS["movie-len-slider"])],
                            id="div-movie-len-slider",
                            style={"display": "block"},
                        ),
                        daq.BooleanSwitch(
                            id="tv-shows-switch", label="TV Shows", on=True
                        ),
                        html.Div(
                            [dcc.RangeSlider(**SLIDERS["n-seasons-slider"])],
                            id="div-n-seasons-slider",
                            style={"display": "block"},
                        ),
                        html.Br(),
                        html.Div(
                            dcc.Input(
                                id="free-text-search",
                                type="text",
                                placeholder="Free text search...",
                                style={"width": "100%"},
                            ),
                        ),
                        html.Br(),
                        html.Div(
                            html.Button("Apply", id="apply-filters"),
                            style={"textAlign": "center"},
                        ),
                    ],
                    className="six columns",
                ),
                html.Div(
                    [
                        html.Label(
                            "Countries of production", style={"textAlign": "center"}
                        ),
                        dcc.Dropdown(
                            id="countries-dd",
                            options=get_dd_country_options(
                                df_country_counts_and_titles
                            ),
                            value=[],
                            multi=True,
                        ),
                        html.Br(),
                        html.Div(
                            [
                                html.Button(
                                    "Select all participating countries",
                                    id="select-all-countries",
                                ),
                                html.Button(
                                    "Clear countries selection", id="clear-countries"
                                ),
                            ],
                            style={"textAlign": "center"},
                        ),
                        html.Br(),
                        html.Div(
                            html.Button(
                                "Show filtered titles table", id="update-table"
                            ),
                            style={"textAlign": "center"},
                        ),
                        html.Br(),
                        html.Div(
                            dash_table.DataTable(
                                id="table",
                                columns=[
                                    {"name": i, "id": i}
                                    for i in df_netflix[NF_DATATABLE_COLUMNS].columns
                                ],
                                style_data={
                                    "whiteSpace": "normal",
                                    "height": "auto",
                                },
                                data=df_netflix.to_dict("records"),
                                tooltip_data=[
                                    {
                                        "type": {
                                            "value": row["listed_in"],
                                            "type": "markdown",
                                        },
                                        "title": {
                                            "value": f"**Description**: {row['description']}\n\n"
                                            f"**Cast**: {row['cast']}\n\n"
                                            f"**Director**: {row['director']}\n\n",
                                            "type": "markdown",
                                        },
                                        "country_code": {
                                            "value": row["country"]
                                            if isinstance(row["country"], str)
                                            else "",
                                            "type": "markdown",
                                        },
                                    }
                                    for row in df_netflix.to_dict("rows")
                                ],
                                row_selectable="single",
                                sort_action="native",
                                page_action="native",
                                filter_action="native",
                                page_current=0,
                                page_size=10,
                            )
                        ),
                    ],
                    className="six columns",
                ),
            ],
            className="row",
        ),
    ],
)


@app.callback(
    Output("div-movie-len-slider", "style"),
    [Input("movies-switch", "on")],
)
def show_hide_movie_len(visibility_state):
    return display_by_visibility(visibility_state)


@app.callback(
    Output("div-n-seasons-slider", "style"),
    [Input("tv-shows-switch", "on")],
)
def show_hide_n_seasons(visibility_state):
    return display_by_visibility(visibility_state)


@app.callback(
    Output("countries-dd", "value"),
    [
        Input("nf-map", "clickData"),
        Input("select-all-countries", "n_clicks"),
        Input("clear-countries", "n_clicks"),
        Input("df-filtered", "children"),
    ],
    State("countries-dd", "value"),
)
def update_selected_countries(click_data, _, __, json_filtered, value):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]
    if "select-all-countries" in changed_id:
        df_filtered_netflix = (
            pd.read_json(json_filtered) if json_filtered else df_netflix
        )
        df_filtered_country_counts_and_titles = get_df_country_counts_and_titles(
            df_filtered_netflix
        )
        return get_participating_country_codes(df_filtered_country_counts_and_titles)
    elif "clear-countries" in changed_id:
        return []
    elif "nf-map.clickData" in changed_id:
        # reading json_filtered is too slow
        # participating_country_codes = get_participating_country_codes(
        #     df_filtered_country_counts_and_titles
        # )
        with suppress(TypeError, IndexError):
            location = click_data["points"][0]["location"]
            # if location not in participating_country_codes:
            #     return value
            if not value:
                value = [location]
            elif location in value:
                value.remove(location)
            else:
                value.append(location)
            return value


@app.callback(
    [Output("nf-map", "figure"), Output("df-filtered", "children")],
    [
        Input("apply-filters", "n_clicks"),
    ],
    [
        State("movie-len-slider", "value"),
        State("movies-switch", "on"),
        State("n-seasons-slider", "value"),
        State("tv-shows-switch", "on"),
        State("free-text-search", "value"),
        State("nf-map", "figure"),
    ],
)
def update_nf_map(
    n_clicks, movie_len, movies_on, n_seasons, tv_shows_on, free_text, figure
):
    if n_clicks:
        df_filtered_netflix = get_df_nf_filtered(
            df_netflix,
            movie_len if movies_on else None,
            n_seasons if tv_shows_on else None,
        )
        df_filtered_country_counts_and_titles = get_df_country_counts_and_titles(
            df_filtered_netflix
        )
        return (
            get_nf_count_map(df_filtered_country_counts_and_titles),
            df_filtered_netflix.to_json(),
        )
    else:
        return figure, df_netflix.to_json()


if __name__ == "__main__":
    app.run_server(debug=True)
