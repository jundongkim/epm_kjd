# TimescaleDB CSV Import & Viewer

This Streamlit application provides a user interface to:
1.  Upload large CSV files.
2.  Ingest the data into a TimescaleDB database, automatically creating a hypertable.
3.  View the data stored in the hypertables.

## Setup

### 1. Prerequisites

*   Python 3.7+
*   A running TimescaleDB instance. You can set one up using Docker.
    ```bash
    docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password timescale/timescaledb:latest-pg14
    ```

### 2. Installation

Clone the repository and install the required Python packages.

```bash
# It is recommended to use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

pip install -r requirements.txt
```

## Running the Application

1.  Make sure your TimescaleDB instance is running.
2.  Run the Streamlit application:

    ```bash
    streamlit run app.py
    ```

3.  Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).
4.  Use the sidebar to enter your TimescaleDB connection details.
5.  Upload a CSV file and ingest the data.
6.  Navigate to the "View Data" tab to see your data. 