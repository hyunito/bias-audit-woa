import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        connection = psycopg2.connect(
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        print("Database connection established successfully.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None
if __name__ == "__main__":
    conn = get_connection()
    if conn:

        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"PostgreSQL version: {db_version}")
        conn.close()
        print("Database connection closed.")