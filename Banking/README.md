# 🏦 Vaultline — Banking Support Chatbot

### 🔗 [**Live Demo →**](https://vaultline-banking-chatbot-2ikwtf3bzdbuzfodsjb9ap.streamlit.app)

A clean, instant-answer support chatbot for common banking queries — account access, cards, UPI, loans, and KYC — built with **Streamlit** and styled with a custom dark "ledger" theme.

> Ask a question in plain English (or Hinglish), get an instant matched answer from a knowledge base — no API keys, no LLM calls, fully offline and self-contained.

---

## ✨ Features

- 🔍 **Fuzzy question matching** — understands rephrased or loosely-worded questions using Python's built-in `difflib`
- 🎨 **Custom designed UI** — navy & gold "ledger" theme, not the default Streamlit look
- 📝 **Live activity log** — every query you ask is logged with a timestamp, like a passbook entry
- ⚡ **One-click example queries** — common questions are clickable chips for instant answers
- 🧩 **Easily extensible** — add new Q&A pairs by editing a single CSV file, no code changes needed
- 🚫 **No external API / no internet required** — runs 100% locally

---

## 📸 Preview

| Home | Resolved Query |
|---|---|
| _Add a screenshot here_ | _Add a screenshot here_ |

> 💡 Tip: After running the app, take a screenshot and drop it into a `/screenshots` folder, then update the links above like:
> `![Home](screenshots/home.png)`

---

## 🛠️ Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [Pandas](https://pandas.pydata.org/) — knowledge base handling
- Python `difflib` — fuzzy text matching
- Custom CSS — Fraunces, Inter & IBM Plex Mono fonts

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/vaultline-banking-chatbot.git
cd vaultline-banking-chatbot
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

The app will open automatically at **http://localhost:8501**

---

## 📂 Project Structure

```
vaultline-banking-chatbot/
├── app.py                  # Main Streamlit application
├── banking_support.csv     # Knowledge base (question/response pairs)
├── requirements.txt        # Python dependencies
├── .gitignore
├── LICENSE
└── README.md
```

---

## 📝 Adding New Questions

The chatbot's knowledge base is just a CSV file with two columns: `question` and `response`.

```csv
question,response
How do I report a fraud transaction?,"Call our 24x7 fraud helpline immediately and freeze your card via the app under 'Card Services' > 'Block Card'."
```

Add a new row to `banking_support.csv`, save, and the chatbot will pick it up on the next run — no code changes required.

---

## 🗺️ Roadmap

- [ ] Add multi-language support (Hindi / Hinglish queries)
- [ ] Connect to a real LLM backend for open-ended queries
- [ ] Add voice input support
- [ ] Deploy live demo on Streamlit Community Cloud

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](../../issues) or open a pull request.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with ❤️ using Streamlit</p>
