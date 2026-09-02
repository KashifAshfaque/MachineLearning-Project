import streamlit as st
import pandas as pd
import os
from difflib import get_close_matches
from datetime import datetime

st.set_page_config(page_title="Vaultline — Banking Support", layout="wide", page_icon="🏦")

# ---------- Load data safely ----------
CSV_PATH = "banking_support.csv"

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error(f"'{CSV_PATH}' file nahi mili. Isi folder me CSV file rakho (columns: question, response).")
    st.stop()

# ---------- Session state ----------
if "question" not in st.session_state:
    st.session_state.question = ""
if "response" not in st.session_state:
    st.session_state.response = ""
if "matched" not in st.session_state:
    st.session_state.matched = None
if "ledger" not in st.session_state:
    st.session_state.ledger = []   # history of Q&A, like passbook entries

def resolve(text):
    questions = df["question"].tolist()
    match = get_close_matches(text, questions, n=1, cutoff=0.4)
    if match:
        ans = df[df["question"] == match[0]]["response"].values[0]
        st.session_state.response = ans
        st.session_state.matched = True
        st.session_state.ledger.insert(0, {
            "q": text, "a": ans, "t": datetime.now().strftime("%H:%M")
        })
    else:
        st.session_state.response = "No entry found for this query. Try rephrasing, or pick an example below."
        st.session_state.matched = False
        st.session_state.ledger.insert(0, {
            "q": text, "a": "Unresolved — no match found.", "t": datetime.now().strftime("%H:%M")
        })

def set_question(text):
    st.session_state.question = text
    resolve(text)

def clear_all():
    st.session_state.question = ""
    st.session_state.response = ""
    st.session_state.matched = None

# ================= STYLING =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root{
    --navy:#0B1620;
    --navy-panel:#101F2D;
    --hairline:#21333F;
    --gold:#D4A24C;
    --gold-soft:#3A331F;
    --ink:#EAE6DD;
    --ink-dim:#8FA3AE;
    --green:#5FAE7E;
}

.stApp{
    background: radial-gradient(circle at 20% 0%, #0E1F2C 0%, var(--navy) 55%);
    color: var(--ink);
}
[data-testid="stHeader"]{background: transparent;}
.block-container{padding-top:2.5rem; max-width:1180px;}

/* ---- Hero ---- */
.eyebrow{
    font-family:'IBM Plex Mono', monospace;
    letter-spacing:.18em;
    text-transform:uppercase;
    font-size:12px;
    color:var(--gold);
    display:flex;
    align-items:center;
    gap:10px;
    margin-bottom:14px;
}
.eyebrow::before{
    content:"";
    width:7px;height:7px;border-radius:50%;
    background:var(--green);
    box-shadow:0 0 0 3px rgba(95,174,126,0.18);
}
.hero-title{
    font-family:'Fraunces', serif;
    font-weight:600;
    font-size:46px;
    line-height:1.08;
    color:var(--ink);
    margin-bottom:10px;
    letter-spacing:-0.01em;
}
.hero-title em{
    color:var(--gold);
    font-style:normal;
}
.hero-sub{
    font-family:'Inter', sans-serif;
    font-size:16px;
    color:var(--ink-dim);
    max-width:620px;
    line-height:1.55;
    margin-bottom:34px;
    border-left:2px solid var(--hairline);
    padding-left:16px;
}

/* ---- Panels ---- */
.panel-label{
    font-family:'IBM Plex Mono', monospace;
    font-size:11px;
    letter-spacing:.14em;
    text-transform:uppercase;
    color:var(--ink-dim);
    margin-bottom:10px;
    display:flex;
    justify-content:space-between;
}
.panel-label span.tag{color:var(--gold);}

div[data-testid="stTextInput"] > div{
    height:58px;
}
div[data-testid="stTextInput"] input{
    background:var(--navy-panel) !important;
    color:var(--ink) !important;
    border:1px solid var(--hairline) !important;
    border-radius:6px !important;
    height:58px !important;
    box-sizing:border-box;
    font-family:'Inter', sans-serif;
    font-size:15.5px;
    line-height:normal;
    padding:0 18px !important;
}
div[data-testid="stTextInput"] input::placeholder{ color:#5A6E79; }
div[data-testid="stTextInput"] input:focus{
    border-color:var(--gold) !important;
    box-shadow:0 0 0 1px var(--gold) !important;
}

/* Response / ledger card */
.ledger-card{
    background:var(--navy-panel);
    border:1px solid var(--hairline);
    border-radius:6px;
    padding:20px 20px 16px 20px;
    min-height:58px;
    font-family:'Inter', sans-serif;
    font-size:15px;
    line-height:1.6;
    color:var(--ink);
    position:relative;
}
.ledger-card.empty{ color:#5A6E79; font-style:italic; }
.ledger-card.resolved{ border-left:3px solid var(--green); }
.ledger-card.unresolved{ border-left:3px solid #B9613F; }
.ledger-status{
    font-family:'IBM Plex Mono', monospace;
    font-size:10.5px;
    letter-spacing:.1em;
    text-transform:uppercase;
    color:var(--green);
    margin-bottom:8px;
    display:block;
}
.ledger-status.bad{ color:#D98A6B; }

/* Buttons */
div.stButton > button{
    width:100%;
    height:50px;
    font-family:'Inter', sans-serif;
    font-weight:600;
    font-size:14.5px;
    border-radius:6px;
    border:1px solid var(--hairline);
    background:transparent;
    color:var(--ink-dim);
    transition:all .15s ease;
}
div.stButton > button:hover{
    border-color:var(--ink-dim);
    color:var(--ink);
}
div.stButton > button[kind="primary"]{
    background:var(--gold);
    border:none;
    color:#1A1304;
    letter-spacing:.02em;
}
div.stButton > button[kind="primary"]:hover{
    background:#E3B468;
    color:#1A1304;
}

/* Example chips */
.section-tag{
    font-family:'IBM Plex Mono', monospace;
    font-size:11px;
    letter-spacing:.14em;
    text-transform:uppercase;
    color:var(--ink-dim);
    margin:38px 0 14px 0;
    display:flex; align-items:center; gap:10px;
}
.section-tag::after{
    content:"";
    flex:1;
    height:1px;
    background:var(--hairline);
}
.example-btn div.stButton > button{
    text-align:left;
    padding-left:16px;
    background:rgba(212,162,76,0.04);
    font-weight:400;
    color:var(--ink-dim);
    font-size:14px;
}
.example-btn div.stButton > button:hover{
    background:rgba(212,162,76,0.09);
    border-color:var(--gold);
    color:var(--ink);
}

/* Ledger history */
.history-row{
    display:flex;
    gap:14px;
    padding:12px 0;
    border-bottom:1px solid var(--hairline);
    font-family:'Inter', sans-serif;
}
.history-time{
    font-family:'IBM Plex Mono', monospace;
    font-size:12px;
    color:var(--ink-dim);
    width:50px;
    flex-shrink:0;
    padding-top:2px;
}
.history-q{ font-size:14px; color:var(--ink); font-weight:500; }

footer, [data-testid="stStatusWidget"]{ visibility:hidden; }
hr{ border-color:var(--hairline) !important; }
</style>
""", unsafe_allow_html=True)

# ================= HERO =================
st.markdown('<div class="eyebrow">24×7 · ALL BRANCHES · INSTANT RESOLUTION</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Banking support,<br>answered like a <em>ledger entry.</em></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Ask anything about your account, card, UPI, loan or KYC. '
    'Every answer is logged below like a passbook entry — clear, timestamped, and ready to act on.</div>',
    unsafe_allow_html=True
)

# ================= INPUT / RESPONSE =================
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="panel-label">YOUR QUERY <span class="tag">01</span></div>', unsafe_allow_html=True)
    question = st.text_input(
        "",
        value=st.session_state.question,
        placeholder="e.g. My account is locked, what should I do?",
        label_visibility="collapsed",
        key="question_input"
    )

with col2:
    status_html = ""
    card_class = "ledger-card empty"
    body = "Awaiting query — your resolution will appear here."

    if st.session_state.matched is True:
        card_class = "ledger-card resolved"
        status_html = '<span class="ledger-status">✓ MATCH FOUND</span>'
        body = st.session_state.response
    elif st.session_state.matched is False:
        card_class = "ledger-card unresolved"
        status_html = '<span class="ledger-status bad">✕ NO MATCH</span>'
        body = st.session_state.response

    st.markdown('<div class="panel-label">RESOLUTION <span class="tag">02</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="{card_class}">{status_html}{body}</div>', unsafe_allow_html=True)

st.write("")

# ================= ACTIONS =================
b1, b2, b3 = st.columns(3)
with b1:
    if st.button("Clear", use_container_width=True):
        clear_all()
        st.rerun()
with b2:
    if st.button("Submit query", type="primary", use_container_width=True):
        if question.strip():
            st.session_state.question = question
            resolve(question)
        st.rerun()
with b3:
    if st.button("Flag this answer", use_container_width=True):
        st.toast("Logged for review. Thank you.")

# ================= EXAMPLES =================
st.markdown('<div class="section-tag">COMMON QUERIES</div>', unsafe_allow_html=True)

examples = [
    "My account is locked, what should I do?",
    "How can I transfer money to another account?",
    "My debit card got declined at the shop.",
    "UPI transaction failed what to do?",
]

ex_col1, ex_col2 = st.columns(2)
ex_col3, ex_col4 = st.columns(2)
cols = [ex_col1, ex_col2, ex_col3, ex_col4]

for col, ex in zip(cols, examples):
    with col:
        st.markdown('<div class="example-btn">', unsafe_allow_html=True)
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            set_question(ex)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ================= LEDGER HISTORY =================
if st.session_state.ledger:
    st.markdown('<div class="section-tag">RECENT ACTIVITY</div>', unsafe_allow_html=True)
    for entry in st.session_state.ledger[:6]:
        st.markdown(f"""
        <div class="history-row">
            <div class="history-time">{entry['t']}</div>
            <div class="history-q">{entry['q']}</div>
        </div>
        """, unsafe_allow_html=True)