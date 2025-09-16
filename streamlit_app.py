# NBA Analytics Dashboard
# Streamlit app that connects to Athena and displays NBA info

import streamlit as st
import pandas as pd
from ui_components import (
    setup_page_config,
    render_dashboard_header,
    setup_sidebar_controls,
    display_standings_table,
    display_player_stats_summary,
    display_player_stats_table,
    render_footer,
    render_sidebar_info,
    apply_team_colors_css,
)
from data_queries import (
    get_team_standings,
    get_team_performance_over_time,
    get_home_vs_away_stats,
    get_player_stats,
    calculate_rolling_averages,
)
from visualizations import (
    create_cumulative_wins_chart,
    create_player_performance_trend_chart,
)

setup_page_config()

render_dashboard_header()

selected_seasons, game_type, player_name, rolling_window = setup_sidebar_controls()

# Main dashboard
try:
    # Load data
    with st.spinner("Loading NBA data from Athena..."):
        standings_df = get_team_standings(selected_seasons, game_type)
        home_away_df = get_home_vs_away_stats(selected_seasons, game_type)

    if standings_df.empty:
        st.error("No data found")
        st.stop()

    st.markdown("---")

    # Team Standings
    display_standings_table(standings_df, selected_seasons)

    st.markdown("---")

    st.header("Team Performance Analysis")

    # Team selector
    selected_teams = st.multiselect(
        "Select teams to compare:",
        options=sorted(standings_df["team_name"].tolist()),
        default=standings_df.head(3)["team_name"].tolist(),
        max_selections=5,
    )

    # Apply team colors
    apply_team_colors_css(selected_teams)

    if selected_teams:
        performance_df = get_team_performance_over_time(
            selected_teams, selected_seasons, game_type
        )

        if not performance_df.empty:
            fig = create_cumulative_wins_chart(performance_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Player Stats Analysis
    if player_name:
        st.header(f"Player Analysis: {player_name}")

        with st.spinner(f"Loading stats for {player_name}..."):
            player_stats_df = get_player_stats(player_name, selected_seasons, game_type)

        if not player_stats_df.empty:
            display_player_stats_summary(player_stats_df)

            display_player_stats_table(player_stats_df)

            # Rolling Average Analysis
            if len(player_stats_df) >= rolling_window:
                st.subheader(f"Rolling {rolling_window}-Game Averages")

                rolling_df = calculate_rolling_averages(player_stats_df, rolling_window)

                if not rolling_df.empty:
                    # Display current rolling averages (most recent window)
                    latest_rolling = rolling_df.iloc[-1]

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            f"Rolling Avg Points ({rolling_window} games)",
                            f"{latest_rolling['points']:.1f}",
                        )
                    with col2:
                        st.metric(
                            f"Rolling Avg Rebounds ({rolling_window} games)",
                            f"{latest_rolling['rebounds']:.1f}",
                        )
                    with col3:
                        st.metric(
                            f"Rolling Avg Assists ({rolling_window} games)",
                            f"{latest_rolling['assists']:.1f}",
                        )
                    with col4:
                        st.metric(
                            f"Rolling FG% ({rolling_window} games)",
                            f"{latest_rolling['rolling_fg_pct']:.1f}%",
                        )

                    # Rolling averages table (last 10 windows or all if less)
                    st.subheader(f"Recent {rolling_window}-Game Rolling Averages")
                    display_rolling = rolling_df.tail(10).copy()

                    rolling_display_columns = [
                        "game_date",
                        "points",
                        "rebounds",
                        "assists",
                        "steals",
                        "blocks",
                        "rolling_fg_pct",
                        "rolling_3pt_pct",
                        "rolling_ft_pct",
                        "turnovers",
                    ]

                    st.dataframe(
                        display_rolling[rolling_display_columns].sort_values(
                            "game_date", ascending=False
                        ),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "game_date": st.column_config.DateColumn("Through Date"),
                            "points": st.column_config.NumberColumn(
                                "Avg PTS", format="%.1f"
                            ),
                            "rebounds": st.column_config.NumberColumn(
                                "Avg REB", format="%.1f"
                            ),
                            "assists": st.column_config.NumberColumn(
                                "Avg AST", format="%.1f"
                            ),
                            "steals": st.column_config.NumberColumn(
                                "Avg STL", format="%.1f"
                            ),
                            "blocks": st.column_config.NumberColumn(
                                "Avg BLK", format="%.1f"
                            ),
                            "rolling_fg_pct": st.column_config.NumberColumn(
                                "Avg FG%", format="%.1f%%"
                            ),
                            "rolling_3pt_pct": st.column_config.NumberColumn(
                                "Avg 3P%", format="%.1f%%"
                            ),
                            "rolling_ft_pct": st.column_config.NumberColumn(
                                "Avg FT%", format="%.1f%%"
                            ),
                            "turnovers": st.column_config.NumberColumn(
                                "Avg TO", format="%.1f"
                            ),
                        },
                    )

            # Performance trends chart
            if len(player_stats_df) > 1:
                st.subheader("Performance Trends")

                stat_options = {
                    "Points": "points",
                    "Rebounds": "rebounds",
                    "Assists": "assists",
                    "Steals": "steals",
                    "Blocks": "blocks",
                    "Field Goal %": "fg_percentage",
                    "3-Point %": "three_pt_percentage",
                    "Free Throw %": "ft_percentage",
                    "Turnovers": "turnovers",
                    "Plus/Minus": "plus_minus",
                }

                selected_stat_label = st.selectbox(
                    "Select stat to visualize:",
                    options=list(stat_options.keys()),
                    index=0,
                    help="Choose which statistic to display in the trend chart",
                )
                selected_stat = stat_options[selected_stat_label]

                fig = create_player_performance_trend_chart(
                    player_stats_df,
                    player_name,
                    selected_stat_label,
                    selected_stat,
                    rolling_window,
                )
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning(f"No stats found for '{player_name}' in the selected season(s).")

    render_footer(selected_seasons, game_type)

except Exception as e:
    st.error(f"Dashboard error: {str(e)}")

render_sidebar_info(selected_seasons, game_type)
