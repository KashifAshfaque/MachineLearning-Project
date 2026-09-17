/* ===== Elements ===== */
const input = document.getElementById("movieInput");
const suggestionsEl = document.getElementById("suggestions");
const recommendBtn = document.getElementById("recommendBtn");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");

const homeView = document.getElementById("homeView");
const detailView = document.getElementById("detailView");
const homeGrid = document.getElementById("homeGrid");
const recGrid = document.getElementById("recGrid");
const feedLabel = document.getElementById("feedLabel");
const categorySelect = document.getElementById("categorySelect");
const gridRange = document.getElementById("gridRange");
const gridValue = document.getElementById("gridValue");
const backBtn = document.getElementById("backBtn");
const cardTemplate = document.getElementById("cardTemplate");

const FALLBACK_POSTER = "/static/no-poster.svg";

let activeSuggestionIndex = -1;
let debounceTimer = null;

/* ===== Helpers ===== */
function showLoading(show) {
    loadingEl.classList.toggle("hidden", !show);
}

function showError(message) {
    if (!message) {
        errorEl.classList.add("hidden");
        errorEl.textContent = "";
        return;
    }
    errorEl.textContent = message;
    errorEl.classList.remove("hidden");
}

function showView(view) {
    homeView.classList.toggle("hidden", view !== "home");
    detailView.classList.toggle("hidden", view !== "detail");
}

/* Build one movie card from the <template>, return the DOM node */
function buildCard(movie) {
    const node = cardTemplate.content.cloneNode(true);
    const card = node.querySelector(".card");
    const img = node.querySelector(".card-img");
    const rating = node.querySelector(".card-rating");
    const title = node.querySelector(".card-title");
    const sub = node.querySelector(".card-sub");
    const openBtn = node.querySelector(".btn-open");

    img.src = movie.poster || FALLBACK_POSTER;
    img.alt = movie.title || "";
    img.onerror = () => { if (img.src !== FALLBACK_POSTER) img.src = FALLBACK_POSTER; };

    if (movie.vote_average) {
        rating.textContent = "★ " + movie.vote_average;
    }

    title.textContent = movie.title || "Unknown";
    sub.textContent = movie.score !== undefined ? `Similarity: ${movie.score}` : "";

    const open = () => openMovie(movie.movie_id);
    openBtn.addEventListener("click", (e) => { e.stopPropagation(); open(); });
    card.addEventListener("click", open);
    card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
    });

    return node;
}

function renderGrid(container, movies) {
    container.innerHTML = "";
    if (!movies || movies.length === 0) {
        container.innerHTML = `<p style="color:var(--text-dim)">Kuch nahi mila.</p>`;
        return;
    }
    movies.forEach((m) => container.appendChild(buildCard(m)));
}

/* ===== Home feed ===== */
async function loadHomeFeed() {
    const category = categorySelect.value;
    feedLabel.textContent = categorySelect.options[categorySelect.selectedIndex].text;
    showError(null);
    showLoading(true);
    try {
        const res = await fetch(`/home-feed?category=${encodeURIComponent(category)}&limit=18`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Home feed load nahi ho paayi.");
        renderGrid(homeGrid, data.results);
    } catch (err) {
        showError(err.message);
    } finally {
        showLoading(false);
    }
}

/* ===== Movie detail + recommendations ===== */
async function openMovie(movieId) {
    showError(null);
    showLoading(true);
    try {
        const res = await fetch(`/movie/${movieId}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Movie detail nahi mili.");

        document.getElementById("detailPoster").src = data.poster || FALLBACK_POSTER;
        document.getElementById("detailPoster").onerror = function () {
            if (this.src !== FALLBACK_POSTER) this.src = FALLBACK_POSTER;
        };
        document.getElementById("detailTitle").textContent = data.title || "";

        const year = data.release_date ? data.release_date.slice(0, 4) : "";
        const ratingText = data.vote_average ? `★ ${data.vote_average}` : "";
        document.getElementById("detailMeta").textContent = [year, ratingText].filter(Boolean).join("  •  ");

        const genresEl = document.getElementById("detailGenres");
        genresEl.innerHTML = "";
        (data.genres || []).forEach((g) => {
            const span = document.createElement("span");
            span.textContent = g;
            genresEl.appendChild(span);
        });

        document.getElementById("detailOverview").textContent = data.overview || "";

        renderGrid(recGrid, data.recommendations);
        showView("detail");
        window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
        showError(err.message);
    } finally {
        showLoading(false);
    }
}

backBtn.addEventListener("click", () => showView("home"));

/* ===== Search suggestions ===== */
function hideSuggestions() {
    suggestionsEl.classList.add("hidden");
    suggestionsEl.innerHTML = "";
    activeSuggestionIndex = -1;
    input.setAttribute("aria-expanded", "false");
}

function renderSuggestions(titles) {
    suggestionsEl.innerHTML = "";
    if (!titles || titles.length === 0) {
        hideSuggestions();
        return;
    }
    titles.forEach((title) => {
        const li = document.createElement("li");
        li.textContent = title;
        li.setAttribute("role", "option");
        li.addEventListener("click", () => {
            input.value = title;
            hideSuggestions();
            searchByTitle(title);
        });
        suggestionsEl.appendChild(li);
    });
    suggestionsEl.classList.remove("hidden");
    input.setAttribute("aria-expanded", "true");
}

input.addEventListener("input", () => {
    const q = input.value.trim();
    clearTimeout(debounceTimer);
    if (!q) {
        hideSuggestions();
        return;
    }
    debounceTimer = setTimeout(async () => {
        try {
            const res = await fetch(`/suggest?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            renderSuggestions(data.results);
        } catch (err) {
            hideSuggestions();
        }
    }, 250);
});

input.addEventListener("keydown", (e) => {
    const items = suggestionsEl.querySelectorAll("li");
    if (e.key === "ArrowDown" && items.length) {
        e.preventDefault();
        activeSuggestionIndex = (activeSuggestionIndex + 1) % items.length;
        items.forEach((li, i) => li.classList.toggle("active", i === activeSuggestionIndex));
    } else if (e.key === "ArrowUp" && items.length) {
        e.preventDefault();
        activeSuggestionIndex = (activeSuggestionIndex - 1 + items.length) % items.length;
        items.forEach((li, i) => li.classList.toggle("active", i === activeSuggestionIndex));
    } else if (e.key === "Enter") {
        if (activeSuggestionIndex >= 0 && items[activeSuggestionIndex]) {
            input.value = items[activeSuggestionIndex].textContent;
        }
        hideSuggestions();
        searchByTitle(input.value.trim());
    } else if (e.key === "Escape") {
        hideSuggestions();
    }
});

document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-wrap")) hideSuggestions();
});

/* ===== Recommend button -> exact search -> open detail ===== */
async function searchByTitle(title) {
    if (!title) {
        showError("Pehle movie ka naam type karo.");
        return;
    }
    showError(null);
    showLoading(true);
    try {
        const res = await fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Movie nahi mili.");
        await openMovie(data.matched_id);
    } catch (err) {
        showError(err.message);
        showLoading(false);
    }
}

recommendBtn.addEventListener("click", () => {
    hideSuggestions();
    searchByTitle(input.value.trim());
});

/* ===== Category + grid columns controls ===== */
categorySelect.addEventListener("change", loadHomeFeed);

gridRange.addEventListener("input", () => {
    gridValue.textContent = gridRange.value;
    homeGrid.style.setProperty("--cols", gridRange.value);
    recGrid.style.setProperty("--cols", gridRange.value);
});

/* ===== Init ===== */
homeGrid.style.setProperty("--cols", gridRange.value);
recGrid.style.setProperty("--cols", gridRange.value);
loadHomeFeed();
