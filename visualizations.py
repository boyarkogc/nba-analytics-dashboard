import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_queries import calculate_rolling_averages
from constants import NBA_TEAM_COLORS


def create_cumulative_wins_chart(performance_df):
    if performance_df.empty:
        return None

    # Win/Loss over time (cumulative wins)
    performance_df = performance_df.sort_values(["team_name", "game_date"])
    performance_df["cumulative_wins"] = performance_df.groupby("team_name")[
        "win_numeric"
    ].cumsum()

    # Create color mapping for selected teams
    unique_teams = performance_df["team_name"].unique()
    color_discrete_map = {}

    for team in unique_teams:
        if team in NBA_TEAM_COLORS:
            color_discrete_map[team] = NBA_TEAM_COLORS[team]
        else:
            # Fallback colors if team not in mapping
            color_discrete_map[team] = None

    fig = px.line(
        performance_df,
        x="game_date",
        y="cumulative_wins",
        color="team_name",
        title="Cumulative Wins Over Season",
        labels={"cumulative_wins": "Total Wins", "game_date": "Game Date"},
        color_discrete_map=color_discrete_map,
    )

    # Enhance the chart appearance
    fig.update_traces(line=dict(width=3))
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_player_performance_trend_chart(
    player_stats_df, player_name, selected_stat_label, selected_stat, rolling_window
):
    if len(player_stats_df) < 2:
        return None

    # Create trend chart with rolling average overlay if available
    if len(player_stats_df) >= rolling_window:
        rolling_df = calculate_rolling_averages(player_stats_df, rolling_window)

        fig = go.Figure()

        # Add game-by-game stats
        fig.add_trace(
            go.Scatter(
                x=player_stats_df.sort_values("game_date")["game_date"],
                y=player_stats_df.sort_values("game_date")[selected_stat],
                mode="markers+lines",
                name=f"Game {selected_stat_label}",
                line=dict(color="lightblue", width=1),
                marker=dict(size=4, color="lightblue"),
            )
        )

        # Add rolling average line (use appropriate column for percentages)
        if not rolling_df.empty:
            if selected_stat == "fg_percentage":
                rolling_stat = "rolling_fg_pct"
            elif selected_stat == "three_pt_percentage":
                rolling_stat = "rolling_3pt_pct"
            elif selected_stat == "ft_percentage":
                rolling_stat = "rolling_ft_pct"
            else:
                rolling_stat = selected_stat

            if rolling_stat in rolling_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=rolling_df["game_date"],
                        y=rolling_df[rolling_stat],
                        mode="lines",
                        name=f"{rolling_window}-Game Rolling Avg",
                        line=dict(color="red", width=3),
                    )
                )

        # Format y-axis for percentages
        y_title = selected_stat_label
        if selected_stat_label.endswith("%"):
            y_title += " (%)"

        fig.update_layout(
            title=f"{player_name} - {selected_stat_label} per Game with {rolling_window}-Game Rolling Average",
            xaxis_title="Game Date",
            yaxis_title=y_title,
            hovermode="x unified",
        )
        return fig

    else:
        # Simple line chart for insufficient data for rolling average
        fig = px.line(
            player_stats_df.sort_values("game_date"),
            x="game_date",
            y=selected_stat,
            title=f"{player_name} - {selected_stat_label} per Game",
            labels={selected_stat: selected_stat_label, "game_date": "Game Date"},
        )
        fig.update_layout(showlegend=False)
        return fig
