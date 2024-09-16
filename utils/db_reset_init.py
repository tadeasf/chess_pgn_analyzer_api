import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()


def run_command(command):
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(stderr.decode())
        sys.exit(1)
    print(stdout.decode())


def run_sql_command(sql):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable is not set.")
        sys.exit(1)

    command = f'psql "{database_url}" -c "{sql}"'
    run_command(command)


if __name__ == "__main__":
    print("Dropping all tables in the public schema...")
    run_sql_command("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")

    print("Recreating Alembic version table...")
    run_command("alembic stamp head")

    print("Upgrading database to head...")
    run_command("alembic upgrade head")

    print("Database reset and initialization complete.")
