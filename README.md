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
