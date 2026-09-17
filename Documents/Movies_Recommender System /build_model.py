import ast
import os
import pickle

import pandas as pd
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "model")

MOVIES_CSV = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
CREDITS_CSV = os.path.join(DATA_DIR, "tmdb_5000_credits.csv")

os.makedirs(MODEL_DIR, exist_ok=True)

ps = PorterStemmer()


def convert(text):
    return [i["name"] for i in ast.literal_eval(text)]


def convert_top3(text):
    l = []
    counter = 0

    for i in ast.literal_eval(text):
        if counter < 3:
            l.append(i["name"])
            counter += 1

    return l


def fetch_director(text):
    return [
        i["name"]
        for i in ast.literal_eval(text)
        if i["job"] == "Director"
    ]


def remove_space(items):
    return [i.replace(" ", "") for i in items]


def stem(text):
    return " ".join(ps.stem(word) for word in text.split())


def build():
    print("Loading CSVs...")

    if not os.path.exists(MOVIES_CSV):
        raise FileNotFoundError(
            f"Movies CSV not found: {MOVIES_CSV}"
        )

    if not os.path.exists(CREDITS_CSV):
        raise FileNotFoundError(
            f"Credits CSV not found: {CREDITS_CSV}"
        )

    movies = pd.read_csv(MOVIES_CSV)
    credits = pd.read_csv(CREDITS_CSV)

    print(f"Movies rows: {len(movies)}")
    print(f"Credits rows: {len(credits)}")

    df = movies.merge(credits, on="title")

    df = df[
        [
            "movie_id",
            "title",
            "overview",
            "genres",
            "keywords",
            "cast",
            "crew",
            "release_date",
            "vote_average",
            "vote_count",
            "popularity",
        ]
    ]

    df.dropna(
        subset=[
            "overview",
            "genres",
            "keywords",
            "cast",
            "crew",
        ],
        inplace=True,
    )

    meta = df[
        [
            "movie_id",
            "title",
            "overview",
            "release_date",
            "vote_average",
            "vote_count",
            "popularity",
        ]
    ].copy()

    meta["genres"] = df["genres"].apply(convert)
    meta.reset_index(drop=True, inplace=True)

    meta_path = os.path.join(
        MODEL_DIR,
        "movie_meta.pkl"
    )

    with open(meta_path, "wb") as f:
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

    df["overview"] = df["overview"].apply(
        lambda x: x.split()
    )

    df["tag"] = (
        df["overview"]
        + df["genres"]
        + df["keywords"]
        + df["cast"]
        + df["crew"]
    )

    movie = df[
        [
            "movie_id",
            "title",
            "tag",
        ]
    ].copy()

    movie["tag"] = movie["tag"].apply(
        lambda x: " ".join(x)
    )

    print("Applying stemming...")

    movie["tag"] = movie["tag"].apply(stem)

    print("Vectorizing...")

    cv = CountVectorizer(
        max_features=5000,
        stop_words="english"
    )

    vectors = cv.fit_transform(
        movie["tag"]
    ).toarray()

    print("Computing cosine similarity...")

    similarity = cosine_similarity(vectors)

    movie.reset_index(drop=True, inplace=True)

    movie_list_path = os.path.join(
        MODEL_DIR,
        "movie_list.pkl"
    )

    similarity_path = os.path.join(
        MODEL_DIR,
        "similarity.pkl"
    )

    with open(movie_list_path, "wb") as f:
        pickle.dump(movie, f)

    with open(similarity_path, "wb") as f:
        pickle.dump(similarity, f)

    print(f"Done! {len(movie)} movies processed.")
    print("Model files generated successfully.")


if __name__ == "__main__":
    build()