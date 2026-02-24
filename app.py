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

@app.route("/api/sentiment", methods=["POST"])
def analyze_sentiment():
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.naive_bayes import MultinomialNB
    
    data = request.get_json()
    text = data.get("text", "")
    
    # Quick sentiment model
    sample_reviews = [
        "amazing wonderful loved fantastic brilliant incredible outstanding",
        "terrible awful horrible boring dreadful waste disappointing bad",
        "great movie enjoyed it very much recommended",
        "worst film ever seen hated every minute",
    ]
    sample_labels = [1, 0, 1, 0]
    
    vec = CountVectorizer()
    X = vec.fit_transform(sample_reviews)
    clf = MultinomialNB()
    clf.fit(X, sample_labels)
    
    result = clf.predict(vec.transform([text]))[0]
    return jsonify({"sentiment": "positive" if result == 1 else "negative"})

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