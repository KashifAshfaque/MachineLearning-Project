"""
app.py — Flask backend for the Movie Recommendation System.

Run:
    python app.py
Then open http://127.0.0.1:5000 in the browser.

Requires model/movie_list.pkl and model/similarity.pkl (run build_model.py first).
"""

import os
import time
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()  # .env file se TMDB_API_KEY load karega agar present ho

app = Flask(__name__)

MODEL_DIR = "model"
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")  # optional, for poster images

movie_list = None
similarity = None
movie_meta = None


def load_model():
    global movie_list, similarity, movie_meta
    with open(os.path.join(MODEL_DIR, "movie_list.pkl"), "rb") as f:
        movie_list = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "similarity.pkl"), "rb") as f:
        similarity = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "movie_meta.pkl"), "rb") as f:
        movie_meta = pickle.load(f)


poster_cache = {}


def fetch_poster(movie_id):
    """TMDB API se poster laata hai — cached, retry ke saath. Fail hone pe local fallback svg."""
    fallback = "/static/no-poster.svg"

    if movie_id in poster_cache:
        return poster_cache[movie_id]

    if not TMDB_API_KEY:
        return fallback

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    for attempt in range(2):  # ek retry, network hiccup ke liye
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 429:  # TMDB rate limit — thoda ruk ke retry
                time.sleep(1)
                continue
            data = resp.json()
            poster_path = data.get("poster_path")
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                poster_cache[movie_id] = poster_url
                return poster_url
            break  # valid response but no poster_path -> fallback
        except Exception as e:
            print(f"[poster fetch failed] movie_id={movie_id} attempt={attempt} error={e}")
            time.sleep(0.5)

    poster_cache[movie_id] = fallback
    return fallback


def fetch_posters_parallel(movie_ids):
    """Ek saath multiple posters fetch karta hai (sequential se kaafi tez)."""
    with ThreadPoolExecutor(max_workers=8) as executor:
        posters = list(executor.map(fetch_poster, movie_ids))
    return dict(zip(movie_ids, posters))


def find_title(typed):
    """Exact match -> case-insensitive match -> partial/contains match."""
    exact = movie_list[movie_list["title"] == typed]
    if not exact.empty:
        return exact.iloc[0]["title"]

    lower_typed = typed.lower()
    ci = movie_list[movie_list["title"].str.lower() == lower_typed]
    if not ci.empty:
        return ci.iloc[0]["title"]

    partial = movie_list[movie_list["title"].str.lower().str.contains(lower_typed, na=False)]
    if not partial.empty:
        return partial.iloc[0]["title"]

    return None


def recommend(title):
    index = movie_list[movie_list["title"] == title].index[0]
    distances = similarity[index]
    movie_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    rows = [movie_list.iloc[i] for i, _ in movie_indices]
    posters = fetch_posters_parallel([int(r["movie_id"]) for r in rows])

    results = []
    for (i, score), row in zip(movie_indices, rows):
        mid = int(row["movie_id"])
        results.append({
            "title": row["title"],
            "movie_id": mid,
            "poster": posters[mid],
            "score": round(float(score), 3),
        })
    return results


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/suggest")
def suggest_route():
    q = (request.args.get("q") or "").strip().lower()
    if not q:
        return jsonify({"results": []})
    matches = movie_list[movie_list["title"].str.lower().str.contains(q, na=False)]
    titles = matches["title"].tolist()[:8]
    return jsonify({"results": titles})


@app.route("/home-feed")
def home_feed_route():
    category = request.args.get("category", "trending")
    limit = int(request.args.get("limit", 18))

    df = movie_meta.copy()
    if category == "top_rated":
        df = df[df["vote_count"] >= 100].sort_values("vote_average", ascending=False)
    elif category == "popular":
        df = df.sort_values("popularity", ascending=False)
    else:  # trending -> best proxy we have from a static dataset
        df = df.sort_values(["popularity", "vote_average"], ascending=False)

    df = df.head(limit)
    movie_ids = df["movie_id"].astype(int).tolist()
    posters = fetch_posters_parallel(movie_ids)

    results = []
    for _, row in df.iterrows():
        mid = int(row["movie_id"])
        results.append({
            "movie_id": mid,
            "title": row["title"],
            "poster": posters[mid],
            "vote_average": round(float(row["vote_average"]), 1),
        })
    return jsonify({"category": category, "results": results})


@app.route("/movie/<int:movie_id>")
def movie_detail_route(movie_id):
    meta_row = movie_meta[movie_meta["movie_id"] == movie_id]
    if meta_row.empty:
        return jsonify({"error": "movie not found"}), 404
    meta_row = meta_row.iloc[0]

    list_row = movie_list[movie_list["movie_id"] == movie_id]
    recs = recommend(list_row.iloc[0]["title"]) if not list_row.empty else []

    return jsonify({
        "movie_id": int(meta_row["movie_id"]),
        "title": meta_row["title"],
        "overview": meta_row["overview"],
        "genres": meta_row["genres"],
        "release_date": meta_row["release_date"],
        "vote_average": round(float(meta_row["vote_average"]), 1),
        "poster": fetch_poster(movie_id),
        "recommendations": recs,
    })


@app.route("/recommend", methods=["POST"])
def recommend_route():
    typed = request.form.get("title") or (request.json or {}).get("title")
    if not typed:
        return jsonify({"error": "movie title required"}), 400

    matched_title = find_title(typed.strip())
    if not matched_title:
        return jsonify({"error": "movie not found in dataset"}), 404

    matched_id = int(movie_list[movie_list["title"] == matched_title].iloc[0]["movie_id"])
    results = recommend(matched_title)
    return jsonify({"matched_title": matched_title, "matched_id": matched_id, "results": results})


if __name__ == "__main__":
    load_model()
    app.run(debug=False)