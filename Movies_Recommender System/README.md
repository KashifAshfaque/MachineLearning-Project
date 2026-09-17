# Movie Recommendation System — Flask UI

Ye tumhare notebook (`movies_recommendation.ipynb`) ki logic ko Flask web app me convert kiya gaya hai.

## Folder Structure
```
movie_recommender/
├── app.py              # Flask backend
├── build_model.py      # Notebook logic — CSVs se pkl files banata hai
├── requirements.txt
├── data/                # <-- yahan apni 2 CSV files daalo
│   ├── tmdb_5000_movies.csv
│   └── tmdb_5000_credits.csv
├── model/               # build_model.py chalane ke baad yahan pkl ban jayenge
├── templates/
│   └── index.html
└── static/
    └── style.css
```

## Setup (5 steps)

1. **Dependencies install karo:**
   ```
   pip install -r requirements.txt
   ```

2. **NLTK ka data download karo** (ek baar):
   ```
   python -c "import nltk; nltk.download('punkt')"
   ```

3. **CSV files `data/` folder me daalo.**
   Tumhare notebook me ye Google Drive se load ho rahi thi
   (`tmdb_5000_movies.csv`, `tmdb_5000_credits.csv`) — wahi 2 files
   yahan `data/` me copy kar do. (Kaggle: "TMDB 5000 Movie Dataset")

4. **Model build karo** (ye notebook ka pura preprocessing + similarity matrix run karega):
   ```
   python build_model.py
   ```
   Isse `model/movie_list.pkl` aur `model/similarity.pkl` ban jayenge.

5. **App run karo:**
   ```
   python app.py
   ```
   Browser me kholo: **http://127.0.0.1:5000**

## Poster Images (Optional)
Agar tum movie posters bhi dikhana chahte ho, TMDB se free API key lo
(https://www.themoviedb.org/settings/api) aur environment variable set karo:

```
# Windows
set TMDB_API_KEY=your_key_here

# Mac/Linux
export TMDB_API_KEY=your_key_here
```

API key na do to bhi app chalega, bas poster placeholder image dikhegi.

## Kaise kaam karta hai
- Dropdown se movie select karo → "Recommend" dabao
- Frontend `/recommend` endpoint ko POST request bhejta hai
- Flask cosine similarity matrix se top-5 similar movies nikal ke JSON return karta hai
- JS un movies ko poster cards ki tarah render kar deta hai

## Deploy karna ho to
- **Render / Railway / PythonAnywhere** — free tier me Flask app easily deploy ho jata hai
- `model/*.pkl` files bhi deploy ke saath upload karna mat bhoolna (size 5000 movies ke liye ~50-100MB ho sakta hai)
