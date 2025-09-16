import streamlit as st
import pandas as pd
from database import query_athena


@st.cache_data(ttl=300)
def get_team_standings(seasons, game_type):
    season_filter = "', '".join(seasons)
    query = f"""
    SELECT 
        fgs.team_name,
        fgs.team_abbreviation,
        COUNT(*) as games_played,
        SUM(CASE WHEN fgs.win_loss = 'W' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN fgs.win_loss = 'L' THEN 1 ELSE 0 END) as losses,
        ROUND(
            CAST(SUM(CASE WHEN fgs.win_loss = 'W' THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 100, 
            1
        ) as win_percentage,
        ROUND(AVG(CAST(fgs.points AS DOUBLE)), 1) as avg_points,
        ROUND(AVG(CAST(fgs.total_rebounds AS DOUBLE)), 1) as avg_rebounds,
        ROUND(AVG(CAST(fgs.assists AS DOUBLE)), 1) as avg_assists
    FROM nba_analytics.fact_game_stats fgs
    JOIN nba_analytics.dim_games dg ON fgs.game_id = dg.game_id
    WHERE fgs.season IN ('{season_filter}')
        AND dg.game_type = '{game_type}'
    GROUP BY fgs.team_name, fgs.team_abbreviation
    ORDER BY win_percentage DESC, wins DESC
    """
    return query_athena(query)


@st.cache_data(ttl=300)
def get_team_performance_over_time(selected_teams, seasons, game_type):
    if not selected_teams:
        return pd.DataFrame()

    team_filter = "', '".join(selected_teams)
    season_filter = "', '".join(seasons)
    query = f"""
    SELECT 
        fgs.team_name,
        fgs.game_date_parsed as game_date,
        fgs.points,
        fgs.total_rebounds,
        fgs.assists,
        fgs.win_loss,
        CASE WHEN fgs.win_loss = 'W' THEN 1 ELSE 0 END as win_numeric
    FROM nba_analytics.fact_game_stats fgs
    JOIN nba_analytics.dim_games dg ON fgs.game_id = dg.game_id
    WHERE fgs.season IN ('{season_filter}')
        AND fgs.team_name IN ('{team_filter}')
        AND dg.game_type = '{game_type}'
    ORDER BY fgs.team_name, fgs.game_date_parsed
    """
    return query_athena(query)


@st.cache_data(ttl=300)
def get_available_seasons():
    query = """
    SELECT DISTINCT season
    FROM nba_analytics.dim_dates
    ORDER BY season ASC
    """
    return query_athena(query)


@st.cache_data(ttl=300)
def get_home_vs_away_stats(seasons, game_type):
    season_filter = "', '".join(seasons)
    query = f"""
    SELECT 
        CASE WHEN fgs.is_home_game THEN 'Home' ELSE 'Away' END as game_location,
        COUNT(*) as games,
        SUM(CASE WHEN fgs.win_loss = 'W' THEN 1 ELSE 0 END) as wins,
        ROUND(
            CAST(SUM(CASE WHEN fgs.win_loss = 'W' THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 100, 
            1
        ) as win_percentage,
        ROUND(AVG(CAST(fgs.points AS DOUBLE)), 1) as avg_points,
        ROUND(AVG(CAST(fgs.field_goal_percentage AS DOUBLE)), 3) as avg_fg_pct
    FROM nba_analytics.fact_game_stats fgs
    JOIN nba_analytics.dim_games dg ON fgs.game_id = dg.game_id
    WHERE fgs.season IN ('{season_filter}')
        AND dg.game_type = '{game_type}'
    GROUP BY fgs.is_home_game
    """
    return query_athena(query)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_player_names():
    query = """
    SELECT DISTINCT CAST(player_name AS VARCHAR) as player_name
    FROM nba_analytics.fact_player_stats
    WHERE player_name IS NOT NULL
    ORDER BY player_name
    """
    df = query_athena(query)
    return df["player_name"].tolist() if not df.empty else []


@st.cache_data(ttl=300)
def get_player_stats(player_name, seasons, game_type):
    if not player_name:
        return pd.DataFrame()

    # Use the same season filtering pattern as the working team queries
    season_filter = "', '".join(seasons)

    query = f"""
    SELECT 
        CAST(fps.game_date AS VARCHAR) as game_date,
        CAST(fps.player_name AS VARCHAR) as player_name,
        CAST(fps.position AS VARCHAR) as position,
        CAST(fps.minutes AS VARCHAR) as minutes,
        CAST(fps.points AS VARCHAR) as points,
        CAST(fps.rebounds AS VARCHAR) as rebounds,
        CAST(fps.assists AS VARCHAR) as assists,
        CAST(fps.steals AS VARCHAR) as steals,
        CAST(fps.blocks AS VARCHAR) as blocks,
        CAST(fps.field_goals_made AS VARCHAR) as field_goals_made,
        CAST(fps.field_goals_attempted AS VARCHAR) as field_goals_attempted,
        CAST(fps.three_pointers_made AS VARCHAR) as three_pointers_made,
        CAST(fps.three_pointers_attempted AS VARCHAR) as three_pointers_attempted,
        CAST(fps.free_throws_made AS VARCHAR) as free_throws_made,
        CAST(fps.free_throws_attempted AS VARCHAR) as free_throws_attempted,
        CAST(fps.turnovers AS VARCHAR) as turnovers,
        CAST(fps.personal_fouls AS VARCHAR) as personal_fouls,
        CAST(fps.plus_minus AS VARCHAR) as plus_minus,
        CAST(fps.season AS VARCHAR) as season
    FROM nba_analytics.fact_player_stats fps
    JOIN nba_analytics.dim_games dg ON fps.game_id = dg.game_id
    WHERE LOWER(fps.player_name) LIKE LOWER('%{player_name}%')
        AND fps.season IN ('{season_filter}')
        AND dg.game_type = '{game_type}'
    ORDER BY fps.game_date DESC
    """

    df = query_athena(query)

    if df.empty:
        return df

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")

    # Handle data type conversions in pandas - everything comes as strings now
    numeric_columns = [
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
        "field_goals_made",
        "field_goals_attempted",
        "three_pointers_made",
        "three_pointers_attempted",
        "free_throws_made",
        "free_throws_attempted",
        "turnovers",
        "personal_fouls",
        "plus_minus",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculate shooting percentages
    df["fg_percentage"] = df.apply(
        lambda row: (
            round(row["field_goals_made"] / row["field_goals_attempted"] * 100, 1)
            if row["field_goals_attempted"] > 0
            else 0
        ),
        axis=1,
    )

    df["three_pt_percentage"] = df.apply(
        lambda row: (
            round(row["three_pointers_made"] / row["three_pointers_attempted"] * 100, 1)
            if row["three_pointers_attempted"] > 0
            else 0
        ),
        axis=1,
    )

    df["ft_percentage"] = df.apply(
        lambda row: (
            round(row["free_throws_made"] / row["free_throws_attempted"] * 100, 1)
            if row["free_throws_attempted"] > 0
            else 0
        ),
        axis=1,
    )

    return df


def calculate_rolling_averages(df, window):
    if df.empty or len(df) < window:
        return pd.DataFrame()

    df_sorted = df.sort_values("game_date").copy()

    rolling_stats = [
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
        "field_goals_made",
        "field_goals_attempted",
        "three_pointers_made",
        "three_pointers_attempted",
        "free_throws_made",
        "free_throws_attempted",
        "turnovers",
    ]

    rolling_df = (
        df_sorted[rolling_stats].rolling(window=window, min_periods=window).mean()
    )

    rolling_df["game_date"] = df_sorted["game_date"].values
    rolling_df["player_name"] = df_sorted["player_name"].values
    rolling_df["games_in_window"] = window

    rolling_df["rolling_fg_pct"] = (
        rolling_df["field_goals_made"] / rolling_df["field_goals_attempted"] * 100
    ).round(1)
    rolling_df["rolling_3pt_pct"] = (
        rolling_df["three_pointers_made"] / rolling_df["three_pointers_attempted"] * 100
    ).round(1)
    rolling_df["rolling_ft_pct"] = (
        rolling_df["free_throws_made"] / rolling_df["free_throws_attempted"] * 100
    ).round(1)

    # Replace inf and nan values with 0
    rolling_df = rolling_df.replace([float("inf"), -float("inf")], 0).fillna(0)

    # Round the main stats to 1 decimal place
    for stat in rolling_stats:
        rolling_df[stat] = rolling_df[stat].round(1)

    # Only return rows where we have a full window of data
    rolling_df = rolling_df.dropna()

    return rolling_df
