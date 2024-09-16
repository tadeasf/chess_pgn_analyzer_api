# Chess PGN Analyzer API

This project is a FastAPI-based API for downloading and analyzing chess games from chess.com.

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.12 or higher
- [Rye](https://rye-up.com/) for Python package management

### Setting up the PostgreSQL Database

1. Ensure Docker is running on your machine.

2. From the root directory of the project, run the following command to start the PostgreSQL database:

   ```sh
   docker-compose -f postgres-compose.yml up -d
   ```

   This command will start the PostgreSQL database in detached mode.

3. To stop the database, you can use:

   ```sh
   docker-compose down
   ```

   If you want to remove the persisted data volume as well, use:

   ```sh
   docker-compose down -v
   ```

### Connecting to the Database

The database will be available with the following credentials:

- Host: `localhost`
- Port: `5432`
- Database: `chess_pgn_analyzer`
- User: `chess_user`
- Password: `chess_password`

You can use these details to connect to the database from your application or a
database management tool.

### Environment Setup

1. Create a `.env` file in the root directory of the project with the following content:

   ```sh
   DATABASE_URL=postgresql://chess_user:chess_password@localhost:5432/chess_pgn_analyzer
   ```

2. Install the project dependencies:

   ```sh
   rye sync
   ```

### Database Migrations with Alembic

This project uses Alembic for database migrations. Here's how to use it:

1. Initialize Alembic (only needed once):

   ```sh
   rye run alembic-init
   ```

2. Generate a new migration:

   ```sh
   rye run alembic-migrate "Description of the migration"
   ```

3. Apply migrations:

   ```sh
   rye run alembic-upgrade
   ```

### Running the Application

To run the application locally:

```sh
python run.py
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development Workflow

1. Start the PostgreSQL database using Docker Compose.
2. Run the FastAPI application locally.
3. Make changes to the code.
4. The FastAPI server will automatically reload with your changes.

Remember to stop the Docker containers when you're done developing.

## Contributing

[Add your contributing guidelines here]

## License

[Add your license information here]
