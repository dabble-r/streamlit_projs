from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import db_dtypes as dbt


# Construct a BigQuery client object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["bigquery"]
)


@st.cache_resource
def get_bigquery_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["bigquery"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

client = get_bigquery_client()

query = """
    SELECT name, SUM(number) as total_people
    FROM `bigquery-public-data.usa_names.usa_1910_2013`
    WHERE state = 'TX'
    GROUP BY name, state
    ORDER BY total_people DESC
    LIMIT 20
"""


@st.cache_data
def run_query(query: str):
    client = get_bigquery_client()
    rows = client.query_and_wait(query)  # Make an API request.
    df = rows.to_dataframe()
    return df

df = run_query(query)
st.dataframe(df)