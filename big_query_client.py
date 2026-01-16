from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import db_dtypes as dbt
import pandas as pd


                            ################### ------------------------------------------------- ###########################

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

@st.cache_resource
def get_bigquery_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["bigquery"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

@st.cache_data
def run_query(query: str):
    client = get_bigquery_client()
    rows = client.query_and_wait(query)
    return rows.to_dataframe()

def query_handler(query: str):
    if not query.strip():
        st.error("Please enter a query")
        return None
    df = run_query(query)
    st.success("Query executed successfully")
    return df

def plotting_demo_st(query: str):
    df = query_handler(query)
    df_small = df[["name", "total"]]

    default_data = {
        "num_legs": [2, 4, 8, 0],
        "num_wings": [2, 0, 0, 0],
        "num_specimen_seen": [10, 2, 1, 8],
    }
    df_default = pd.DataFrame(default_data, index=["falcon", "dog", "spider", "fish"])

    if df is None:
        df_small = df_default

    st.dataframe(df)
    st.line_chart(df_small)

def plotting_demo_alt(query: str):
    import altair as alt
    import streamlit as st

    df_alt = query_handler(query)
    df_alt = df_alt[["name", "total", "gender"]]
    default_data = {
        "num_legs": [2, 4, 8, 0],
        "num_wings": [2, 0, 0, 0],
        "num_specimen_seen": [10, 2, 1, 8],
    }
    df_default = pd.DataFrame(default_data, index=["falcon", "dog", "spider", "fish"])
    if df_alt is None:
        df_alt = df_default

    chart = (
        alt.Chart(df_alt)
        #.mark_line()
        .mark_point()
        .encode(
            x=alt.X("name:N", title="Name"),
            y=alt.Y("total:Q", title="Total"),
            color=alt.Color("gender:N", scale=alt.Scale(scheme="category10")),
            tooltip=["name", "total", "gender"]
        )
        .properties(
            width="container",
            height=400,
            title="My Custom Line Chart"
        )
    )
    chart = chart.interactive()
    st.altair_chart(chart, use_container_width=True)

st.title("Big Query Client")

query_2 = st.text_area("query", height=150)

if st.button("Submit"):
    # plotting_demo_st(query_2)
    plotting_demo_alt(query_2)