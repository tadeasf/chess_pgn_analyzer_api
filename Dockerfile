# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary tools and Stockfish
RUN apt-get update && apt-get install -y \
    wget \
    stockfish \
    && rm -rf /var/lib/apt/lists/* \
    && echo 'export PATH=$PATH:/usr/games' >> /etc/bash.bashrc \
    && /usr/games/stockfish --version

# Install Stockfish
RUN apt-get update && apt-get install -y stockfish

# Set the Stockfish path environment variable
ENV STOCKFISH_PATH=/usr/games/stockfish

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.lock --use-pep517

# Make port 8000 available for the FastAPI app and 8501 for Streamlit
EXPOSE 8000 8501

# Create a script to run both FastAPI and Streamlit
RUN echo '#!/bin/bash\n\
export PATH=$PATH:/usr/games\n\
stockfish_path=$(which stockfish)\n\
echo "Stockfish path: $stockfish_path"\n\
$stockfish_path --version\n\
export STOCKFISH_PATH=$stockfish_path\n\
python -m src.chess_pgn_analyzer_api.wait_for_db\n\
uvicorn src.chess_pgn_analyzer_api.main:app --host 0.0.0.0 --port 8000 &\n\
streamlit run utils/dashboard.py --server.port 8501 --server.address 0.0.0.0\n\
wait' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the script
CMD ["/app/start.sh"]