import os
import time
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, jsonify

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
STATIC_DIR = os.path.join(BASE_DIR, "static")

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

movie_list = None
similarity = None
movie_meta = None

poster_cache = {}

FALLBACK_POSTER = "/static/no-poster.svg"


def load_pickle(filename):
    path = os.path.join(MODEL_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required model file not found: {path}"
        )

    with open(path, "rb") as file:
        return pickle.load(file)


def load_model():
    global movie_list
    global similarity
    global movie_meta

    movie_list = load_pickle("movie_list.pkl")
    similarity = load_pickle("similarity.pkl")
    movie_meta = load_pickle("movie_meta.pkl")

    print("=" * 60)
    print("Movie model loaded successfully")
    print(f"Movies in movie_list: {len(movie_list)}")
    print(f"Movies in movie_meta: {len(movie_meta)}")
    print(f"TMDB API key loaded: {bool(TMDB_API_KEY)}")
    print("=" * 60)


load_model()


def get_value(row, column, default=None):
    try:
        if column in row:
            value = row[column]

            if value is None:
                return default

            try:
                if value != value:
                    return default
            except Exception:
                pass

            return value
    except Exception:
        pass

    return default


def clean_value(value):
    if value is None:
        return None

    try:
        if value != value:
            return None
    except Exception:
        pass

    try:
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass

    return value


def movie_to_dict(row, poster=None, score=None):
    movie_id = clean_value(
        get_value(
            row,
            "movie_id",
            get_value(row, "id", None)
        )
    )

    title = clean_value(
        get_value(
            row,
            "title",
            get_value(row, "movie_title", "")
        )
    )

    overview = clean_value(
        get_value(row, "overview", "")
    )

    rating = clean_value(
        get_value(
            row,
            "vote_average",
            get_value(
                row,
                "rating",
                get_value(row, "vote", None)
            )
        )
    )

    release_date = clean_value(
        get_value(
            row,
            "release_date",
            get_value(row, "release_year", "")
        )
    )

    popularity = clean_value(
        get_value(row, "popularity", None)
    )

    genres = clean_value(
        get_value(row, "genres", "")
    )

    result = {
        "movie_id": movie_id,
        "id": movie_id,
        "title": title,
        "movie_title": title,
        "poster": poster or FALLBACK_POSTER,
        "poster_url": poster or FALLBACK_POSTER,
        "overview": overview or "",
        "rating": rating,
        "vote_average": rating,
        "release_date": release_date or "",
        "popularity": popularity,
        "genres": genres
    }

    if score is not None:
        result["score"] = round(float(score), 4)
        result["similarity"] = round(float(score), 4)

    return result


def fetch_poster(movie_id, title=""):
    if movie_id in poster_cache:
        return poster_cache[movie_id]

    if not TMDB_API_KEY:
        poster_cache[movie_id] = FALLBACK_POSTER
        return FALLBACK_POSTER

    headers = {
        "Accept": "application/json",
        "User-Agent": "Movie-Recommendation-System/1.0"
    }

    movie_url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}"
    )

    for attempt in range(3):
        try:
            response = requests.get(
                movie_url,
                params={
                    "api_key": TMDB_API_KEY,
                    "language": "en-US"
                },
                headers=headers,
                timeout=15
            )

            if response.status_code == 429:
                time.sleep(2)
                continue

            if response.status_code == 200:
                data = response.json()
                poster_path = data.get("poster_path")

                if poster_path:
                    poster = (
                        "https://image.tmdb.org/t/p/w500"
                        + poster_path
                    )

                    poster_cache[movie_id] = poster
                    return poster

                break

        except Exception as error:
            print(
                f"[poster fetch failed] "
                f"movie_id={movie_id} "
                f"attempt={attempt} "
                f"error={error}"
            )

            time.sleep(0.8)

    if title:
        search_url = (
            "https://api.themoviedb.org/3/search/movie"
        )

        try:
            response = requests.get(
                search_url,
                params={
                    "api_key": TMDB_API_KEY,
                    "query": title,
                    "language": "en-US",
                    "include_adult": False
                },
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if results:
                    poster_path = results[0].get(
                        "poster_path"
                    )

                    if poster_path:
                        poster = (
                            "https://image.tmdb.org/t/p/w500"
                            + poster_path
                        )

                        poster_cache[movie_id] = poster
                        return poster

        except Exception as error:
            print(
                f"[TMDB search failed] "
                f"{title} | {error}"
            )

    poster_cache[movie_id] = FALLBACK_POSTER
    return FALLBACK_POSTER


def fetch_posters(rows):
    def get_poster(row):
        movie_id = get_value(
            row,
            "movie_id",
            get_value(row, "id", None)
        )

        title = get_value(
            row,
            "title",
            get_value(row, "movie_title", "")
        )

        try:
            movie_id = int(movie_id)
        except Exception:
            return FALLBACK_POSTER

        return fetch_poster(
            movie_id,
            str(title)
        )

    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:
        return list(
            executor.map(get_poster, rows)
        )


def find_title(typed):
    if movie_list is None:
        return None

    typed = str(typed).strip()

    if not typed:
        return None

    titles = movie_list["title"].astype(str)

    exact = movie_list[
        titles == typed
    ]

    if not exact.empty:
        return exact.iloc[0]["title"]

    lower_typed = typed.lower()

    case_insensitive = movie_list[
        titles.str.lower() == lower_typed
    ]

    if not case_insensitive.empty:
        return case_insensitive.iloc[0]["title"]

    partial = movie_list[
        titles.str.lower().str.contains(
            lower_typed,
            na=False,
            regex=False
        )
    ]

    if not partial.empty:
        return partial.iloc[0]["title"]

    return None


def recommend(title, limit=5):
    if movie_list is None or similarity is None:
        return []

    matches = movie_list[
        movie_list["title"] == title
    ]

    if matches.empty:
        return []

    position = matches.index[0]

    if hasattr(movie_list, "index"):
        try:
            position = movie_list.index.get_loc(
                matches.index[0]
            )
        except Exception:
            position = matches.index[0]

    distances = similarity[position]

    movie_indices = sorted(
        enumerate(distances),
        key=lambda x: x[1],
        reverse=True
    )

    movie_indices = movie_indices[
        1:limit + 1
    ]

    rows = [
        movie_list.iloc[index]
        for index, score in movie_indices
    ]

    posters = fetch_posters(rows)

    results = []

    for position, (
        (index, score),
        row
    ) in enumerate(
        zip(movie_indices, rows)
    ):
        results.append(
            movie_to_dict(
                row,
                posters[position],
                score
            )
        )

    return results


def prepare_home_movies(category, limit):
    if movie_meta is None:
        return []

    df = movie_meta.copy()

    if df.empty:
        return []

    category = str(category).lower()

    if category == "popular":
        if "popularity" in df.columns:
            df = df.sort_values(
                "popularity",
                ascending=False
            )

    elif category in ["top-rated", "top_rated"]:
        if "vote_average" in df.columns:
            df = df.sort_values(
                "vote_average",
                ascending=False
            )
        elif "rating" in df.columns:
            df = df.sort_values(
                "rating",
                ascending=False
            )

    elif category == "trending":
        if "popularity" in df.columns:
            df = df.sort_values(
                "popularity",
                ascending=False
            )

    elif category == "recent":
        if "release_date" in df.columns:
            df = df.sort_values(
                "release_date",
                ascending=False
            )

    df = df.head(limit)

    rows = [
        row
        for _, row in df.iterrows()
    ]

    posters = fetch_posters(rows)

    movies = []

    for row, poster in zip(rows, posters):
        movies.append(
            movie_to_dict(
                row,
                poster
            )
        )

    return movies


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/suggest")
def suggest_route():
    query = request.args.get(
        "q",
        request.args.get("query", "")
    ).strip()

    if not query:
        return jsonify({
            "suggestions": []
        })

    titles = movie_list["title"].astype(str)

    mask = titles.str.lower().str.contains(
        query.lower(),
        na=False,
        regex=False
    )

    suggestions = (
        movie_list.loc[mask, "title"]
        .astype(str)
        .drop_duplicates()
        .head(10)
        .tolist()
    )

    return jsonify({
        "suggestions": suggestions,
        "results": suggestions
    })


@app.route("/home-feed")
def home_feed_route():
    category = request.args.get(
        "category",
        "trending"
    )

    try:
        limit = int(
            request.args.get(
                "limit",
                18
            )
        )
    except Exception:
        limit = 18

    limit = max(
        1,
        min(limit, 50)
    )

    movies = prepare_home_movies(
        category,
        limit
    )

    return jsonify({
        "category": category,
        "limit": limit,
        "movies": movies,
        "results": movies
    })


@app.route("/movie/<int:movie_id>")
def movie_detail_route(movie_id):
    if movie_meta is None:
        return jsonify({
            "error": "Movie metadata is not loaded"
        }), 500

    if "movie_id" in movie_meta.columns:
        matches = movie_meta[
            movie_meta["movie_id"] == movie_id
        ]
    elif "id" in movie_meta.columns:
        matches = movie_meta[
            movie_meta["id"] == movie_id
        ]
    else:
        matches = movie_meta.iloc[0:0]

    if matches.empty:
        return jsonify({
            "error": "Movie not found"
        }), 404

    row = matches.iloc[0]

    title = get_value(
        row,
        "title",
        get_value(row, "movie_title", "")
    )

    poster = fetch_poster(
        movie_id,
        str(title)
    )

    return jsonify(
        movie_to_dict(
            row,
            poster
        )
    )


@app.route(
    "/recommend",
    methods=["GET", "POST"]
)
def recommend_route():
    title = ""

    if request.method == "POST":
        if request.is_json:
            data = request.get_json(
                silent=True
            ) or {}

            title = (
                data.get("title")
                or data.get("movie")
                or data.get("query")
                or ""
            )
        else:
            title = (
                request.form.get("title")
                or request.form.get("movie")
                or request.form.get("query")
                or ""
            )
    else:
        title = (
            request.args.get("title")
            or request.args.get("movie")
            or request.args.get("query")
            or ""
        )

    title = str(title).strip()

    if not title:
        return jsonify({
            "error": "Please enter a movie title",
            "recommendations": [],
            "movies": []
        }), 400

    matched_title = find_title(title)

    if not matched_title:
        return jsonify({
            "error": "Movie not found in the dataset",
            "recommendations": [],
            "movies": []
        }), 404

    recommendations = recommend(
        matched_title,
        5
    )

    return jsonify({
        "title": matched_title,
        "movie": matched_title,
        "recommendations": recommendations,
        "movies": recommendations,
        "results": recommendations
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "movie_list_loaded": movie_list is not None,
        "movie_meta_loaded": movie_meta is not None,
        "similarity_loaded": similarity is not None,
        "tmdb_key_loaded": bool(TMDB_API_KEY)
    })


if __name__ == "__main__":
    print("=" * 60)
    print("Starting Flask server...")
    print("Open: http://127.0.0.1:5000")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )