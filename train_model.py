"""Train the optional ML risk model.

It learns P(next answer in a topic is wrong) from a student's history so far.
No real student data ships with this repo, so by default it trains on
*simulated* students (each has a hidden skill; harder questions are missed
more often). Swap `simulate()` for a query over your own `attempts` table
once you have real data.

    python train_model.py
    RISK_ENGINE=ml flask --app neurolens run
"""
import os

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from neurolens.risk_model import FEATURE_NAMES, features

OUT = os.environ.get("MODEL_PATH", os.path.join("models", "miss_model.joblib"))


def simulate(n_students=6000, seed=42):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for _ in range(n_students):
        skill = rng.beta(2, 2)
        history = []
        for _step in range(rng.integers(4, 16)):
            d = int(rng.integers(1, 4))
            p_correct = float(np.clip(skill - 0.15 * (d - 1) + rng.normal(0, 0.08), 0.05, 0.95))
            correct = int(rng.random() < p_correct)
            if len(history) >= 3:                      # predict this answer from the history before it
                X.append(features(history))
                y.append(1 - correct)
            history.append((d, correct))
    return np.array(X), np.array(y)


def main():
    X, y = simulate()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    model = LogisticRegression(max_iter=1000).fit(X_tr, y_tr)
    auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    joblib.dump(model, OUT)
    print(f"Trained on {len(X_tr)} samples, held-out AUC = {auc:.3f}")
    print("Features:", ", ".join(FEATURE_NAMES))
    print("Saved to", OUT)


if __name__ == "__main__":
    main()
