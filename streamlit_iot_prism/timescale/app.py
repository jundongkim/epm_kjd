import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time
import base64
from pathlib import Path
import plotly.express as px
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="TimescaleDB CSV Uploader",
    page_icon="🧊",
    layout="wide",
)

# --- Custom Font Setup ---
@st.cache_data
def load_font_css(font_path: Path) -> str:
    """Read a font file and return the CSS to embed it."""
    if not font_path.is_file():
        print(f"Font file not found at {font_path}")
        return ""
    with font_path.open("rb") as f:
        font_data = f.read()
    encoded_font = base64.b64encode(font_data).decode("utf-8")
    font_css = f"""
        <style>
            @font-face {{
                font-family: 'Paperlogy';
                src: url(data:font/ttf;base64,{encoded_font}) format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            html, body, [class*="st-"], [class*="css-"] {{
                font-family: 'Paperlogy', sans-serif;
            }}
        </style>
    """
    return font_css

# Construct path to the font file relative to the app script
font_path = Path(__file__).parent / "fonts" / "Paperlogy.ttf"
st.markdown(load_font_css(font_path), unsafe_allow_html=True)


# --- Database Connection ---
st.sidebar.header("Database Connection")
db_user = st.sidebar.text_input("User", "postgres")
db_password = st.sidebar.text_input("Password", "password", type="password")
db_host = st.sidebar.text_input("Host", "localhost")
db_port = st.sidebar.text_input("Port", "5432")
db_name = st.sidebar.text_input("Database", "postgres")

# Create a database URL
db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

try:
    engine = create_engine(db_url)
    with engine.connect() as connection:
        st.sidebar.success("Database connected successfully!")
except Exception as e:
    st.sidebar.error(f"Database connection failed: {e}")
    st.stop()


def get_hypertables():
    """Get list of hypertables from the database."""
    query = """
    SELECT hypertable_name
    FROM timescaledb_information.hypertables;
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            return [row[0] for row in result]
    except Exception:
        return []

# --- Main Application ---
st.title("📊 TimescaleDB CSV Import & Viewer")

st.markdown("""
This application allows you to upload a CSV file, ingest its data into a TimescaleDB hypertable,
and then view the data directly from the database.
""")

# --- Tabbed Interface ---
tab1, tab2, tab3 = st.tabs(["⬆️ Ingest Data", "🔍 View Data", "📊 Visualize Data"])

# --- Ingest Data Tab ---
with tab1:
    st.header("Upload and Ingest CSV Data")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # Preview the first 5 rows for efficiency, then reset file pointer
            df_preview = pd.read_csv(uploaded_file, nrows=5)
            st.write("**CSV Preview:**")
            st.dataframe(df_preview)
            uploaded_file.seek(0)

            st.subheader("Ingestion Settings")
            table_name = st.text_input("Enter a name for your database table", "sensor_data")
            
            # Get column headers without loading the entire file, then reset
            all_columns = pd.read_csv(uploaded_file, nrows=0).columns.tolist()
            uploaded_file.seek(0)

            # Detect potential time columns
            potential_time_cols = [col for col in all_columns if 'time' in col.lower() or 'date' in col.lower()]
            time_column = st.selectbox("Select the time column for the hypertable", options=all_columns, index=all_columns.index(potential_time_cols[0]) if potential_time_cols else 0)

            # Let user select data columns to ingest
            default_data_cols = [col for col in all_columns if col != time_column]
            data_columns_to_ingest = st.multiselect(
                "Select data columns to ingest (time column is always included)",
                options=default_data_cols,
                default=default_data_cols
            )
            
            st.info(f"Column '{time_column}' will be used as the time index.")

            if st.button("Ingest Data into TimescaleDB"):
                if not table_name:
                    st.warning("Please enter a table name.")
                elif not data_columns_to_ingest:
                    st.warning("Please select at least one data column to ingest.")
                else:
                    columns_to_use = [time_column] + data_columns_to_ingest
                    # Reset file pointer to the beginning before the full read
                    uploaded_file.seek(0)
                    
                    with st.spinner(f"Ingesting data into '{table_name}'... This may take a while for large files."):
                        start_time = time.time()
                        try:
                            chunk_size = 50000
                            total_rows = 0
                            
                            csv_reader = pd.read_csv(uploaded_file, chunksize=chunk_size, iterator=True, usecols=columns_to_use)
                            
                            first_chunk = next(csv_reader)
                            first_chunk[time_column] = pd.to_datetime(first_chunk[time_column])
                            
                            # Convert data columns to numeric to ensure correct DB types
                            for col in data_columns_to_ingest:
                                first_chunk[col] = pd.to_numeric(first_chunk[col], errors='coerce')

                            first_chunk.to_sql(table_name, engine, if_exists='replace', index=False)
                            total_rows += len(first_chunk)

                            with engine.connect() as connection:
                                with connection.begin():
                                    is_hypertable_query = text(f"SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = '{table_name}'")
                                    is_hypertable = connection.execute(is_hypertable_query).scalar() is not None
                                    if not is_hypertable:
                                        # Add migrate_data => TRUE to handle non-empty tables
                                        hypertable_query = text(f"SELECT create_hypertable('{table_name}', '{time_column}', migrate_data => TRUE);")
                                        connection.execute(hypertable_query)

                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            for i, chunk in enumerate(csv_reader):
                                chunk[time_column] = pd.to_datetime(chunk[time_column])
                                # Also convert subsequent chunks
                                for col in data_columns_to_ingest:
                                    chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
                                chunk.to_sql(table_name, engine, if_exists='append', index=False)
                                total_rows += len(chunk)
                                status_text.text(f"Processed approximately {total_rows} rows...")
                                # This is a placeholder for progress visualization
                                progress_bar.progress((i % 20) * 0.05)


                            progress_bar.empty()
                            status_text.empty()
                            end_time = time.time()
                            st.success(f"Successfully ingested {total_rows} rows into hypertable '{table_name}' in {end_time - start_time:.2f} seconds.")
                            st.balloons()
                        except StopIteration:
                            st.warning("The uploaded CSV file seems to be empty or has no rows with the selected columns.")
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

        except Exception as e:
            st.error(f"Error processing file: {e}")


# --- View Data Tab ---
with tab2:
    st.header("View Data from TimescaleDB")
    
    hypertables = get_hypertables()
    
    if not hypertables:
        st.info("No hypertables found in the database. Please ingest data first.")
    else:
        selected_table = st.selectbox("Select a hypertable to view", options=hypertables)
        
        if selected_table:
            try:
                with st.spinner(f"Loading data from '{selected_table}'..."):
                    query = f'SELECT * FROM "{selected_table}" ORDER BY 1 DESC LIMIT 1000' # Order by first column, assuming it's time
                    df_from_db = pd.read_sql(query, engine)
                    st.write(f"**Displaying last 1000 rows from `{selected_table}`:**")
                    st.dataframe(df_from_db)
            except Exception as e:
                st.error(f"Could not load data from table '{selected_table}': {e}")

# --- Visualize Data Tab ---
with tab3:
    st.header("Visualize Hypertable Data")
    
    hypertables = get_hypertables()
    
    if not hypertables:
        st.info("No hypertables found. Please ingest data first.")
    else:
        selected_table_viz = st.selectbox("Select a hypertable to visualize", options=hypertables, key="viz_table_selector")
        
        if selected_table_viz:
            try:
                time_column_viz = ""
                numeric_cols = []
                with engine.connect() as connection:
                    # Find the time column from hypertable metadata
                    time_col_query = text(f"""
                        SELECT d.column_name
                        FROM timescaledb_information.dimensions d
                        WHERE d.hypertable_name = :table_name
                        ORDER BY d.dimension_number
                        LIMIT 1;
                    """)
                    time_column_viz = connection.execute(time_col_query, {'table_name': selected_table_viz}).scalar_one_or_none()
                    
                    if not time_column_viz:
                        st.error("Could not automatically determine the main time column for this hypertable.")
                        st.stop()
                    
                    st.info(f"Using time column: `{time_column_viz}`")

                    # Get numeric columns directly from the database schema for reliability
                    numeric_cols_query = text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = :table_name
                        AND data_type IN (
                            'smallint', 'integer', 'bigint',
                            'decimal', 'numeric', 'real', 'double precision', 'money'
                        );
                    """)
                    numeric_cols_result = connection.execute(numeric_cols_query, {'table_name': selected_table_viz})
                    numeric_cols = [row[0] for row in numeric_cols_result]
                    
                    # Ensure the time column is not in the list of numeric columns for y-axis selection
                    if time_column_viz in numeric_cols:
                        numeric_cols.remove(time_column_viz)

                y_axis_cols = st.multiselect("Select columns for Y-axis", options=numeric_cols, default=numeric_cols[:1])

                # --- Performance Optimization ---
                st.subheader("Query Optimization")

                # 1. Time Range Selection
                col1, col2 = st.columns(2)
                with col1:
                    use_time_range = st.toggle("Filter by time range", value=True)
                with col2:
                    # 2. Data Aggregation
                    agg_option = st.selectbox(
                        "Aggregate data by (for speed)",
                        options=['None (raw data)', '1 minute', '5 minutes', '15 minutes', '1 hour', '1 day', '1 week'],
                        index=3 # Default to 1 hour
                    )
                
                start_datetime, end_datetime = None, None
                if use_time_range:
                    with engine.connect() as connection:
                        min_max_query = f'SELECT MIN("{time_column_viz}") as min_time, MAX("{time_column_viz}") as max_time FROM "{selected_table_viz}"'
                        min_max_df = pd.read_sql(min_max_query, connection)
                        min_dt = min_max_df['min_time'].iloc[0] if not min_max_df.empty else datetime.now()
                        max_dt = min_max_df['max_time'].iloc[0] if not min_max_df.empty else datetime.now()

                    col1_time, col2_time = st.columns(2)
                    with col1_time:
                        start_datetime = st.date_input("Start date", value=min_dt, min_value=min_dt, max_value=max_dt)
                    with col2_time:
                        end_datetime = st.date_input("End date", value=max_dt, min_value=min_dt, max_value=max_dt)


                if st.button("📊 Generate Chart"):
                    if not y_axis_cols:
                        st.warning("Please select at least one column for the Y-axis.")
                    else:
                        with st.spinner("Querying data and generating chart..."):
                            # Build the query
                            time_col_alias = "time"
                            
                            if agg_option == 'None (raw data)':
                                select_cols_str = f'"{time_column_viz}" AS {time_col_alias}, ' + ", ".join([f'"{c}"' for c in y_axis_cols])
                                query = f'SELECT {select_cols_str} FROM "{selected_table_viz}"'
                                where_clauses = []
                                if use_time_range and start_datetime and end_datetime:
                                    where_clauses.append(f'"{time_column_viz}" BETWEEN \'{start_datetime}\' AND \'{end_datetime}\'')
                                if where_clauses:
                                    query += " WHERE " + " AND ".join(where_clauses)
                                query += f' ORDER BY "{time_column_viz}" ASC'

                            else: # Use time_bucket for aggregation
                                interval = agg_option.replace(' ', '')
                                agg_cols = [f'AVG("{c}") as "{c}"' for c in y_axis_cols]
                                select_cols_str = f"time_bucket('{interval}', \"{time_column_viz}\") AS {time_col_alias}, {', '.join(agg_cols)}"
                                query = f'SELECT {select_cols_str} FROM "{selected_table_viz}"'
                                where_clauses = []
                                if use_time_range and start_datetime and end_datetime:
                                    where_clauses.append(f'"{time_column_viz}" BETWEEN \'{start_datetime}\' AND \'{end_datetime}\'')
                                if where_clauses:
                                    query += " WHERE " + " AND ".join(where_clauses)
                                query += f' GROUP BY {time_col_alias} ORDER BY {time_col_alias} ASC'

                            st.code(query, language="sql")
                            
                            # Fetch data and plot
                            plot_df = pd.read_sql(query, engine, index_col=time_col_alias)

                            if plot_df.empty:
                                st.warning("No data found for the selected time range and columns.")
                            else:
                                fig = px.line(plot_df, x=plot_df.index, y=y_axis_cols, title=f"Data from {selected_table_viz}")
                                fig.update_layout(
                                    xaxis_title='Time',
                                    font=dict(
                                        family="Paperlogy, sans-serif",
                                        size=14,
                                        color="black"
                                    )
                                )
                                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred during visualization: {e}") 