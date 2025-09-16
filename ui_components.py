import streamlit as st
from datetime import datetime
from data_queries import get_all_player_names, get_available_seasons
from constants import NBA_TEAM_COLORS, NUGGETS_COLORS


def setup_page_config():
    import os

    # Try to use NBA logo, fallback to basketball emoji
    logo_path = "assets/nba_logo_32x32.png"
    if os.path.exists(logo_path):
        page_icon = logo_path
    else:
        page_icon = "🏀"

    st.set_page_config(
        page_title="NBA Analytics Dashboard",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Nuggets themed CSS
    st.markdown(
        f"""
    <style>
        /* Main theme colors */
        :root {{
            --nuggets-navy: {NUGGETS_COLORS['navy']};
            --nuggets-gold: {NUGGETS_COLORS['gold']};
            --nuggets-red: {NUGGETS_COLORS['red']};
            --nuggets-white: {NUGGETS_COLORS['white']};
            --nuggets-light: {NUGGETS_COLORS['light_gray']};
        }}
        
        /* Main header styling */
        .main-header {{
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
        }}
        
        /* Metric cards */
        .metric-card {{
            background: linear-gradient(135deg, var(--nuggets-light) 0%, var(--nuggets-white) 100%);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid var(--nuggets-gold);
            box-shadow: 0 2px 4px rgba(14, 34, 64, 0.1);
        }}
        
        /* Sidebar styling */
        .sidebar .sidebar-content {{
            background: linear-gradient(180deg, var(--nuggets-navy) 0%, #1a2f4a 100%);
            color: var(--nuggets-white);
        }}
        
        /* Headers and subheaders */
        h1, h2, h3 {{
            color: var(--nuggets-navy) !important;
        }}
        
        /* Multiselect styling */
        .stMultiSelect [data-baseweb="tag"] {{
            transition: all 0.2s ease;
        }}
        
        /* Button styling */
        .stButton > button {{
            background: linear-gradient(90deg, var(--nuggets-gold) 0%, #e6b01a 100%);
            color: var(--nuggets-navy);
            border: none;
            font-weight: bold;
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            background: linear-gradient(90deg, #e6b01a 0%, var(--nuggets-gold) 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(254, 197, 36, 0.3);
        }}
        
        /* Selectbox styling */
        .stSelectbox > div > div {{
            border-color: var(--nuggets-gold);
        }}
        
        /* Radio button styling */
        .stRadio > div {{
            color: var(--nuggets-white);
        }}
        
        /* Sidebar text color */
        .sidebar .sidebar-content .stMarkdown {{
            color: var(--nuggets-white) !important;
        }}
        
        /* Info boxes */
        .stInfo {{
            background-color: rgba(254, 197, 36, 0.1);
            border-left-color: var(--nuggets-gold);
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def apply_team_colors_css(selected_teams):
    """Apply team-specific colors to multiselect tags"""
    if not selected_teams:
        return

    # Simple CSS targeting each team by position
    css_rules = []
    for i, team in enumerate(selected_teams):
        if team in NBA_TEAM_COLORS:
            color = NBA_TEAM_COLORS[team]
            css_rules.append(
                f"""
                .stMultiSelect [data-baseweb="tag"]:nth-child({i+1}) {{
                    background-color: {color} !important;
                    color: white !important;
                    border-color: {color} !important;
                }}
                .stMultiSelect [data-baseweb="tag"]:nth-child({i+1}) svg {{
                    fill: white !important;
                }}
            """
            )

    if css_rules:
        st.markdown(
            f"""
        <style>
        {''.join(css_rules)}
        </style>
        """,
            unsafe_allow_html=True,
        )


def render_dashboard_header():
    st.markdown(
        '<h1 class="main-header">NBA Analytics Dashboard</h1>',
        unsafe_allow_html=True,
    )


def setup_sidebar_controls():
    st.sidebar.header("Dashboard Controls")
    st.sidebar.markdown("---")

    # Season selection logic
    try:
        available_seasons_df = get_available_seasons()
        if not available_seasons_df.empty:
            available_seasons = available_seasons_df["season"].tolist()
            selected_seasons = ["2023-24"]  # Default fallback
        else:
            available_seasons = ["2023-24"]
            selected_seasons = ["2023-24"]  # Fallback
    except Exception as e:
        available_seasons = ["2023-24"]
        selected_seasons = ["2023-24"]  # Fallback

    st.sidebar.subheader("Season Selection")
    try:
        if available_seasons:
            start_season = st.sidebar.selectbox(
                "Start Season:",
                options=available_seasons,
                index=0 if available_seasons else 0,
            )

            # Filter end season options to be >= start season
            start_idx = (
                available_seasons.index(start_season)
                if start_season in available_seasons
                else 0
            )
            end_season_options = available_seasons[start_idx:]

            end_season = st.sidebar.selectbox(
                "End Season:", options=end_season_options, index=0
            )

            # Create list of selected seasons (inclusive range)
            start_idx = available_seasons.index(start_season)
            end_idx = available_seasons.index(end_season)
            selected_seasons = available_seasons[start_idx : end_idx + 1]

        else:
            st.sidebar.error("Could not load available seasons")

    except Exception as e:
        st.sidebar.error(f"Error loading seasons: {str(e)}")

    st.sidebar.subheader("Game Type")
    game_type = st.sidebar.radio(
        "Select game type:",
        options=["Regular Season", "Playoffs"],
        index=0,
        help="Choose between regular season and playoff games",
    )

    st.sidebar.markdown("---")

    # Player search section
    st.sidebar.subheader("Player Analysis")
    player_name = setup_player_selection()

    # Rolling average settings
    rolling_window = st.sidebar.number_input(
        "Rolling average window:",
        min_value=3,
        max_value=20,
        value=5,
        step=1,
        help="Number of recent games to calculate rolling averages (3-20 games)",
    )

    st.sidebar.markdown("---")

    # Data refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    return selected_seasons, game_type, player_name, rolling_window


def setup_player_selection():
    try:
        with st.spinner("Loading player names..."):
            available_players = get_all_player_names()

        if available_players:
            # Add empty option at the beginning
            player_options = [""] + available_players

            selected_player_index = st.sidebar.selectbox(
                "Select a player:",
                options=range(len(player_options)),
                format_func=lambda x: (
                    player_options[x] if player_options[x] else "-- Choose a player --"
                ),
                help="Search and select a player from the dropdown",
            )

            player_name = (
                player_options[selected_player_index]
                if selected_player_index > 0
                else ""
            )
        else:
            st.sidebar.error("Could not load player names")
            player_name = ""

    except Exception as e:
        st.sidebar.error(f"Error loading players: {str(e)}")
        player_name = st.sidebar.text_input(
            "Enter player name:",
            placeholder="e.g., Nikola Jokic",
            help="Search for a player by name (partial matches supported)",
        )

    return player_name


def display_standings_table(standings_df, selected_seasons):
    st.header("Team Standings")

    if len(selected_seasons) == 1:
        st.subheader(f"{selected_seasons[0]} Season Standings")
    else:
        st.subheader(
            f"{selected_seasons[0]} to {selected_seasons[-1]} Combined Standings"
        )

    # Add rank column
    standings_display = standings_df.copy()
    standings_display.insert(0, "Rank", range(1, len(standings_display) + 1))

    st.dataframe(
        standings_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "win_percentage": st.column_config.NumberColumn("Win %", format="%.1f%%"),
            "avg_points": st.column_config.NumberColumn("Avg Points", format="%.1f"),
            "avg_rebounds": st.column_config.NumberColumn(
                "Avg Rebounds", format="%.1f"
            ),
            "avg_assists": st.column_config.NumberColumn("Avg Assists", format="%.1f"),
        },
    )


def display_player_stats_summary(player_stats_df):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_points = player_stats_df["points"].mean()
        st.metric("Avg Points", f"{avg_points:.1f}")

    with col2:
        avg_rebounds = player_stats_df["rebounds"].mean()
        st.metric("Avg Rebounds", f"{avg_rebounds:.1f}")

    with col3:
        avg_assists = player_stats_df["assists"].mean()
        st.metric("Avg Assists", f"{avg_assists:.1f}")

    with col4:
        avg_fg_pct = player_stats_df["fg_percentage"].mean()
        st.metric("Avg FG%", f"{avg_fg_pct:.1f}%")


def display_player_stats_table(player_stats_df):
    st.subheader("Game-by-Game Stats")

    display_columns = [
        "game_date",
        "points",
        "rebounds",
        "assists",
        "minutes",
        "fg_percentage",
        "three_pt_percentage",
        "ft_percentage",
        "steals",
        "blocks",
        "turnovers",
        "plus_minus",
    ]

    st.dataframe(
        player_stats_df[display_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "game_date": st.column_config.DateColumn("Date"),
            "points": st.column_config.NumberColumn("PTS", format="%.0f"),
            "rebounds": st.column_config.NumberColumn("REB", format="%.0f"),
            "assists": st.column_config.NumberColumn("AST", format="%.0f"),
            "minutes": st.column_config.TextColumn("MIN"),
            "fg_percentage": st.column_config.NumberColumn("FG%", format="%.1f%%"),
            "three_pt_percentage": st.column_config.NumberColumn(
                "3P%", format="%.1f%%"
            ),
            "ft_percentage": st.column_config.NumberColumn("FT%", format="%.1f%%"),
            "steals": st.column_config.NumberColumn("STL", format="%.0f"),
            "blocks": st.column_config.NumberColumn("BLK", format="%.0f"),
            "turnovers": st.column_config.NumberColumn("TO", format="%.0f"),
            "plus_minus": st.column_config.NumberColumn("+/-", format="%.0f"),
        },
    )


def render_footer(selected_seasons, game_type):
    st.markdown("---")
    st.markdown("### Technical Details")
    season_display = (
        f"{selected_seasons[0]}"
        if len(selected_seasons) == 1
        else f"{selected_seasons[0]} to {selected_seasons[-1]}"
    )
    st.info(
        f"""
    **Data Pipeline:** NBA API → AWS S3 → AWS Glue → AWS Athena → Streamlit  
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    **Season(s):** {season_display} {game_type}  
    """
    )


def render_sidebar_info(selected_seasons, game_type):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    season_display = (
        f"{selected_seasons[0]}"
        if len(selected_seasons) == 1
        else f"{selected_seasons[0]} to {selected_seasons[-1]}"
    )
    st.sidebar.info(
        f"""
    This dashboard analyzes NBA {season_display} {game_type.lower()} data using:
    - **AWS Athena** for fast SQL queries
    - **Streamlit** for interactive visualization
    - **Plotly** for dynamic charts
    """
    )

    st.sidebar.markdown("### Available Data")
    st.sidebar.markdown(
        """
    - Team performance statistics
    - Win/loss records
    - Player game-by-game stats
    - Points, rebounds, assists, shooting %
    """
    )
