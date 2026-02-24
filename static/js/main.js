let currentMovie = null;

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
async function getRecommendations(movieId, movieTitle, event) {
    event.stopPropagation();
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

// --- LOAD TASTE PROFILE ---
async function loadTasteProfile() {
    const res = await fetch("/api/taste-profile");
    const data = await res.json();
    
    const container = document.getElementById("tasteBars");
    
    if (data.length === 0) {
        container.innerHTML = "<p class='loading'>No data yet — start clicking on movies!</p>";
        return;
    }
    
    const max = data[0].count;
    container.innerHTML = data.map(item => `
        <div class="taste-bar-row">
            <div class="taste-bar-label">${item.genre}</div>
            <div class="taste-bar-track">
                <div class="taste-bar-fill" style="width: ${(item.count / max) * 100}%"></div>
            </div>
            <div class="taste-bar-count">${item.count}</div>
        </div>
    `).join("");
}

// --- OPEN MOVIE PANEL ---
function openPanel(movie) {
    currentMovie = movie;
    document.getElementById("panelTitle").textContent = movie.title;
    document.getElementById("panelGenres").textContent = movie.genres;
    document.getElementById("aiBlurb").textContent = "Click generate to find out...";
    document.getElementById("reviewInput").value = "";
    document.getElementById("sentimentResult").textContent = "";
    document.getElementById("detailPanel").style.display = "block";
    document.getElementById("panelOverlay").style.display = "block";

    // Track genres for taste profile
    fetch("/api/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ genres: movie.genres })
    }).then(() => loadTasteProfile());
}

// --- CLOSE PANEL ---
function closePanel() {
    document.getElementById("detailPanel").style.display = "none";
    document.getElementById("panelOverlay").style.display = "none";
}

// --- GENERATE AI BLURB ---
async function generateAIBlurb() {
    if (!currentMovie) return;
    const blurb = document.getElementById("aiBlurb");
    blurb.textContent = "🤖 Thinking...";

    const res = await fetch(`/api/ai-blurb/${currentMovie.movieId}`);
    const data = await res.json();
    blurb.textContent = data.blurb;
}

// --- LIVE SENTIMENT ANALYSIS ---
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("searchInput").addEventListener("keypress", (e) => {
        if (e.key === "Enter") searchMovies();
    });

    document.getElementById("reviewInput").addEventListener("input", async (e) => {
        const text = e.target.value;
        const result = document.getElementById("sentimentResult");
        
        if (text.length < 10) {
            result.textContent = "";
            return;
        }

        const res = await fetch("/api/sentiment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        
        if (data.sentiment === "positive") {
            result.className = "sentiment-result positive";
            result.textContent = "😊 Positive review!";
        } else {
            result.className = "sentiment-result negative";
            result.textContent = "😞 Negative review";
        }
    });
});

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
        <div class="movie-card" onclick='openPanel(${JSON.stringify(movie)})'>
            <div class="movie-title">${movie.title}</div>
            <div class="movie-genres">${movie.genres}</div>
            ${rating}
            ${similarity}
            <button class="recommend-btn" onclick="getRecommendations(${movie.movieId}, '${movie.title.replace(/'/g, "\\'")}', event)">
                ✨ Get Recommendations
            </button>
        </div>
    `;

}