"""
Layer 2 - CNN Synthetic-Artifact Detector (runtime / OUTPUT GUARD).

Examines an image and estimates the probability that it is AI-generated
(synthetic) rather than a real photograph, by detecting the statistical
artifacts that diffusion / GAN pipelines leave behind (Safak, 2024;
Zhang et al., 2024). This is the system's secondary line of defence for
content that slips past the Layer 1 prompt filter.

Two paths:
  * "cnn"       - a trained lightweight CNN (model/detector.keras). PRIMARY.
  * "heuristic" - an FFT high-frequency-energy proxy used only if TensorFlow
                  or the trained model is missing, so the system still runs.
The active mode is always reported in the result.
"""

import os
import io

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "model", "detector.keras")
INPUT_SIZE = (32, 32)          # CIFAKE native size
FLAG_THRESHOLD = 0.50          # P(synthetic) >= this -> flagged as AI-generated


class ArtifactDetector:
    """Estimates whether an image is AI-generated."""

    def __init__(self, threshold=FLAG_THRESHOLD):
        self.model = None
        self.mode = "heuristic"
        self.threshold = threshold

    def load(self):
        """Load the trained CNN if present; otherwise stay in heuristic mode."""
        if os.path.exists(MODEL_PATH):
            try:
                os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
                from tensorflow import keras
                self.model = keras.models.load_model(MODEL_PATH)
                self.mode = "cnn"
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[Layer 2] CNN unavailable ({exc}); using heuristic fallback")
                self.model, self.mode = None, "heuristic"
        else:
            self.mode = "heuristic"
        return self

    @property
    def model_ready(self):
        return self.model is not None

    # --- image loading (accepts path, PIL image, bytes, or file-like) ---
    def _load_image(self, image):
        if isinstance(image, str):
            with Image.open(image) as raw:
                return raw.convert("RGB")
        elif isinstance(image, Image.Image):
            return image.convert("RGB")
        else:
            data = image.read() if hasattr(image, "read") else image
            with Image.open(io.BytesIO(data)) as raw:
                return raw.convert("RGB")

    # --- CNN path ---
    def _cnn_score(self, im):
        arr = np.asarray(im.resize(INPUT_SIZE), dtype="float32") / 255.0
        arr = arr.reshape(1, INPUT_SIZE[1], INPUT_SIZE[0], 3)
        return float(self.model.predict(arr, verbose=0)[0][0])  # P(synthetic)

    # --- Heuristic fallback path ---
    def _heuristic_score(self, im):
        """FFT-based proxy: synthetic images tend to show abnormal high-frequency
        spectral energy. Returns a rough 0..1 synthetic-likelihood."""
        g = np.asarray(im.convert("L").resize((128, 128)), dtype="float32")
        spectrum = np.abs(np.fft.fftshift(np.fft.fft2(g)))
        cy, cx = 64, 64
        yy, xx = np.ogrid[:128, :128]
        radius = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        high = spectrum[radius > 40].mean()
        low = spectrum[radius <= 40].mean() + 1e-6
        ratio = high / low
        score = 1.0 / (1.0 + np.exp(-(ratio * 50.0 - 2.0)))
        return float(np.clip(score, 0.0, 1.0))

    def analyze(self, image):
        """Return a structured verdict for one image."""
        im = self._load_image(image)
        score = self._cnn_score(im) if self.model is not None else self._heuristic_score(im)
        label = "ai_generated" if score >= self.threshold else "real"
        confidence = score if label == "ai_generated" else 1.0 - score
        return {
            "label": label,
            "synthetic_probability": round(score, 4),
            "confidence": round(confidence, 4),
            "mode": self.mode,
            "threshold": self.threshold,
        }


# Quick manual test:  py layer2_detector/detector.py path/to/image.png
if __name__ == "__main__":
    import sys
    det = ArtifactDetector().load()
    print(f"detector mode: {det.mode}")
    if len(sys.argv) > 1:
        print(det.analyze(sys.argv[1]))
