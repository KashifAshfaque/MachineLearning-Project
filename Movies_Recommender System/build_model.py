"""
build_model.py
----------------
Ye script tumhare notebook (movies_recommendation.ipynb) ki poori logic
replicate karta hai:
    1. tmdb_5000_movies.csv + tmdb_5000_credits.csv ko merge karna
    2. genres, keywords, cast, crew ko clean karna
    3. sabko ek 'tag' column me combine karna
    4. stemming + CountVectorizer + cosine_similarity

Output: model/movie_list.pkl aur model/similarity.pkl
Flask app (app.py) inhi do pickle files ko load karke recommendations deta hai.

USAGE:
    1. data/tmdb_5000_movies.csv aur data/tmdb_5000_credits.csv daal do
       (Kaggle: "TMDB 5000 Movie Dataset")
    2. pip install -r requirements.txt
    3. python build_model.py
"""

import ast
import pickle
import pandas as pd
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MOVIES_CSV = "data/tmdb_5000_movies.csv"
CREDITS_CSV = "data/tmdb_5000_credits.csv"

ps = PorterStemmer()


def convert(text):
    """genres / keywords: list of dicts -> list of names"""
    return [i["name"] for i in ast.literal_eval(text)]


def convert_top3(text):
    """cast: sirf top 3 actors"""
    l, counter = [], 0
    for i in ast.literal_eval(text):
        if counter < 3:
            l.append(i["name"])
            counter += 1
    return l


def fetch_director(text):
    """crew: sirf director ka naam"""
    return [i["name"] for i in ast.literal_eval(text) if i["job"] == "Director"]


def remove_space(items):
    return [i.replace(" ", "") for i in items]


def stem(text):
    return " ".join(ps.stem(word) for word in text.split())


def build():
    print("Loading CSVs...")
    movies = pd.read_csv(MOVIES_CSV)
    credits = pd.read_csv(CREDITS_CSV)

    df = movies.merge(credits, on="title")
    df = df[[
        "movie_id", "title", "overview", "genres", "keywords", "cast", "crew",
        "release_date", "vote_average", "vote_count", "popularity",
    ]]
    df.dropna(subset=["overview", "genres", "keywords", "cast", "crew"], inplace=True)

    print("Building metadata (for home feed + detail view)...")
    meta = df[["movie_id", "title", "overview", "release_date", "vote_average", "vote_count", "popularity"]].copy()
    meta["genres"] = df["genres"].apply(convert)
    meta.reset_index(drop=True, inplace=True)
    with open("model/movie_meta.pkl", "wb") as f:
        pickle.dump(meta, f)

    print("Cleaning columns...")
    df["genres"] = df["genres"].apply(convert)
    df["keywords"] = df["keywords"].apply(convert)
    df["cast"] = df["cast"].apply(convert_top3)
    df["crew"] = df["crew"].apply(fetch_director)

    df["cast"] = df["cast"].apply(remove_space)
    df["crew"] = df["crew"].apply(remove_space)
    df["genres"] = df["genres"].apply(remove_space)
    df["keywords"] = df["keywords"].apply(remove_space)

    df["overview"] = df["overview"].apply(lambda x: x.split())
    df["tag"] = df["overview"] + df["genres"] + df["keywords"] + df["cast"] + df["crew"]

    movie = df[["movie_id", "title", "tag"]].copy()
    movie["tag"] = movie["tag"].apply(lambda x: " ".join(x))

    print("Stemming...")
    movie["tag"] = movie["tag"].apply(stem)

    print("Vectorizing + computing similarity (thoda time lagega)...")
    cv = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(movie["tag"]).toarray()
    similarity = cosine_similarity(vectors)

    movie.reset_index(drop=True, inplace=True)

    with open("model/movie_list.pkl", "wb") as f:
        pickle.dump(movie, f)
    with open("model/similarity.pkl", "wb") as f:
        pickle.dump(similarity, f)

    print(f"Done! {len(movie)} movies processed.")
    print("model/movie_list.pkl, model/similarity.pkl, model/movie_meta.pkl ban gaye. Ab app.py run karo.")


if __name__ == "__main__":
    build()
