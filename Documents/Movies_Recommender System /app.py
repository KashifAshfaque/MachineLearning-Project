import os
import time
import pickle
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
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

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "").strip()

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_API_BASE = "https://api.themoviedb.org/3"

FALLBACK_POSTER = "/static/no-poster.svg"

movie_list = None
similarity = None
movie_meta = None

poster_cache = {}

session = requests.Session()
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "Movie-Recommendation-System/1.0"
})


def clean_value(value, default=""):
    if value is None:
        return default

    try:
        if str(value).lower() == "nan":
            return default
    except Exception:
        pass

    return str(value).strip()


def get_value(item, key, default=""):
    if item is None:
        return default

    if isinstance(item, dict):
        return item.get(key, default)

    try:
        if hasattr(item, "get"):
            value = item.get(key, default)
            if value is not None:
                return value
    except Exception:
        pass

    try:
        return getattr(item, key, default)
    except Exception:
        return default


def movie_to_dict(movie, index=None):
    title = clean_value(
        get_value(movie, "title")
        or get_value(movie, "original_title")
        or get_value(movie, "name")
        or ""
    )

    movie_id = (
        get_value(movie, "id")
        or get_value(movie, "movie_id")
        or get_value(movie, "tmdb_id")
        or 0
    )

    try:
        movie_id = int(movie_id)
    except Exception:
        movie_id = 0

    overview = clean_value(
        get_value(movie, "overview")
        or get_value(movie, "description")
        or ""
    )

    release_date = clean_value(
        get_value(movie, "release_date")
        or get_value(movie, "release")
        or ""
    )

    genres = get_value(movie, "genres", "")

    if isinstance(genres, list):
        genres = ", ".join(
            clean_value(
                g.get("name", "")
                if isinstance(g, dict)
                else g
            )
            for g in genres
        )

    genres = clean_value(genres)

    poster = clean_value(
        get_value(movie, "poster")
        or get_value(movie, "poster_url")
        or get_value(movie, "poster_path")
        or ""
    )

    return {
        "index": index,
        "id": movie_id,
        "title": title,
        "overview": overview,
        "release_date": release_date,
        "genres": genres,
        "poster": poster
    }


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

    print("\n" + "=" * 65)
    print("Loading Movie Recommendation Model")
    print("=" * 65)

    movie_list = load_pickle("movie_list.pkl")
    similarity = load_pickle("similarity.pkl")
    movie_meta = load_pickle("movie_meta.pkl")

    print(f"Movies in movie_list : {len(movie_list)}")

    try:
        print(f"Movies in movie_meta : {len(movie_meta)}")
    except Exception:
        print("Movies in movie_meta : Unknown")

    print(f"TMDB API key loaded  : {bool(TMDB_API_KEY)}")

    print("=" * 65)
    print("Movie model loaded successfully")
    print("=" * 65 + "\n")


def fetch_poster(movie_id, title=""):
    try:
        movie_id = int(movie_id)
    except Exception:
        movie_id = 0

    if movie_id in poster_cache:
        return poster_cache[movie_id]

    if not TMDB_API_KEY:
        poster_cache[movie_id] = FALLBACK_POSTER
        return FALLBACK_POSTER

    headers = {
        "Accept": "application/json",
        "User-Agent": "Movie-Recommendation-System/1.0"
    }

    if movie_id:
        movie_url = f"{TMDB_API_BASE}/movie/{movie_id}"

        for attempt in range(3):
            try:
                response = session.get(
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
                        poster = TMDB_IMAGE_BASE + poster_path
                        poster_cache[movie_id] = poster
                        return poster

                    break

                if response.status_code == 404:
                    break

            except requests.exceptions.RequestException as error:
                print(
                    f"[TMDB] Request failed | "
                    f"movie_id={movie_id} | "
                    f"attempt={attempt + 1} | {error}"
                )
                time.sleep(0.8)

            except Exception as error:
                print(
                    f"[TMDB] Unexpected error | "
                    f"movie_id={movie_id} | {error}"
                )
                break

    title = clean_value(title)

    if title:
        search_url = f"{TMDB_API_BASE}/search/movie"

        for attempt in range(2):
            try:
                response = session.get(
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

                if response.status_code == 429:
                    time.sleep(2)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    if results:
                        selected_result = results[0]
                        title_lower = title.lower()

                        for result in results:
                            result_title = clean_value(
                                result.get("title", "")
                            )

                            if result_title.lower() == title_lower:
                                selected_result = result
                                break

                        poster_path = selected_result.get(
                            "poster_path"
                        )

                        if poster_path:
                            poster = (
                                TMDB_IMAGE_BASE
                                + poster_path
                            )

                            poster_cache[movie_id] = poster
                            return poster

                    break

            except requests.exceptions.RequestException as error:
                print(
                    f"[TMDB Search] {title} | "
                    f"attempt={attempt + 1} | {error}"
                )
                time.sleep(0.8)

            except Exception as error:
                print(
                    f"[TMDB Search] {title} | {error}"
                )
                break

    poster_cache[movie_id] = FALLBACK_POSTER
    return FALLBACK_POSTER


def fetch_posters(movies, max_workers=8):
    if not movies:
        return []

    results = [FALLBACK_POSTER] * len(movies)

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_map = {}

        for index, movie in enumerate(movies):
            movie_dict = movie_to_dict(
                movie,
                index=index
            )

            future = executor.submit(
                fetch_poster,
                movie_dict["id"],
                movie_dict["title"]
            )

            future_map[future] = index

        for future in as_completed(future_map):
            index = future_map[future]

            try:
                results[index] = future.result()
            except Exception as error:
                print(
                    f"[Poster Worker Error] "
                    f"index={index} | {error}"
                )
                results[index] = FALLBACK_POSTER

    return results


def find_title(query):
    if movie_list is None:
        return []

    query = clean_value(query).lower()

    if not query:
        return []

    matches = []

    try:
        if hasattr(movie_list, "iterrows"):
            for index, row in movie_list.iterrows():
                title = clean_value(
                    get_value(row, "title")
                )

                if query in title.lower():
                    matches.append(index)

                    if len(matches) >= 10:
                        break

            return matches

    except Exception as error:
        print(f"[find_title DataFrame] {error}")

    try:
        for index, movie in enumerate(movie_list):
            title = clean_value(
                get_value(movie, "title")
            )

            if query in title.lower():
                matches.append(index)

                if len(matches) >= 10:
                    break

    except Exception as error:
        print(f"[find_title list] {error}")

    return matches


def get_movie(index):
    try:
        if hasattr(movie_list, "iloc"):
            return movie_list.iloc[index]

        return movie_list[index]

    except Exception:
        return None


def recommend(title, count=10):
    if movie_list is None or similarity is None:
        return []

    title = clean_value(title)

    if not title:
        return []

    index = None

    try:
        if hasattr(movie_list, "reset_index"):
            data = movie_list.reset_index(drop=True)

            for i, row in data.iterrows():
                movie_title = clean_value(
                    get_value(row, "title")
                )

                if movie_title.lower() == title.lower():
                    index = i
                    break

            if index is None:
                for i, row in data.iterrows():
                    movie_title = clean_value(
                        get_value(row, "title")
                    )

                    if title.lower() in movie_title.lower():
                        index = i
                        break

    except Exception as error:
        print(f"[Recommendation search] {error}")

    if index is None:
        try:
            for i, movie in enumerate(movie_list):
                movie_title = clean_value(
                    get_value(movie, "title")
                )

                if movie_title.lower() == title.lower():
                    index = i
                    break

                if title.lower() in movie_title.lower():
                    index = i

        except Exception as error:
            print(
                f"[Recommendation list search] {error}"
            )

    if index is None:
        return []

    try:
        distances = similarity[index]
    except Exception as error:
        print(
            f"[Similarity error] "
            f"index={index} | {error}"
        )
        return []

    try:
        movie_indexes = sorted(
            enumerate(distances),
            key=lambda x: x[1],
            reverse=True
        )
    except Exception as error:
        print(
            f"[Similarity sorting error] {error}"
        )
        return []

    recommendations = []

    for movie_index, score in movie_indexes[1:]:

        if len(recommendations) >= count:
            break

        try:
            movie = get_movie(movie_index)

            if movie is None:
                continue

            movie_dict = movie_to_dict(
                movie,
                index=movie_index
            )

            movie_dict["similarity"] = round(
                float(score),
                4
            )

            recommendations.append(movie_dict)

        except Exception as error:
            print(
                f"[Recommendation item error] "
                f"{movie_index} | {error}"
            )

    poster_list = fetch_posters(
        recommendations,
        max_workers=8
    )

    for i, poster in enumerate(poster_list):
        if i < len(recommendations):
            recommendations[i]["poster"] = poster

    return recommendations


def prepare_home_movies(limit=12):
    if movie_list is None:
        return []

    movies = []

    try:
        total = min(
            len(movie_list),
            limit
        )

        for i in range(total):
            movie = get_movie(i)

            if movie is None:
                continue

            movie_dict = movie_to_dict(
                movie,
                index=i
            )

            movies.append(movie_dict)

    except Exception as error:
        print(f"[Home movies error] {error}")
        return []

    posters = fetch_posters(
        movies,
        max_workers=8
    )

    for i, poster in enumerate(posters):
        if i < len(movies):
            movies[i]["poster"] = poster

    return movies


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/suggest")
def suggest():
    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:
        return jsonify([])

    matches = find_title(query)

    suggestions = []

    for index in matches:
        try:
            movie = get_movie(index)

            movie_dict = movie_to_dict(
                movie,
                index=index
            )

            suggestions.append({
                "id": movie_dict["id"],
                "title": movie_dict["title"],
                "index": index
            })

        except Exception:
            continue

    return jsonify(suggestions)


@app.route("/home-feed")
def home_feed():
    try:
        movies = prepare_home_movies(
            limit=12
        )

        return jsonify({
            "success": True,
            "movies": movies
        })

    except Exception as error:
        print(f"[Home Feed Error] {error}")

        return jsonify({
            "success": False,
            "movies": [],
            "error": str(error)
        }), 500


@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    if movie_list is None:
        return jsonify({
            "success": False,
            "error": "Movie model is not loaded."
        }), 500

    found_movie = None

    try:
        if hasattr(movie_list, "iterrows"):
            for index, row in movie_list.iterrows():

                current_id = (
                    get_value(row, "id")
                    or get_value(row, "movie_id")
                    or get_value(row, "tmdb_id")
                    or 0
                )

                try:
                    current_id = int(current_id)
                except Exception:
                    continue

                if current_id == movie_id:
                    found_movie = movie_to_dict(
                        row,
                        index=index
                    )
                    break

    except Exception as error:
        print(
            f"[Movie Details DataFrame] {error}"
        )

    if found_movie is None:
        try:
            for index, movie in enumerate(movie_list):

                current_id = (
                    get_value(movie, "id")
                    or get_value(movie, "movie_id")
                    or get_value(movie, "tmdb_id")
                    or 0
                )

                try:
                    current_id = int(current_id)
                except Exception:
                    continue

                if current_id == movie_id:
                    found_movie = movie_to_dict(
                        movie,
                        index=index
                    )
                    break

        except Exception as error:
            print(
                f"[Movie Details List] {error}"
            )

    if found_movie is None:
        return jsonify({
            "success": False,
            "error": "Movie not found."
        }), 404

    found_movie["poster"] = fetch_poster(
        found_movie["id"],
        found_movie["title"]
    )

    return jsonify({
        "success": True,
        "movie": found_movie
    })


@app.route(
    "/recommend",
    methods=["GET", "POST"]
)
def recommend_route():

    if request.method == "POST":

        data = request.get_json(
            silent=True
        ) or {}

        title = (
            data.get("title")
            or data.get("movie")
            or data.get("query")
            or ""
        )

        try:
            count = int(
                data.get(
                    "count",
                    10
                )
            )
        except Exception:
            count = 10

    else:

        title = (
            request.args.get("title")
            or request.args.get("movie")
            or request.args.get("query")
            or ""
        )

        try:
            count = int(
                request.args.get(
                    "count",
                    10
                )
            )
        except Exception:
            count = 10

    count = max(
        1,
        min(count, 20)
    )

    title = title.strip()

    if not title:
        return jsonify({
            "success": False,
            "error": "Please provide a movie title.",
            "recommendations": []
        }), 400

    try:

        recommendations = recommend(
            title,
            count=count
        )

        return jsonify({
            "success": True,
            "movie": title,
            "recommendations": recommendations
        })

    except Exception as error:

        print(
            f"[Recommendation Route Error] "
            f"{error}"
        )

        return jsonify({
            "success": False,
            "error": str(error),
            "recommendations": []
        }), 500


@app.route("/health")
def health():

    model_loaded = (
        movie_list is not None
        and similarity is not None
        and movie_meta is not None
    )

    return jsonify({
        "status": "ok",
        "model_loaded": model_loaded,
        "movie_count": (
            len(movie_list)
            if movie_list is not None
            else 0
        ),
        "tmdb_api_key_loaded": bool(
            TMDB_API_KEY
        )
    })


@app.route("/model-status")
def model_status():

    return jsonify({
        "movie_list_loaded": movie_list is not None,
        "similarity_loaded": similarity is not None,
        "movie_meta_loaded": movie_meta is not None,
        "movie_count": (
            len(movie_list)
            if movie_list is not None
            else 0
        ),
        "meta_count": (
            len(movie_meta)
            if movie_meta is not None
            else 0
        ),
        "tmdb_api_key_loaded": bool(
            TMDB_API_KEY
        ),
        "model_directory": MODEL_DIR
    })


load_model()


if __name__ == "__main__":

    print("\nMovie Recommendation System started!")

    print(
        "Open: http://127.0.0.1:5000"
    )

    print(
        "Health: http://127.0.0.1:5000/health"
    )

    print(
        "Model Status: "
        "http://127.0.0.1:5000/model-status"
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )