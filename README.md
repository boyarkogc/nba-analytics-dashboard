cat << EOF > README.md
# NBA Analytics Dashboard 🏀

An interactive dashboard analyzing NBA 2023-24 season data using AWS Athena and Streamlit.

## Features
- Team standings and performance metrics
- Interactive team comparisons
- Home vs away analysis
- Season progression trends

## Tech Stack
- **Data Source**: NBA API
- **Data Pipeline**: AWS (S3, Glue, Athena)
- **Dashboard**: Streamlit + Plotly
- **Deployment**: Streamlit Community Cloud

## Live Dashboard
[View Dashboard](your-streamlit-url-here)

## Local Development
\`\`\`bash
pip install -r requirements.txt
streamlit run streamlit_app.py
\`\`\`

## Data Pipeline Architecture
NBA API → AWS S3 → AWS Glue → AWS Athena → Streamlit Dashboard
EOF