import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def get_recommendations(movie_id, movies, ratings):
    # Create a movie-user matrix
    matrix = ratings.pivot_table(index="movieId", columns="userId", values="rating").fillna(0)
    
    if movie_id not in matrix.index:
        return []
    
    # Calculate similarity between movies
    similarity = cosine_similarity(matrix)
    sim_df = pd.DataFrame(similarity, index=matrix.index, columns=matrix.index)
    
    # Get most similar movies
    similar = sim_df[movie_id].sort_values(ascending=False)[1:6]
    
    # Get movie details
    recommended = movies[movies["movieId"].isin(similar.index)][["movieId", "title", "genres"]]
    recommended["similarity"] = recommended["movieId"].map(similar)
    recommended["similarity"] = (recommended["similarity"] * 100).round(1)
    recommended = recommended.sort_values("similarity", ascending=False)
    
    return recommended.to_dict(orient="records")
