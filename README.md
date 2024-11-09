# Chess PGN Analyzer API

This project is a FastAPI-based API for downloading and analyzing chess games from chess.com.

## Dev deployment with localtunnel

First deploy and run the localtunnel server:

```bash
docker-compose -f localtunnel-server.yml up -d
```

Then run your main stack:

```bash
docker-compose up -d
```

The localtunnel client will automatically connect to your localtunnel server and create a secure HTTPS tunnel. Your API will be accessible at: `https://chess-api.lt.tadeasfort.cz`

This URL will:
* **Have a valid HTTPS certificate**
* **Be publicly accessible**
* **Handle CORS issues since it's using HTTPS**
* **Allow your Next.js frontend to make API calls without any CORS configuration**
* **You can verify it's working by:**
* **Checking the localtunnel-client logs:**

```bash
docker-compose logs localtunnel-client
```

Making a test request to the URL:

```bash
curl https://chess-api.lt.tadeasfort.cz/docs
```

The tunnel will automatically reconnect if the connection drops, and the URL will remain consistent because you specified the subdomain (chess-api).

Obviously you **have to setup dns!** You can check examples in [localTunnelDNStutorial.md](./localtunnelDNStutorial.md)

## Deployment with Docker and Caddy

### Prerequisites

- Docker and Docker Compose
- A domain name pointed to your server's IP address

### Deployment Steps

1. Clone the repository to your server:

   ```sh
   git clone https://github.com/yourusername/chess-pgn-analyzer-api.git
   cd chess-pgn-analyzer-api
   ```

2. Create a `Caddyfile` in the project root with the following content (replace `your-domain.com` with your actual domain):

   ```sh
   your-domain.com {
     reverse_proxy api:8000
   }

   dashboard.your-domain.com {
     reverse_proxy api:8501
   }
   ```

3. Create a `.env` file in the project root with the following content:

   ```sh
   DATABASE_URL=postgresql://chess_user:chess_password@db:5432/chess_pgn_analyzer
   ```

4. Build and start the Docker containers:

   ```sh
   docker-compose up -d --build
   ```

5. The services will be available at:
   - API: `https://your-domain.com`
   - API Documentation: `https://your-domain.com/docs`
   - Streamlit Dashboard: `https://dashboard.your-domain.com`

6. To stop the services:

   ```sh
   docker-compose down
   ```

### Updating the Application

To update the application with new changes:

1. Pull the latest changes from the repository:

   ```sh
   git pull origin main
   ```

2. Rebuild and restart the containers:

   ```sh
   docker-compose up -d --build
   ```

### Viewing Logs

To view logs for a specific service:

```sh
docker-compose logs -f api
```

Replace `api` with `db` or `caddy` to view logs for other services.

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

- Swagger UI: `https://your-domain.com/docs`
- ReDoc: `https://your-domain.com/redoc`

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
