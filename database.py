import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# PyAthena for connecting to AWS Athena
try:
    from pyathena import connect
    from pyathena.pandas.cursor import PandasCursor
except ImportError:
    st.error("PyAthena not installed. Run: pip install PyAthena")
    st.stop()

load_dotenv()


@st.cache_resource
def init_athena_connection():
    try:
        # Get AWS credentials from environment
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        s3_staging_dir = f"s3://{os.getenv('NBA_ATHENA_BUCKET')}/streamlit-queries/"

        conn = connect(
            region_name=region, s3_staging_dir=s3_staging_dir, cursor_class=PandasCursor
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Athena: {str(e)}")
        st.error(
            "Make sure your AWS credentials are configured and NBA_ATHENA_BUCKET is set in .env"
        )
        st.stop()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def query_athena(query):
    conn = init_athena_connection()
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        st.error(f"Query: {query}")
        return pd.DataFrame()
