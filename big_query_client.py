from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st
import db_dtypes as dbt
import pandas as pd


                            ################### ------------------------------------------------- ###########################
# build layout
# -- text area
# -- submit button
# -- sidebar
# after hit submit
# display datafrmae previe of dataset schema and checkboxed for schema tables
# user selects checkboxes and hits submit (submit button for sidebar)
# display dataframe preview of selected tables


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
client = get_bigquery_client()



@st.cache_data
def run_query(query: str):
    rows = client.query_and_wait(query)
    return rows.to_dataframe()


def query_handler(query: str):
    if not query.strip():
        st.error("Please enter a query")
        return None
    df = run_query(query)
    st.success("Query executed successfully")
    return df


@st.cache_resource
def get_all_datsets():
    # The client handles authentication and project selection
    # It uses Application Default Credentials by default.

    print("Datasets in the bigquery-public-data project:")
    # Specify the project ID for public data
    public_data_project_id = "bigquery-public-data"
    datasets = list(client.list_datasets(project=public_data_project_id))

    if datasets:
        return [dataset.dataset_id for dataset in datasets]
    else:
        print("No datasets found.")
        return []


def get_schema(dataset: str):
    query = f"""
        SELECT table_name
        FROM `bigquery-public-data.{dataset}.INFORMATION_SCHEMA.TABLES`
    """
    df = run_query(query)
    df.rename(columns={"table_name": "table_id"}, inplace=True)
    return df

def build_main_view():
    st.title("Big Query Client")
    datasets = get_all_datsets()

    if not datasets:
        st.write("No datasets found")
        return None, None

    selected_dataset = st.selectbox("Select a dataset", options=datasets)
    query = st.text_area("query", height=150)

    if selected_dataset != st.session_state.get("selected_dataset"):
        st.session_state.main_submitted = False

    st.button(
        "Submit",
        on_click=submit_handler_main,
        args=(selected_dataset,),
        key="submit_main"
    )

    return (
        st.session_state.get("schema"),
        st.session_state.get("selected_dataset")
    )


def update_chart_data_type(value):
    st.session_state.chart_data_type = value


def build_sidebar(schema, selected_dataset):
    st.sidebar.title("Big Query Datasets")
    st.sidebar.write("Select a table:")

    # -------------------------------
    # 1) TABLE SELECT (max 1)
    # -------------------------------
    if st.session_state.main_submitted:
        tables = list(schema.table_id)

        selected_table = st.sidebar.multiselect(
            "Choose one table:",
            tables,
            max_selections=1,
            key="sidebar_table_select"
        )
    else:
        selected_table = []

    # -------------------------------
    # 2) FIELD SELECT (max 2)
    # Only appears after table chosen
    # -------------------------------
    selected_fields = []

    if selected_table:
        dataset_path = f"bigquery-public-data.{selected_dataset}"
        table_path = f"{dataset_path}.{selected_table[0]}"

        table_obj = client.get_table(table_path)
        field_names = [field.name for field in table_obj.schema]

        selected_fields = st.sidebar.multiselect(
            "Select up to 2 fields:",
            field_names,
            max_selections=2,
            key="sidebar_field_select"
        )
    
  # 2) Radio buttons: disabled until fields selected
    if not selected_fields:
        chart_type = None
    else:
        chart_type = st.sidebar.radio(
            "Select a chart data type:",
            options=["Numeric", "Mixed"],
            key="sidebar_chart_data_type"
        )


    # -------------------------------
    # 3) SUBMIT BUTTON (bottom)
    # Enabled only when:
    # - main submit clicked
    # - table selected
    # - fields selected
    # -------------------------------
    button_disabled = not (
        st.session_state.main_submitted
        and selected_table
        and selected_fields
    )

    st.sidebar.button(
        "Submit",
        on_click=submit_handler_sidebar,
        args=(selected_dataset, selected_table, selected_fields, schema),
        disabled=button_disabled,
        key="sidebar_submit_btn"
    )

    return selected_table, selected_fields
def build_layout():
    schema, dataset = build_main_view()

    # Sidebar updates automatically based on state
    tables = build_sidebar(schema, dataset)


def safe_extract(df, cols):
    return df[[c for c in cols if c in df.columns]]

def plotting_demo_st(df: pd.DataFrame = None):
    default_data = {
        "num_legs": [2, 4, 8, 0],
        "num_wings": [2, 0, 0, 0],
        "num_specimen_seen": [10, 2, 1, 8],
    }
    df_default = pd.DataFrame(default_data, index=["falcon", "dog", "spider", "fish"])

    if df is None or df.empty:
        df = df_default

    # Only numeric columns for Streamlit charts
    numeric_df = df.select_dtypes(include=["number"])

    if numeric_df.empty:
        st.warning("No numeric columns available for plotting")
        st.dataframe(df)
        return

    st.dataframe(numeric_df)
    st.line_chart(numeric_df)



def plotting_demo_alt(df: pd.DataFrame, selected_fields: list):
    import altair as alt
    import streamlit as st

    # Validate data
    if df is None or df.empty:
        st.warning("No data available to plot")
        return

    # Keep only selected fields
    selected_fields = [f for f in selected_fields if f in df.columns]
    df = df[selected_fields]

    if not selected_fields:
        st.warning("No valid fields selected for plotting")
        st.dataframe(df)
        return

    # Identify numeric vs categorical
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    # Determine x and y
    if len(selected_fields) == 2:
        f1, f2 = selected_fields

        # numeric vs categorical mapping
        if f1 in numeric_cols and f2 in categorical_cols:
            x_field, y_field = f2, f1
        elif f2 in numeric_cols and f1 in categorical_cols:
            x_field, y_field = f1, f2
        else:
            # both numeric or both categorical
            x_field, y_field = f1, f2

    elif len(selected_fields) == 1:
        # Single field → plot against row index
        y_field = selected_fields[0]
        df = df.reset_index().rename(columns={"index": "row_index"})
        x_field = "row_index"

    # Determine Altair types
    x_type = "Q" if x_field in numeric_cols else "N"
    y_type = "Q" if y_field in numeric_cols else "N"

    # Build chart
    chart = (
        alt.Chart(df)
        .mark_point()
        .encode(
            x=alt.X(f"{x_field}:{x_type}", title=x_field),
            y=alt.Y(f"{y_field}:{y_type}", title=y_field),
            tooltip=selected_fields,
        )
        .properties(
            width="container",
            height=400,
            title="Custom Chart"
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


def submit_handler_main(selected_dataset: str):
    st.session_state.main_submitted = True
    st.session_state.selected_dataset = selected_dataset
    st.session_state.schema = get_schema(selected_dataset)
    if selected_dataset:
        st.write(f"Selected: {selected_dataset}\n\nID: bigquery-public-data.{selected_dataset}")
        schema = get_schema(selected_dataset)
        st.dataframe(schema)
        
        return schema, selected_dataset

def submit_handler_sidebar(selected_dataset: str, table: list, fields: list, schema: pd.DataFrame):
    if not fields:
        print("fields are not selected")
        return

    dataset_path = f"bigquery-public-data.{selected_dataset}"

    # Load the fields
    full_table_path = f"{dataset_path}.{table[0]}"

    df = run_query(f"SELECT * FROM `{full_table_path}` LIMIT 500")

    # If your checkboxes represent TABLES, not columns:
    df_small = safe_extract(df, fields)

    # If later your checkboxes represent COLUMNS, use:
    # df_small = safe_extract(df, tables)

    if st.session_state.chart_data_type == "Numeric":
        plotting_demo_st(df_small)
    else:
        plotting_demo_alt(df_small, fields)

def init_state():
    if "main_submitted" not in st.session_state:
        st.session_state.main_submitted = False

    if "schema" not in st.session_state:
        st.session_state.schema = None

    if "selected_dataset" not in st.session_state:
        st.session_state.selected_dataset = None

if __name__ == "__main__":
    init_state()
    build_layout()