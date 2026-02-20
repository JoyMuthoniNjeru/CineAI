// Load top movies on page load
window.onload = () => {
    loadTopMovies();
}

// --- LOAD TOP MOVIES ---
async function loadTopMovies() {
    const res = await fetch("/api/movies");
    const movies = await res.json();
    
    const grid = document.getElementById("topMovies");
    grid.innerHTML = movies.map(movie => createMovieCard(movie)).join("");
}

// --- SEARCH ---
async function searchMovies() {
    const query = document.getElementById("searchInput").value;
    if (!query) return;

    const res = await fetch(`/api/search?q=${query}`);
    const movies = await res.json();

    const section = document.getElementById("searchSection");
    const grid = document.getElementById("searchResults");

    section.style.display = "block";
    grid.innerHTML = movies.length 
        ? movies.map(movie => createMovieCard(movie)).join("")
        : "<p class='loading'>No results found.</p>";
}

// --- GET RECOMMENDATIONS ---
async function getRecommendations(movieId, movieTitle) {
    const res = await fetch(`/api/recommend/${movieId}`);
    const movies = await res.json();

    const section = document.getElementById("recommendSection");
    const grid = document.getElementById("recommendations");
    const title = document.getElementById("recommendTitle");

    title.textContent = movieTitle;
    section.style.display = "block";

    grid.innerHTML = movies.length
        ? movies.map(movie => createMovieCard(movie, true)).join("")
        : "<p class='loading'>No recommendations found.</p>";

    section.scrollIntoView({ behavior: "smooth" });
}

// --- CREATE MOVIE CARD ---
function createMovieCard(movie, showSimilarity = false) {
    const rating = movie.avg_rating ? `
        <div class="movie-rating">
            <span class="stars">★</span>
            <span>${movie.avg_rating}</span>
            <span class="rating-count">(${movie.num_ratings} ratings)</span>
        </div>` : "";

    const similarity = showSimilarity && movie.similarity ? `
        <span class="similarity-badge">🎯 ${movie.similarity}% match</span>` : "";

    return `
        <div class="movie-card">
            <div class="movie-title">${movie.title}</div>
            <div class="movie-genres">${movie.genres}</div>
            ${rating}
            ${similarity}
            <button class="recommend-btn" onclick="getRecommendations(${movie.movieId}, '${movie.title.replace(/'/g, "\\'")}')">
                ✨ Get Recommendations
            </button>
        </div>
    `;
}

// Search on Enter key
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("searchInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") searchMovies();
    });
});