from flask import Flask, render_template, jsonify, request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
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

@app.route("/api/sentiment", methods=["POST"])
def analyze_sentiment():
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.naive_bayes import MultinomialNB

sentiment_reviews = [
    "amazing wonderful loved fantastic brilliant incredible outstanding",
    "great movie enjoyed it very much recommended",
    "beautiful story loved the characters heartwarming",
    "best film ever seen masterpiece loved every minute",
    "highly recommend brilliant acting loved the plot",
    "terrible awful horrible boring dreadful waste disappointing bad",
    "worst film ever seen hated every minute",
    "boring slow painful to watch complete disaster",
    "awful acting horrible story waste of time",
    "dreadful film do not watch it disappointing",
]
sentiment_labels = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]

sentiment_vec = CountVectorizer()
sentiment_X = sentiment_vec.fit_transform(sentiment_reviews)
sentiment_clf = MultinomialNB()
sentiment_clf.fit(sentiment_X, sentiment_labels)


# In-memory taste profile (tracks genre clicks)
taste_profile = {}

@app.route("/api/track", methods=["POST"])
def track_genre():
    data = request.get_json()
    genres = data.get("genres", "")
    
    for genre in genres.split(", "):
        genre = genre.strip()
        if genre:
            taste_profile[genre] = taste_profile.get(genre, 0) + 1
    
    return jsonify({"status": "ok"})

@app.route("/api/taste-profile")
def get_taste_profile():
    if not taste_profile:
        return jsonify([])
    
    sorted_profile = sorted(taste_profile.items(), key=lambda x: x[1], reverse=True)
    return jsonify([{"genre": k, "count": v} for k, v in sorted_profile[:8]])

@app.route("/api/ai-blurb/<int:movie_id>")
def ai_blurb(movie_id):
    from transformers import pipeline
    
    movie = movies[movies["movieId"] == movie_id].iloc[0]
    genres = movie["genres"]
    title = movie["title"]
    
    generator = pipeline("text-generation", model="distilgpt2")
    prompt = f"This {genres} movie called {title} is great because"
    result = generator(prompt, max_length=80, do_sample=True, temperature=0.9)
    
    blurb = result[0]["generated_text"]
    return jsonify({"blurb": blurb})

if __name__ == "__main__":
    app.run(debug=True)