# Demographic Bias Auditing Baseline

## Overview
This project tracks and audits data transformations during the preprocessing stage of machine learning pipelines. It utilizes a `ProvenanceMetadataTracker` to capture intersectional demographic data before and after every pipeline step. These metadata logs are pushed to a PostgreSQL JSONB database, where the Whale Optimization Algorithm (WOA) is utilized as a baseline to search for silent bias clusters.

## Prerequisites
Before running the pipeline, ensure you have the following installed:
1. **Python 3.x**
2. **PostgreSQL** and **pgAdmin 4** (for managing the database)

## 1. Database Setup (PostgreSQL)
To run this project, you must have a local PostgreSQL database configured to receive the metadata logs.

1. Open **pgAdmin 4** and connect to your local server.
2. Create a new database named `bias_audit_db` (or a name of your choice).
3. Open the **Query Tool** for your new database and run the following SQL command to create the required table:
   ```sql
   CREATE TABLE provenance_logs (
       id SERIAL PRIMARY KEY,
       log_data JSONB NOT NULL
   );
   ```

## 2. Environment Configuration
For security, database credentials are not hardcoded in the Python scripts. Every group member needs to create their own local environment file.

1. In the root directory of this project, create a new file named exactly **`.env`**.
2. Add the following lines to your `.env` file, replacing `your_pgadmin_password_here` with your actual PostgreSQL master password:
   ```env
   DB_NAME=bias_audit_db
   DB_USER=postgres
   DB_PASSWORD=your_pgadmin_password_here
   DB_HOST=localhost
   DB_PORT=5432
   ```
*(Note: The `.env` file is included in `.gitignore` to prevent uploading passwords to GitHub. Do not commit your password!)*

## 3. Python Setup
Open your terminal in the project folder and install the required Python libraries. This includes `psycopg2-binary` for database connection, `python-dotenv` for reading the environment variables, and `psutil` which will be used for evaluating memory scalability.

```bash
pip install pandas psycopg2-binary python-dotenv psutil
```

## Running the Pipeline
Once your database and environment variables are set up, you can execute the main script:

```bash
python main.py
```

This script will:
1. Load the raw demographic dataset.
2. Run data through the preprocessing pipelines (e.g., removing duplicates, fixing formats, handling missing values, and outliers).
3. Generate active metadata provenance snapshots to identify privileged demographic groups dynamically.
4. Export the resulting logs to `data/provenance/provenance_metadata.json` AND push them securely to your PostgreSQL database.

## Viewing and Managing Logs
To verify the logs were saved successfully:
1. Open **pgAdmin 4**.
2. Navigate to `bias_audit_db` -> **Schemas** -> **public** -> **Tables**.
3. Right-click on `provenance_logs` -> **View/Edit Data** -> **All Rows**.
4. Alternatively, you can run the following query in the Query Tool:
   ```sql
   SELECT * FROM public.provenance_logs ORDER BY id ASC;
   ```

**Resetting the Database for Testing:**
If you want to clear the logs and start from a fresh slate (resetting the ID counter back to 1), run this command in the pgAdmin 4 Query Tool:
```sql
TRUNCATE TABLE provenance_logs RESTART IDENTITY;
```
