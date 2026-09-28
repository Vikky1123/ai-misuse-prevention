"""
Layer 1 - Train the pre-generation semantic prompt filter.

Trains a TF-IDF + Logistic Regression classifier on data/prompts.csv to
distinguish harmful (adversarial / NCII / jailbreak) prompts from benign ones.
TF-IDF with word bigrams lets the model learn *phrase-level patterns*
(e.g. "remove her clothes", "ignore your instructions") rather than single
banned keywords - this is the "semantic, not keyword" property the seminar
argues for (Kumar et al., 2023; Zhao et al., 2024).

Run:  py layer1_filter/train_filter.py
"""

import os
import json

import pandas as pd
import joblib
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data", "prompts.csv")
MODEL_PATH = os.path.join(HERE, "model.joblib")
METRICS_PATH = os.path.join(HERE, "metrics.json")


def build_pipeline():
    """Word features (phrase patterns) + character features (robustness).

    Two complementary TF-IDF views are concatenated with a FeatureUnion:

      * WORD  unigrams+bigrams - learns phrase-level patterns like
        "remove her clothes" / "ignore your instructions" (the "semantic, not
        keyword" property the seminar argues for).
      * CHAR  char_wb 3-5 grams - learns sub-word shapes, so the filter still
        fires on light obfuscation / typos the word view would miss
        ("un-dress", "n4ked", "nudify", "deepfakenude").
    """
    word = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
        lowercase=True,
        strip_accents="unicode",
    )
    char = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        sublinear_tf=True,
        lowercase=True,
        strip_accents="unicode",
    )
    return Pipeline(
        [
            ("features", FeatureUnion([("word", word), ("char", char)])),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    C=4.0,                 # a touch less regularisation for the
                    class_weight="balanced",  # larger, sparser feature space
                ),
            ),
        ]
    )


def main():
    df = pd.read_csv(DATA_PATH)
    X, y = df["text"], df["label"]
    print(f"Loaded {len(df)} labelled prompts "
          f"({(y == 'harmful').sum()} harmful, {(y == 'safe').sum()} safe)")
    if "category" in df.columns:
        print("Category breakdown:")
        for cat, n in df["category"].value_counts().sort_index().items():
            print(f"    {cat:24s} {n}")

    pipe = build_pipeline()

    # 5-fold cross-validation for an honest accuracy estimate.
    scores = cross_val_score(pipe, X, y, cv=5)
    print(f"5-fold CV accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")

    # Held-out report.
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    pipe.fit(X_tr, y_tr)
    y_pred = pipe.predict(X_te)
    print("\nHeld-out test report:")
    print(classification_report(y_te, y_pred))

    metrics = {
        "cv_mean": float(scores.mean()),
        "cv_std": float(scores.std()),
        "holdout_accuracy": float(accuracy_score(y_te, y_pred)),
        "n_total": int(len(df)),
        "n_harmful": int((y == "harmful").sum()),
        "n_safe": int((y == "safe").sum()),
        "report": classification_report(y_te, y_pred, output_dict=True, zero_division=0),
    }
    if "category" in df.columns:
        metrics["categories"] = {str(k): int(v)
                                 for k, v in df["category"].value_counts().items()}
    with open(METRICS_PATH, "w") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"Saved filter metrics to: {METRICS_PATH}")

    # Refit on ALL data and save for deployment.
    pipe.fit(X, y)
    joblib.dump(pipe, MODEL_PATH)
    print(f"Saved trained filter to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
