# NBA Analytics Dashboard
# Streamlit app that connects to Athena and displays NBA insights

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

# PyAthena for connecting to AWS Athena
try:
    from pyathena import connect
    from pyathena.pandas.cursor import PandasCursor
except ImportError:
    st.error("PyAthena not installed. Run: pip install PyAthena")
    st.stop()

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="NBA Analytics Dashboard",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B35;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize connection to Athena
@st.cache_resource
def init_athena_connection():
    """Initialize connection to AWS Athena"""
    try:
        # Get AWS credentials from environment
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        s3_staging_dir = f"s3://{os.getenv('NBA_ATHENA_BUCKET')}/streamlit-queries/"
        
        conn = connect(
            region_name=region,
            s3_staging_dir=s3_staging_dir,
            cursor_class=PandasCursor
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Athena: {str(e)}")
        st.error("Make sure your AWS credentials are configured and NBA_ATHENA_BUCKET is set in .env")
        st.stop()

# Query functions with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def query_athena(query):
    """Execute query against Athena and return DataFrame"""
    conn = init_athena_connection()
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        st.error(f"Query: {query}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_team_standings():
    """Get team standings and basic stats"""
    query = """
    SELECT 
        team_name,
        team_abbreviation,
        COUNT(*) as games_played,
        SUM(CASE WHEN win_loss = 'W' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN win_loss = 'L' THEN 1 ELSE 0 END) as losses,
        ROUND(
            CAST(SUM(CASE WHEN win_loss = 'W' THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 100, 
            1
        ) as win_percentage,
        ROUND(AVG(CAST(points AS DOUBLE)), 1) as avg_points,
        ROUND(AVG(CAST(total_rebounds AS DOUBLE)), 1) as avg_rebounds,
        ROUND(AVG(CAST(assists AS DOUBLE)), 1) as avg_assists
    FROM nba_analytics.fact_game_stats
    WHERE season = '2023-24'
    GROUP BY team_name, team_abbreviation
    ORDER BY win_percentage DESC, wins DESC
    """
    return query_athena(query)

@st.cache_data(ttl=300)
def get_team_performance_over_time(selected_teams):
    """Get team performance trends over time"""
    if not selected_teams:
        return pd.DataFrame()
    
    team_filter = "', '".join(selected_teams)
    query = f"""
    SELECT 
        team_name,
        game_date_parsed as game_date,
        points,
        total_rebounds,
        assists,
        win_loss,
        CASE WHEN win_loss = 'W' THEN 1 ELSE 0 END as win_numeric
    FROM nba_analytics.fact_game_stats
    WHERE season = '2023-24'
        AND team_name IN ('{team_filter}')
    ORDER BY team_name, game_date_parsed
    """
    return query_athena(query)

@st.cache_data(ttl=300)
def get_home_vs_away_stats():
    """Get home vs away performance comparison"""
    query = """
    SELECT 
        CASE WHEN is_home_game THEN 'Home' ELSE 'Away' END as game_location,
        COUNT(*) as games,
        SUM(CASE WHEN win_loss = 'W' THEN 1 ELSE 0 END) as wins,
        ROUND(
            CAST(SUM(CASE WHEN win_loss = 'W' THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 100, 
            1
        ) as win_percentage,
        ROUND(AVG(CAST(points AS DOUBLE)), 1) as avg_points,
        ROUND(AVG(CAST(field_goal_percentage AS DOUBLE)), 3) as avg_fg_pct
    FROM nba_analytics.fact_game_stats
    WHERE season = '2023-24'
    GROUP BY is_home_game
    """
    return query_athena(query)

@st.cache_data(ttl=300)
def get_monthly_trends():
    """Get league-wide trends by month"""
    query = """
    SELECT 
        month,
        CASE 
            WHEN month = 1 THEN 'January'
            WHEN month = 2 THEN 'February'
            WHEN month = 3 THEN 'March'
            WHEN month = 4 THEN 'April'
            WHEN month = 10 THEN 'October'
            WHEN month = 11 THEN 'November'
            WHEN month = 12 THEN 'December'
        END as month_name,
        COUNT(*) as total_games,
        ROUND(AVG(CAST(points AS DOUBLE)), 1) as avg_points,
        ROUND(AVG(CAST(field_goal_percentage AS DOUBLE)), 3) as avg_fg_pct,
        ROUND(AVG(CAST(three_point_percentage AS DOUBLE)), 3) as avg_3pt_pct
    FROM nba_analytics.fact_game_stats
    WHERE season = '2023-24'
    GROUP BY month
    ORDER BY month
    """
    return query_athena(query)

# Dashboard Header
st.markdown('<h1 class="main-header">🏀 NBA Analytics Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### 2023-24 Season Insights")

# Sidebar
st.sidebar.header("Dashboard Controls")
st.sidebar.markdown("---")

# Data refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Main dashboard
try:
    # Load data
    with st.spinner("Loading NBA data from Athena..."):
        standings_df = get_team_standings()
        home_away_df = get_home_vs_away_stats()
        monthly_df = get_monthly_trends()

    if standings_df.empty:
        st.error("No data found. Check your Athena connection and table structure.")
        st.stop()

    # Key Metrics Row
    st.header("🎯 Key League Statistics")
    col1, col2, col3, col4 = st.columns(4)

    total_games = standings_df['games_played'].sum()
    avg_points_league = standings_df['avg_points'].mean()
    highest_win_pct = standings_df['win_percentage'].max()
    best_team = standings_df.iloc[0]['team_name']

    with col1:
        st.metric("Total Games Played", f"{total_games:,}")
    with col2:
        st.metric("League Avg Points", f"{avg_points_league:.1f}")
    with col3:
        st.metric("Best Win %", f"{highest_win_pct}%")
    with col4:
        st.metric("Best Team", best_team)

    st.markdown("---")

    # Team Standings
    st.header("📊 Team Standings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Interactive standings table
        st.subheader("2023-24 Season Standings")
        
        # Add rank column
        standings_display = standings_df.copy()
        standings_display.insert(0, 'Rank', range(1, len(standings_display) + 1))
        
        st.dataframe(
            standings_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "win_percentage": st.column_config.NumberColumn(
                    "Win %",
                    format="%.1f%%"
                ),
                "avg_points": st.column_config.NumberColumn(
                    "Avg Points",
                    format="%.1f"
                ),
                "avg_rebounds": st.column_config.NumberColumn(
                    "Avg Rebounds", 
                    format="%.1f"
                ),
                "avg_assists": st.column_config.NumberColumn(
                    "Avg Assists",
                    format="%.1f"
                )
            }
        )

    with col2:
        # Top teams visualization
        st.subheader("Win Percentage Leaders")
        top_teams = standings_df.head(10)
        
        fig = px.bar(
            top_teams, 
            x='win_percentage', 
            y='team_abbreviation',
            orientation='h',
            title="Top 10 Teams by Win %",
            labels={'win_percentage': 'Win Percentage', 'team_abbreviation': 'Team'},
            color='win_percentage',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Team Performance Analysis
    st.header("🔍 Team Performance Analysis")
    
    # Team selector
    selected_teams = st.multiselect(
        "Select teams to compare:",
        options=sorted(standings_df['team_name'].tolist()),
        default=standings_df.head(3)['team_name'].tolist(),
        max_selections=5
    )
    
    if selected_teams:
        performance_df = get_team_performance_over_time(selected_teams)
        
        if not performance_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Points over time
                fig = px.line(
                    performance_df, 
                    x='game_date', 
                    y='points', 
                    color='team_name',
                    title="Points Per Game Over Time",
                    labels={'points': 'Points', 'game_date': 'Game Date'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Win/Loss over time (cumulative wins)
                performance_df = performance_df.sort_values(['team_name', 'game_date'])
                performance_df['cumulative_wins'] = performance_df.groupby('team_name')['win_numeric'].cumsum()
                
                fig = px.line(
                    performance_df,
                    x='game_date',
                    y='cumulative_wins', 
                    color='team_name',
                    title="Cumulative Wins Over Season",
                    labels={'cumulative_wins': 'Total Wins', 'game_date': 'Game Date'}
                )
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # League Trends
    st.header("📈 League Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Home vs Away performance
        st.subheader("Home vs Away Performance")
        if not home_away_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Win Percentage',
                x=home_away_df['game_location'],
                y=home_away_df['win_percentage'],
                yaxis='y',
                marker_color='lightblue'
            ))
            fig.add_trace(go.Scatter(
                name='Avg Points',
                x=home_away_df['game_location'],
                y=home_away_df['avg_points'],
                yaxis='y2',
                mode='lines+markers',
                marker_color='red',
                line=dict(width=3)
            ))
            
            fig.update_layout(
                title='Home Court Advantage Analysis',
                xaxis=dict(title='Game Location'),
                yaxis=dict(title='Win Percentage (%)', side='left'),
                yaxis2=dict(title='Average Points', side='right', overlaying='y'),
                legend=dict(x=0.7, y=1)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Monthly trends
        st.subheader("Season Progression")
        if not monthly_df.empty:
            fig = px.line(
                monthly_df,
                x='month_name',
                y=['avg_points', 'avg_fg_pct', 'avg_3pt_pct'],
                title="League Averages by Month",
                labels={'value': 'Value', 'month_name': 'Month'}
            )
            fig.update_layout(
                yaxis=dict(title='Points / Shooting %'),
                legend=dict(title='Metric')
            )
            st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("### 🔧 Technical Details")
    st.info(f"""
    **Data Pipeline:** NBA API → AWS S3 → AWS Glue → AWS Athena → Streamlit  
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    **Season:** 2023-24 Regular Season  
    **Total Games:** {total_games:,}
    """)

except Exception as e:
    st.error(f"Dashboard error: {str(e)}")
    st.error("Check your AWS credentials and Athena connection.")

# Sidebar information
st.sidebar.markdown("---")
st.sidebar.markdown("### 🏀 About")
st.sidebar.info("""
This dashboard analyzes NBA 2023-24 season data using:
- **AWS Athena** for fast SQL queries
- **Streamlit** for interactive visualization
- **Plotly** for dynamic charts
""")

st.sidebar.markdown("### 📊 Available Data")
st.sidebar.markdown("""
- Team performance statistics
- Win/loss records
- Points, rebounds, assists
- Home vs away analysis
- Season trends
""")