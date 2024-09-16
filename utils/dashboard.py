import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd
import json
from dotenv import load_dotenv
import os
from chess_pgn_analyzer_api.models.game import Game
from chess_pgn_analyzer_api.models.player import Player

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Streamlit app
st.set_page_config(layout="wide")
st.title("Chess Game Analysis Dashboard")

# Date range selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("End Date", datetime.now())

# Player selection
db = next(get_db())
players = db.query(Player).all()
selected_player = st.selectbox("Select Player", options=[p.username for p in players])

# Time control filter
time_controls = db.query(Game.time_control).distinct().all()
selected_time_control = st.multiselect(
    "Time Control", options=[tc[0] for tc in time_controls]
)

# Fetch filtered game data
query = (
    db.query(Game)
    .join(Player)
    .filter(
        Player.username == selected_player,
        Game.start_time >= start_date,
        Game.end_time <= end_date,
    )
)
if selected_time_control:
    query = query.filter(Game.time_control.in_(selected_time_control))
games = query.all()


def parse_analysis_result(result, player_color):
    try:
        parsed = json.loads(result)
        return float(parsed.get(player_color, 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0


def categorize_accuracy(accuracy):
    if accuracy >= 90:
        return "Excellent"
    elif accuracy >= 80:
        return "Good"
    elif accuracy >= 70:
        return "Fair"
    elif accuracy >= 60:
        return "Inaccurate"
    else:
        return "Poor"


def parse_move_analysis(move_analysis, player_color):
    if not move_analysis:
        return []
    try:
        moves = json.loads(move_analysis)
        player_moves = [
            move
            for i, move in enumerate(moves)
            if i % 2 == (0 if player_color == "white" else 1)
        ]
        return player_moves
    except (json.JSONDecodeError, TypeError):
        return []


def categorize_move(category):
    categories = {
        "??": "Blunder",
        "?": "Mistake",
        "?!": "Dubious Move",
        "∓": "Slight Disadvantage",
        "=": "Equal",
        "⩲": "Slight Advantage",
        "±": "Clear Advantage",
        "+": "Winning Advantage",
        "++": "Decisive Advantage",
    }
    return categories.get(category, "Normal")


try:
    df = pd.DataFrame(
        [
            {
                "date": game.end_time.date(),
                "player_color": "white"
                if game.white_username == selected_player
                else "black",
                "player_accuracy": parse_analysis_result(
                    game.analysis_result,
                    "white" if game.white_username == selected_player else "black",
                ),
                "player_rating": game.white_rating
                if game.white_username == selected_player
                else game.black_rating,
                "time_control": game.time_control,
                "result": game.white_result
                if game.white_username == selected_player
                else game.black_result,
                "move_analysis": parse_move_analysis(
                    getattr(game, "move_analysis", None),
                    "white" if game.white_username == selected_player else "black",
                ),
            }
            for game in games
        ]
    )

    # Calculate weekly averages
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W")
    weekly_accuracy = df.groupby("week")["player_accuracy"].mean().reset_index()
    weekly_accuracy["date"] = weekly_accuracy["week"].dt.to_timestamp()
    weekly_rating = df.groupby("week")["player_rating"].mean().reset_index()
    weekly_rating["date"] = weekly_rating["week"].dt.to_timestamp()

    # Flatten move analysis data
    move_data = []
    for _, row in df.iterrows():
        for move in row["move_analysis"]:
            move_data.append(
                {
                    "date": row["date"],
                    "category": categorize_move(move.get("category", "")),
                    "eval_diff": move.get("eval_diff"),
                }
            )

    move_df = pd.DataFrame(move_data)

    # Check if we have any move analysis data
    if not move_df.empty:
        st.subheader("Move Analysis")

        # Move Quality Distribution
        st.subheader("Move Quality Distribution")
        move_quality_counts = move_df["category"].value_counts()
        fig_move_quality = px.pie(
            values=move_quality_counts.values,
            names=move_quality_counts.index,
            title="Move Quality Distribution",
        )
        st.plotly_chart(fig_move_quality, use_container_width=True)

        # Average Move Performance Over Time
        st.subheader("Average Move Performance Over Time")
        move_df["date"] = pd.to_datetime(move_df["date"])
        move_df["week"] = move_df["date"].dt.to_period("W")
        weekly_move_performance = (
            move_df.groupby("week")["eval_diff"].mean().reset_index()
        )
        weekly_move_performance["date"] = weekly_move_performance[
            "week"
        ].dt.to_timestamp()

        fig_move_performance = px.line(
            weekly_move_performance,
            x="date",
            y="eval_diff",
            title="Weekly Average Move Performance",
            labels={"eval_diff": "Average Evaluation Difference", "date": "Date"},
        )
        fig_move_performance.update_traces(mode="lines+markers")
        st.plotly_chart(fig_move_performance, use_container_width=True)
    else:
        st.warning("No move analysis data available for the selected games.")

    # Display summary of available data
    st.subheader("Data Summary")
    total_games = len(df)
    games_with_move_analysis = df["move_analysis"].apply(len).gt(0).sum()
    st.write(f"Total games: {total_games}")
    st.write(f"Games with move analysis: {games_with_move_analysis}")
    st.write(
        f"Percentage of games with move analysis: {games_with_move_analysis/total_games*100:.2f}%"
    )

    # Visualizations
    if df.empty:
        st.write("No data available for the selected filters.")
    else:
        # Enhanced Average Accuracy Over Time
        st.subheader("Average Accuracy Over Time")
        fig_accuracy = go.Figure()
        fig_accuracy.add_trace(
            go.Scatter(
                x=weekly_accuracy["date"],
                y=weekly_accuracy["player_accuracy"],
                mode="lines+markers+text",
                name="Weekly Average Accuracy",
                line=dict(shape="spline", smoothing=0.3, color="blue"),
                marker=dict(size=8, color="blue"),
                text=weekly_accuracy["player_accuracy"].round(2),
                textposition="top center",
            )
        )
        fig_accuracy.update_layout(
            title="Player's Weekly Average Accuracy",
            xaxis_title="Date",
            yaxis_title="Accuracy",
            yaxis_range=[0, 100],
            hovermode="x unified",
        )
        st.plotly_chart(fig_accuracy, use_container_width=True)

        # Enhanced Player Rating Over Time
        st.subheader("Player Rating Over Time")
        fig_elo = go.Figure()
        fig_elo.add_trace(
            go.Scatter(
                x=weekly_rating["date"],
                y=weekly_rating["player_rating"],
                mode="lines+markers+text",
                name="Weekly Average Rating",
                line=dict(shape="spline", smoothing=0.3, color="blue"),
                marker=dict(size=8, color="blue"),
                text=weekly_rating["player_rating"].round(0),
                textposition="top center",
            )
        )
        fig_elo.update_layout(
            title="Player's Weekly Average Rating",
            xaxis_title="Date",
            yaxis_title="Rating",
            hovermode="x unified",
        )
        st.plotly_chart(fig_elo, use_container_width=True)

        # Game Accuracy Distribution
        st.subheader("Game Accuracy Distribution")
        fig_accuracy_dist = px.histogram(
            df,
            x="player_accuracy",
            nbins=20,
            title="Distribution of Game Accuracies",
            labels={"player_accuracy": "Accuracy", "count": "Number of Games"},
        )
        st.plotly_chart(fig_accuracy_dist, use_container_width=True)

        # Average Accuracy Over Time
        st.subheader("Average Accuracy Over Time")
        fig_accuracy_trend = px.line(
            weekly_accuracy,
            x="date",
            y="player_accuracy",
            title="Weekly Average Accuracy",
            labels={"player_accuracy": "Accuracy", "date": "Date"},
        )
        fig_accuracy_trend.update_traces(mode="lines+markers")
        st.plotly_chart(fig_accuracy_trend, use_container_width=True)

        # Game Outcomes
        st.subheader("Game Outcomes")
        outcome_counts = df["result"].value_counts()
        fig_outcomes = px.pie(
            values=outcome_counts.values,
            names=outcome_counts.index,
            title="Win/Loss/Draw Ratio",
        )
        st.plotly_chart(fig_outcomes, use_container_width=True)

        # Performance Analysis
        st.subheader("Performance Analysis")
        col1, col2 = st.columns(2)

        with col1:
            avg_accuracy = df["player_accuracy"].mean() / 100
            fig_accuracy_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=avg_accuracy,
                    title={"text": "Average Accuracy"},
                    gauge={
                        "axis": {"range": [0, 1]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 0.4], "color": "red"},
                            {"range": [0.4, 0.7], "color": "yellow"},
                            {"range": [0.7, 1], "color": "green"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 0.8,
                        },
                    },
                )
            )
            st.plotly_chart(fig_accuracy_gauge, use_container_width=True)

        with col2:
            rating_change = df["player_rating"].iloc[-1] - df["player_rating"].iloc[0]
            fig_rating_change = go.Figure(
                go.Indicator(
                    mode="delta",
                    value=df["player_rating"].iloc[-1],
                    delta={"reference": df["player_rating"].iloc[0], "relative": False},
                    title={"text": "Rating Change"},
                )
            )
            st.plotly_chart(fig_rating_change, use_container_width=True)

        # Accuracy Distribution by Color
        st.subheader("Accuracy Distribution by Color")
        fig_dist = px.box(
            df,
            x="player_color",
            y="player_accuracy",
            title="Accuracy Distribution by Color",
            labels={"player_accuracy": "Accuracy", "player_color": "Player Color"},
        )
        st.plotly_chart(fig_dist, use_container_width=True)

        # Accuracy vs Time Control
        st.subheader("Accuracy vs Time Control")
        fig_time_control = px.box(
            df,
            x="time_control",
            y="player_accuracy",
            title="Accuracy vs Time Control",
            labels={"player_accuracy": "Accuracy", "time_control": "Time Control"},
        )
        st.plotly_chart(fig_time_control, use_container_width=True)

except Exception as e:
    st.error(f"Error creating DataFrame: {str(e)}")
    st.write("Sample of problematic data:")
    for game in games[:5]:
        st.write(
            f"Game ID: {game.id}, Analysis Result: {game.analysis_result}, Move Analysis: {getattr(game, 'move_analysis', 'Not available')}"
        )
    st.stop()

# Close the database session
db.close()
