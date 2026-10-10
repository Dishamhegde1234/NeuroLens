# 🧠 NeuroLens

**AI-powered learning difficulty predictor for C programming.**
Find weak topics early, practise smarter.

NeuroLens is a Flask web app that watches how a student answers C programming
questions, estimates a **risk score for every topic**, and turns it into focused practice.
It was built for the **CBC 2.0 Hackathon** (Problem PS-34, domain AI-ML).

> Overall marks hide topic-level weaknesses. A student can keep missing pointer questions
> and never know that *pointers* is the topic to fix. NeuroLens shows that, early.

## Features

- **Topic-wise risk** across 8 levels and 46 topics, from *C Fundamentals* to *File handling*.
- **Difficulty-aware**: missing an easy question says more about a gap than missing a hard one.
- **Recurring-weakness detection**: repeated misses matter, one wrong answer does not.
- **Explainable**: every score comes with its reasons, attempt history and a confidence level.
- **Adaptive practice**: questions are picked to match your current risk and never repeat until
  the whole topic has been covered. Each level has a mixed *Proficiency Assessment*.
- **Updates after every answer**, with XP, levels, streaks and badges.
- **Study habits that start at zero**: attendance and study time grow as you practise.
- **Accounts**: sign up / log in with hashed passwords and server-side sessions.
- **Light and dark themes**, responsive layout with a mobile menu.
- **Optional**: "Explain with AI" (Gemini or OpenAI), an ML risk engine, and a Streamlit educator view.

## Tech stack

| Layer | Used here |
|---|---|
| Design | Claude, Figma |
| Frontend | HTML, CSS, vanilla JavaScript served by Flask · Streamlit for the educator dashboard |
| Backend | Python, Flask |
| Database | SQLite (Supabase/Postgres schema included, see below) |
| AI / APIs | Gemini or OpenAI for explanations · scikit-learn for the optional ML engine |

## Quick start

```bash
git clone https://github.com/<your-username>/neurolens.git
cd neurolens

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# put a real SECRET_KEY in .env (the command is inside the file)

flask --app neurolens run          # http://127.0.0.1:5000
```

Open the site, sign up, or press **Try the demo as Asha** for a student with existing history.
The database file is created automatically at `instance/neurolens.db`.

Run the tests:

```bash
python -m unittest discover -s tests -t . -v
```

### Production

```bash
SECRET_KEY=... SESSION_COOKIE_SECURE=1 gunicorn wsgi:app
```

Serve it behind HTTPS. Note that the login throttle is kept in memory per process, so with several
gunicorn workers each worker counts separately.

## How the risk score works

For every topic, the attempts are `(difficulty, correct)` pairs, oldest first.

```
risk = 0.60 × weighted miss rate
     + 0.25 × recurrence          (wrong answers among the last 5, capped at 3)
     + 0.15 × worsening trend     (second half of the history worse than the first)
     + 0.04 if attendance < 75%
```

- **Weighted miss rate**: each answer's weight is `0.85^(age)` × a difficulty weight
  (easy 1.3, medium 1.0, hard 0.7), so recent answers and easy misses count more.
- **Smoothing**: the miss rate is pulled toward a neutral 40% prior, so one answer never decides.
- **Confidence**: `n / (n + 4)`. New topics show as low-confidence baselines.
- **Tiers**: ≥ 55% high, ≥ 38% medium, otherwise low. A topic counts as *mastered* with at least 4 attempts and low risk.

The code is in [`neurolens/risk_model.py`](neurolens/risk_model.py) and is covered by unit tests.

### Optional ML engine

```bash
pip install -r requirements-ml.txt
python train_model.py                       # writes models/miss_model.joblib
RISK_ENGINE=ml flask --app neurolens run
```

This trains a logistic regression that predicts the chance the *next* answer in a topic is wrong,
and blends it 50/50 with the heuristic. **It is trained on simulated students**, because this repo ships
no real student data (held-out AUC on the simulation is about 0.69, so treat it as a demo). Replace
`simulate()` in `train_model.py` with a query over your `attempts` table to train on real data.

### Optional AI explanations

Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` and an **Explain with AI** button appears after each
answer. Model names are configurable (`GEMINI_MODEL`, `OPENAI_MODEL`) because providers retire models,
so check their docs for current names. Keys stay on the server and are never sent to the browser.

### Educator view (Streamlit)

```bash
pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

Shows one student's risk by topic and the topics the whole class struggles with. It has no login of its
own, so run it on a trusted network only.

## Project structure

```
neurolens/
├── neurolens/
│   ├── __init__.py        app factory, security headers, CLI
│   ├── api.py             JSON API (auth, dashboard, questions, answers)
│   ├── services.py        dashboard data, adaptive question flow, demo account
│   ├── risk_model.py      the explainable risk score (+ ML feature code)
│   ├── questions.py       question bank and picking logic
│   ├── ai_helper.py       Gemini / OpenAI explanations
│   ├── db.py              all SQL (SQLite)
│   ├── config.py          settings from environment variables
│   ├── data/              curriculum.json, questions.json, demo_seed.json
│   ├── templates/         index.html
│   └── static/            css/style.css, js/app.js
├── tests/                 35 unit tests
├── train_model.py         optional ML training
├── streamlit_app.py       optional educator dashboard
├── supabase_schema.sql    Postgres version of the tables
├── wsgi.py                gunicorn entry point
└── requirements*.txt
```

## API

All endpoints return JSON. Everything except sign-up, log-in and demo needs a signed-in session.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/signup` | `{name, email, password}`, creates an account and signs in |
| POST | `/api/login` | `{email, password}` |
| POST | `/api/demo` | temporary demo student with history |
| POST | `/api/logout` | |
| GET | `/api/dashboard` | stats, habits, badges, and every topic with its risk |
| GET | `/api/topic/<key>` | why a topic has its score |
| GET | `/api/question?topic=KEY` or `?level=L1` | next question (never includes the answer) |
| POST | `/api/answer` | `{qid, choice}`, records it and returns the new risk |
| POST | `/api/explain` | `{qid, choice}`, AI explanation (needs a key) |

## Adding questions or topics

Questions live in `neurolens/data/questions.json` as
`{"id", "topic", "difficulty" (1-3), "text", "options" (4), "answer" (index 0-3)}`.
Topics and levels live in `curriculum.json`. No code changes are needed; the tests check that
every question is well-formed. **Please re-verify answers before using this for real teaching.**
Levels 3 to 8 currently have only 3 questions per topic.

## Using Supabase instead of SQLite

SQLite is the only backend implemented. All SQL is in `neurolens/db.py`, and
`supabase_schema.sql` has the matching Postgres tables. To switch, reimplement the functions in
`db.py` with a Postgres driver (for example `psycopg`) and keep the rest of the app unchanged.

## Security notes

- Passwords are hashed with Werkzeug (scrypt/PBKDF2), never stored in plain text.
- Sessions use HttpOnly, SameSite=Lax cookies. Set `SESSION_COOKIE_SECURE=1` behind HTTPS.
- The browser never receives correct answers before submitting.
- The API only accepts JSON bodies; there is no CSRF token, so keep SameSite cookies on and serve from one origin.
- Dates and attendance use UTC.
- Demo accounts are throwaway and cleaned up after 24 hours.

## Limitations and roadmap

- Attendance means "days you practised since signing up", and study time is estimated at 1.5 minutes per answer.
- Only C programming content is included.
- Ideas: teacher accounts, spaced repetition, real training data for the ML engine, Supabase backend, more questions per topic.

## Team

**ORACLEX** · Team ID CBC098 · Domain AI-ML · CBC 2.0 Hackathon
Eshani K, Disha M Hegde, Ananya S R, G S Bhavana Patil
3rd Sem, Global Academy of Technology

## License

MIT, see [LICENSE](LICENSE).
