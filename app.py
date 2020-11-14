from contextlib import suppress

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State

from netflimap.helpers import (SLIDERS, display_by_visibility,
                               get_dd_country_options,
                               get_df_country_counts_and_titles,
                               get_df_nf_filtered, get_nf_count_map,
                               get_participating_country_codes)

df_netflix = pd.read_csv("data/netflix_dataset.csv")
df_country_counts_and_titles = get_df_country_counts_and_titles(df_netflix)
df_filtered_country_counts_and_titles = df_country_counts_and_titles

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1(
            "🎥 Netflimap - browse Netflix titles with a map 🎥",
            style={"textAlign": "center"},
        ),
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
    ],
    State("countries-dd", "value"),
)
def update_selected_countries(click_data, _, __, value):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]
    if "select-all-countries" in changed_id:
        return get_participating_country_codes(df_filtered_country_counts_and_titles)
    elif "clear-countries" in changed_id:
        return []
    elif "nf-map.clickData" in changed_id:
        participating_country_codes = get_participating_country_codes(
            df_filtered_country_counts_and_titles
        )
        with suppress(TypeError, IndexError):
            location = click_data["points"][0]["location"]
            if location not in participating_country_codes:
                return value
            if not value:
                value = [location]
            elif location in value:
                value.remove(location)
            else:
                value.append(location)
            return value


@app.callback(
    Output("nf-map", "figure"),
    [
        Input("apply-filters", "n_clicks"),
        Input("movie-len-slider", "value"),
        Input("movies-switch", "on"),
        Input("n-seasons-slider", "value"),
        Input("tv-shows-switch", "on"),
        Input("free-text-search", "value"),
    ],
    State("nf-map", "figure"),
)
def update_nf_map(_, movie_len, movies_on, n_seasons, tv_shows_on, free_text, figure):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]
    if "apply-filters" in changed_id:
        global df_filtered_country_counts_and_titles
        df_filtered = get_df_nf_filtered(
            df_netflix,
            movie_len if movies_on else None,
            n_seasons if tv_shows_on else None,
        )
        df_filtered_country_counts_and_titles = get_df_country_counts_and_titles(
            df_filtered
        )
        return get_nf_count_map(df_filtered_country_counts_and_titles)
    else:
        return figure


if __name__ == "__main__":
    app.run_server(debug=True)
