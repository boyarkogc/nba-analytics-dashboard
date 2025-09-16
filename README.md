# NBA Analytics Dashboard

An interactive dashboard analyzing NBA 2023-24 season data using AWS Athena and Streamlit

## Features
- Team standings and performance metrics
- Interactive team comparisons
- Home vs away analysis
- Season progression trends

## Tech Stack
- **Data Source**: NBA API (nba_api python library)
- **Data Pipeline**: AWS (S3, Glue, Athena)
- **Dashboard**: Streamlit + Plotly
- **Deployment**: Streamlit Community Cloud

## Live Dashboard
[View Dashboard](https://nba-analytics-dashboard-proj.streamlit.app/)

## Local Development
\`\`\`bash
pip install -r requirements.txt
streamlit run streamlit_app.py
\`\`\`

## Data Pipeline Architecture
NBA API → AWS S3 → AWS Glue → AWS Athena → Streamlit Dashboard

## Table schema

fact_player_stats:
  `game_id` string, 
  `team_id` bigint, 
  `player_id` bigint, 
  `player_name` string, 
  `position` string, 
  `minutes` string, 
  `comment` string, 
  `points` double, 
  `rebounds` double, 
  `assists` double, 
  `steals` double, 
  `blocks` double, 
  `field_goals_made` double, 
  `field_goals_attempted` double, 
  `three_pointers_made` double, 
  `three_pointers_attempted` double, 
  `free_throws_made` double, 
  `free_throws_attempted` double, 
  `turnovers` double, 
  `personal_fouls` double, 
  `plus_minus` double, 
  `game_date` date
PARTITIONED BY ( 
  `season` string, 
  `month` string)

dim_players:
  `player_id` bigint,
  `player_name` string,
  `position` string,
  `team_id` bigint