from flask import Flask, render_template, jsonify, request
import pandas as pd
import os

app = Flask(__name__)

# --- LOAD DATA ---
movies = pd.read_csv("data/movies.csv")
ratings = pd.read_csv("data/ratings.csv")

# Clean up genres
movies["genres"] = movies["genres"].str.replace("|", ", ", regex=False)

# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/movies")
def get_movies():
    # Get top rated movies
    avg_ratings = ratings.groupby("movieId")["rating"].agg(["mean", "count"]).reset_index()
    avg_ratings.columns = ["movieId", "avg_rating", "num_ratings"]
    
    # Merge with movie info
    top_movies = movies.merge(avg_ratings, on="movieId")
    
    # Only movies with at least 50 ratings
    top_movies = top_movies[top_movies["num_ratings"] >= 50]
    top_movies = top_movies.sort_values("avg_rating", ascending=False)
    
    # Return top 20
    result = top_movies.head(20)[["movieId", "title", "genres", "avg_rating", "num_ratings"]]
    result["avg_rating"] = result["avg_rating"].round(1)
    
    return jsonify(result.to_dict(orient="records"))

@app.route("/api/search")
def search_movies():
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify([])
    
    results = movies[movies["title"].str.lower().str.contains(query)]
    return jsonify(results.head(10)[["movieId", "title", "genres"]].to_dict(orient="records"))

@app.route("/api/recommend/<int:movie_id>")
def recommend(movie_id):
    from ml.recommender import get_recommendations
    recommendations = get_recommendations(movie_id, movies, ratings)
    return jsonify(recommendations)

if __name__ == "__main__":
    app.run(debug=True)