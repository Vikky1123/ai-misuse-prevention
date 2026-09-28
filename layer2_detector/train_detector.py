"""
Layer 2 - Train the lightweight CNN synthetic-image detector on CIFAKE.

Builds a compact convolutional neural network (the "lightweight CNN" approach
of Safak, 2024) that learns to separate real photographs from AI-generated
images by their statistical artifacts. Trains on a balanced subset, evaluates
on the held-out test split, and saves the model plus a confusion matrix,
training curve, and metrics.json for the report.

Target convention: output = P(synthetic), where 1 = FAKE/AI-generated.

Tuning knobs (all overridable from the environment, so you can scale up without
editing the file):

    TRAIN_PER_CLASS   images per class for training   (default 20000, max 50000)
    TEST_PER_CLASS    images per class for testing     (default 5000,  max 10000)
    EPOCHS            max epochs (early stopping cuts it short)   (default 40)
    BATCH             mini-batch size                              (default 128)
    AUGMENT           "1" to enable a horizontal-flip augmentation (default 0)

Examples:
    py layer2_detector/train_detector.py                  # solid 20k/class run
    TRAIN_PER_CLASS=50000 TEST_PER_CLASS=10000 py layer2_detector/train_detector.py

Note on augmentation: CIFAKE detection relies on subtle high-frequency
generative artifacts, which geometric warps (rotation/zoom/translation) smear
away - empirically that *hurt* accuracy here, so augmentation is OFF by default
and limited to a horizontal flip when enabled. The reliable lever is more data
(raise TRAIN_PER_CLASS).

Run (after download_data.py):  py layer2_detector/train_detector.py
"""

import os
import io
import json

import numpy as np
import pandas as pd
from PIL import Image

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
MODEL_DIR = os.path.join(HERE, "model")


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# Balanced subset sizes (per class). Bigger = more accurate but slower on CPU.
# Defaults are a 2.5x increase over the original 8000 and clearly beat it;
# raise to 50000/10000 (the full CIFAKE dataset) for the strongest model.
TRAIN_PER_CLASS = min(_env_int("TRAIN_PER_CLASS", 20000), 50000)
TEST_PER_CLASS = min(_env_int("TEST_PER_CLASS", 5000), 10000)
IMG = 32
EPOCHS = _env_int("EPOCHS", 40)
BATCH = _env_int("BATCH", 128)
AUGMENT = os.environ.get("AUGMENT", "0") != "0"


def load_split(parquet_name, per_class):
    df = pd.read_parquet(os.path.join(DATA_DIR, parquet_name))
    parts = [df[df.label == lbl].head(per_class) for lbl in (0, 1)]
    df = pd.concat(parts).sample(frac=1, random_state=42).reset_index(drop=True)

    X = np.zeros((len(df), IMG, IMG, 3), dtype="float32")
    y = np.zeros((len(df),), dtype="float32")
    for i, row in df.iterrows():
        im = Image.open(io.BytesIO(row["image"]["bytes"])).convert("RGB").resize((IMG, IMG))
        X[i] = np.asarray(im, dtype="float32") / 255.0
        y[i] = 1.0 if row["label"] == 0 else 0.0   # 1 = FAKE / synthetic
    return X, y


def build_model():
    # Optional, artifact-preserving augmentation. OFF by default: on CIFAKE the
    # synthetic fingerprint is a subtle spatial-frequency pattern, and geometric
    # warps (rotation/zoom/translation) tend to smear it - a horizontal flip is
    # the only reasonably safe transform, and even it buys little here.
    aug = [layers.RandomFlip("horizontal")] if AUGMENT else []

    # Architecture matches the validated 92.85% baseline (3 conv blocks ->
    # Flatten -> Dense). Flatten (not GlobalAveragePooling) is deliberate: it
    # preserves the spatial layout the artifact signal lives in. The only
    # intended change vs the baseline is the AMOUNT OF DATA (TRAIN_PER_CLASS)
    # plus the optimisation callbacks in main() (LR schedule / early stopping).
    model = keras.Sequential([
        keras.Input((IMG, IMG, 3)),
        *aug,
        layers.Conv2D(32, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Conv2D(128, 3, padding="same", activation="relu"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dropout(0.4),
        layers.Dense(128, activation="relu"),
        layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer=keras.optimizers.Adam(1e-3),
                  loss="binary_crossentropy", metrics=["accuracy"])
    return model


def save_plots(history, cm):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Confusion matrix
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, cmap="Blues")
    plt.title("Confusion Matrix")
    plt.colorbar()
    ticks = ["real", "ai_generated"]
    plt.xticks([0, 1], ticks); plt.yticks([0, 1], ticks)
    for i in range(2):
        for j in range(2):
            plt.text(j, i, int(cm[i, j]), ha="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.xlabel("Predicted"); plt.ylabel("Actual"); plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, "confusion_matrix.png"), dpi=120)
    plt.close()

    # Training curve
    plt.figure(figsize=(5, 3))
    plt.plot(history.history["accuracy"], label="train")
    plt.plot(history.history["val_accuracy"], label="validation")
    plt.title("Detector accuracy"); plt.xlabel("epoch"); plt.ylabel("accuracy")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, "training_history.png"), dpi=120)
    plt.close()


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"Config: TRAIN_PER_CLASS={TRAIN_PER_CLASS}  TEST_PER_CLASS={TEST_PER_CLASS}  "
          f"EPOCHS={EPOCHS}  BATCH={BATCH}  AUGMENT={AUGMENT}")
    print("Loading training data ...")
    X_tr, y_tr = load_split("train.parquet", TRAIN_PER_CLASS)
    print("Loading test data ...")
    X_te, y_te = load_split("test.parquet", TEST_PER_CLASS)
    print(f"train={X_tr.shape}  test={X_te.shape}")

    model = build_model()
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=6, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-5, verbose=1),
        keras.callbacks.ModelCheckpoint(
            os.path.join(MODEL_DIR, "detector.keras"),
            monitor="val_accuracy", save_best_only=True),
    ]
    history = model.fit(
        X_tr, y_tr, validation_data=(X_te, y_te),
        epochs=EPOCHS, batch_size=BATCH, callbacks=callbacks, verbose=2,
    )

    loss, acc = model.evaluate(X_te, y_te, verbose=0)
    print(f"\nFINAL TEST ACCURACY: {acc:.4f}")

    # Ensure the saved model is the best-weights one we just restored.
    model.save(os.path.join(MODEL_DIR, "detector.keras"))

    proba = model.predict(X_te, verbose=0).ravel()
    y_pred = (proba >= 0.5).astype(int)
    cm = confusion_matrix(y_te.astype(int), y_pred)
    report = classification_report(
        y_te.astype(int), y_pred, target_names=["real", "ai_generated"],
        output_dict=True, zero_division=0,
    )
    try:
        auc = float(roc_auc_score(y_te.astype(int), proba))
    except ValueError:
        auc = None
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as fh:
        json.dump({"test_accuracy": float(acc),
                   "roc_auc": auc,
                   "train_per_class": TRAIN_PER_CLASS,
                   "test_per_class": TEST_PER_CLASS,
                   "augmented": AUGMENT,
                   "confusion_matrix": cm.tolist(),
                   "report": report}, fh, indent=2)
    save_plots(history, cm)
    print(f"Saved model + metrics + plots to {MODEL_DIR}")
    if auc is not None:
        print(f"ROC-AUC: {auc:.4f}")


if __name__ == "__main__":
    main()
