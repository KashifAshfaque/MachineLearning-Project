# 🎬 Movie Recommendation System

A content-based movie recommendation web application built with **Python, Flask, and Machine Learning**. The system recommends movies based on the similarity between their metadata such as genres, keywords, cast, crew, and other movie information.

## 🚀 Overview

This project converts a machine learning movie recommendation model into an interactive Flask web application.

Users can:

- Search/select a movie
- Get similar movie recommendations
- View movie posters and details
- Interact with the recommendation system through a web interface

The recommendation engine uses **content-based filtering** with **Cosine Similarity**.

---

## ✨ Features

- 🎥 Content-based movie recommendations
- 🔎 Movie search interface
- 🧠 Machine Learning based similarity calculation
- 📊 TMDB 5000 Movies dataset
- 🌐 Flask web application
- 🎨 Responsive frontend interface
- 🖼️ Movie poster integration
- ⚡ Pre-computed similarity model for faster recommendations

---

## 🛠️ Tech Stack

### Programming & Machine Learning
- Python
- Pandas
- NumPy
- Scikit-learn
- Cosine Similarity

### Backend
- Flask

### Frontend
- HTML
- CSS
- JavaScript

### Data & Model
- TMDB 5000 Movies Dataset
- Pickle (`.pkl`) model files

---

## 🧠 Recommendation Approach

The system follows a **content-based recommendation approach**.

### Workflow

```text
Movie Dataset
     ↓
Data Cleaning & Preprocessing
     ↓
Feature Extraction
     ↓
Text Feature Combination
     ↓
Vectorization
     ↓
Cosine Similarity
     ↓
Similarity Matrix
     ↓
Movie Recommendations
     ↓
Flask Web Application
```

Movies with similar metadata receive higher similarity scores and are recommended to the user.

---

## 📂 Project Structure

```text
Movies_Recommender System/
│
├── data/
│   └── tmdb_5000_movies.csv
│
├── model/
│   ├── movie_list.pkl
│   └── movie_meta.pkl
│
├── static/
│   ├── no-poster.svg
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── app.py
├── build_model.py
├── requirements.txt
├── README.md
└── .gitignore
```

> **Note:** The generated `similarity.pkl` file is intentionally excluded from GitHub because of GitHub's individual file-size limit. It can be generated locally using the model-building workflow.

---

## 📊 Dataset

This project uses the **TMDB 5000 Movies Dataset**.

The dataset contains information such as:

- Movie title
- Genres
- Keywords
- Cast
- Crew
- Overview
- Popularity
- Release information

The dataset is stored inside:

```text
data/tmdb_5000_movies.csv
```

---

## ⚙️ How It Works

### 1. Data Preprocessing

Movie metadata is cleaned and transformed into useful features.

### 2. Feature Engineering

Relevant movie attributes are combined to create a consolidated representation of each movie.

### 3. Vectorization

The textual movie features are converted into numerical vectors.

### 4. Similarity Calculation

**Cosine Similarity** is used to measure similarity between movie vectors.

### 5. Recommendation

When a user selects a movie, the system finds movies with the highest similarity scores and returns recommendations.

### 6. Flask Integration

The trained recommendation components are loaded into the Flask backend and connected to the frontend.

---

## 💻 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/KashifAshfaque/MachineLearning-Project.git
```

### 2. Navigate to the Project

```bash
cd MachineLearning-Project/"Movies_Recommender System"
```

### 3. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 4. Activate the Environment

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the Flask server:

```bash
python3 app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## 🔄 Model Generation

The project includes:

```text
build_model.py
```

This script is responsible for preparing the recommendation model and generating the required model artifacts.

The large generated similarity matrix is not stored in GitHub due to its file size.

---

## 🔐 Environment Variables

API credentials and sensitive configuration should be stored in a `.env` file.

The `.env` file is excluded from Git using `.gitignore`.

Example:

```text
API_KEY=your_api_key_here
```

Never commit real API keys or secrets to GitHub.

---

## 📈 Future Improvements

- Add user-based personalized recommendations
- Improve recommendation ranking
- Add movie ratings
- Add genre-based filtering
- Add recommendation history
- Deploy the application using a cloud platform
- Improve mobile responsiveness
- Add automated model rebuilding

---

## 🎯 Learning Outcomes

Through this project, the following concepts were implemented:

- Data preprocessing
- Feature engineering
- Natural Language Processing concepts
- Text vectorization
- Cosine similarity
- Content-based recommendation systems
- Flask backend development
- REST-style application integration
- Frontend and backend integration
- Git and GitHub project management

---

## 👨‍💻 Author

**Kashif Ashfaque**

Computer Science Engineering Student

GitHub: [KashifAshfaque](https://github.com/KashifAshfaque)