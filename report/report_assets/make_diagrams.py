"""Generate diagrams for the Chapter 3 / Chapter 4 report."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

OUT = os.path.dirname(os.path.abspath(__file__))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved {path}")


# ---------- Figure 3.1 : Three-layer system architecture ----------
def architecture():
    fig, ax = plt.subplots(figsize=(9, 11))
    ax.set_xlim(0, 10); ax.set_ylim(0, 14); ax.axis("off")

    def box(x, y, w, h, text, fill, edge="#222", fs=10, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.15",
                                     linewidth=1.4, edgecolor=edge, facecolor=fill))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", wrap=True)

    def arrow(x1, y1, x2, y2, label=None, color="#222"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                                      linewidth=1.5, color=color))
        if label:
            ax.text((x1+x2)/2 + 0.15, (y1+y2)/2, label, fontsize=9, color=color, style="italic")

    # USER
    box(3.2, 13, 3.6, 0.8, "USER\nprompt (+ optional image)", "#fff7d6", fs=10, bold=True)

    # Layer 1
    box(1.5, 10.8, 7, 1.5,
        "LAYER 1  —  Pre-generation Semantic Filter (INPUT GUARD)\n"
        "TF-IDF (word + char n-grams) → Logistic Regression\n"
        "+ Transparent regex signal layer (5 harm categories)",
        "#d6e8ff", fs=10)
    arrow(5, 13, 5, 12.35)

    # branches from L1
    box(0.4, 9, 3.6, 1.1, "Image generation\n(SIMULATED)", "#e7f7d8", fs=10)
    box(6.0, 9, 3.6, 1.1, "Generation prevented\n(logged in Layer 3)", "#fde2e2", fs=10)
    arrow(3.5, 10.8, 2.2, 10.15, "allowed", color="#1b6e1b")
    arrow(6.5, 10.8, 7.8, 10.15, "blocked", color="#a52020")

    # Layer 2
    box(1.5, 6.7, 7, 1.6,
        "LAYER 2  —  CNN Synthetic-Artifact Detector  (OUTPUT GUARD)\n"
        "3 conv blocks (32/64/128) + BatchNorm + MaxPool → Flatten → Dropout → Dense → σ\n"
        "Returns P(synthetic). Fallback: FFT high-frequency heuristic",
        "#d6e8ff", fs=10)
    arrow(2.2, 9, 3.5, 8.35, "image", color="#1b6e1b")

    box(1.5, 4.8, 3.2, 1.0, "clean\n(real photo)", "#e7f7d8", fs=10)
    box(5.3, 4.8, 3.2, 1.0, "flagged\n(AI-generated)", "#fde2e2", fs=10)
    arrow(3.5, 6.7, 3.1, 5.85, color="#1b6e1b")
    arrow(6.5, 6.7, 6.9, 5.85, color="#a52020")

    # Layer 3
    box(1.5, 2.4, 7, 1.7,
        "LAYER 3  —  Governance, Severity & Human Review\n"
        "SQLite events table  →  severity bands  →  escalation\n"
        "Analyst dashboard · case page · performance page",
        "#e7d6ff", fs=10)
    arrow(3.1, 4.8, 3.5, 4.15)
    arrow(6.9, 4.8, 6.5, 4.15)
    arrow(7.8, 9, 7, 4.15)   # blocked → L3
    arrow(2.5, 4.8, 5, 4.15) # generic to L3 center

    # legend
    ax.text(5, 1.6, "Flow direction: USER → L1 → (generation) → L2 → L3",
            ha="center", fontsize=9, style="italic", color="#444")

    save(fig, "fig_3_1_architecture.png")


# ---------- Figure 3.2 : Process / data flow ----------
def dataflow():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis("off")

    def step(x, y, w, h, text, fill):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.1",
                                     linewidth=1.3, edgecolor="#222", facecolor=fill))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=9.5, wrap=True)

    def arrow(x1, y1, x2, y2, color="#222"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=15,
                                      linewidth=1.4, color=color))

    step(0.2, 4.7, 1.8, 1.0, "1. Validate\ninput\n(prompt/image)", "#fff7d6")
    step(2.3, 4.7, 1.8, 1.0, "2. Layer 1\nanalyze(prompt)\n→ verdict + score", "#d6e8ff")
    step(4.4, 4.7, 1.8, 1.0, "3. Severity +\nlog event\n(L3)", "#e7d6ff")
    step(6.5, 4.7, 1.8, 1.0, "4. Simulate\ngeneration\n(if allowed)", "#e7f7d8")
    step(8.6, 4.7, 2.0, 1.0, "5. Layer 2\nanalyze(image)\n→ P(synthetic)", "#d6e8ff")

    for x1, x2 in [(2.0, 2.3), (4.1, 4.4), (6.2, 6.5), (8.3, 8.6)]:
        arrow(x1, 5.2, x2, 5.2)

    # branch: blocked path
    step(4.4, 2.7, 1.8, 1.0, "generation\nprevented", "#fde2e2")
    arrow(5.3, 4.7, 5.3, 3.7, color="#a52020")
    ax.text(5.55, 4.2, "blocked", fontsize=9, style="italic", color="#a52020")

    # L3 logs again
    step(8.6, 2.7, 2.0, 1.0, "6. Log image\nevent (L3)\nseverity / review", "#e7d6ff")
    arrow(9.6, 4.7, 9.6, 3.7)

    # final outputs
    step(2.3, 0.7, 2.0, 1.2, "Analyst\nDashboard\n(/dashboard)", "#fff0d6")
    step(5.0, 0.7, 2.0, 1.2, "Case Page\n(/case/<id>)", "#fff0d6")
    step(7.7, 0.7, 2.3, 1.2, "Performance Page\n(/performance)", "#fff0d6")
    arrow(5.3, 2.7, 3.3, 1.9, color="#444")
    arrow(5.3, 2.7, 6.0, 1.9, color="#444")
    arrow(9.6, 2.7, 8.8, 1.9, color="#444")

    save(fig, "fig_3_2_dataflow.png")


# ---------- Figure 3.3 : Severity decision flow ----------
def severity():
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")

    def box(x, y, w, h, text, fill):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.12",
                                     linewidth=1.3, edgecolor="#222", facecolor=fill))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=10, wrap=True)

    def arrow(x1, y1, x2, y2, label=None, color="#222"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=15,
                                      linewidth=1.4, color=color))
        if label:
            ax.text((x1+x2)/2 + 0.1, (y1+y2)/2 + 0.05, label, fontsize=9,
                    color=color, style="italic")

    box(3.5, 5.8, 3, 0.9, "Input: risk_score + categories", "#fff7d6")

    box(3.5, 4.3, 3, 0.9, "Category override?", "#d6e8ff")
    arrow(5, 5.8, 5, 5.2)

    box(0.3, 2.6, 3.0, 0.9, "ncii or minor_safety\n+ score ≥ 0.40", "#fde2e2")
    box(6.7, 2.6, 3.0, 0.9, "impersonation or forgery\n+ score ≥ 0.40", "#fff0d6")
    arrow(4, 4.3, 1.8, 3.5, color="#a52020")
    arrow(6, 4.3, 8.2, 3.5, color="#cc7000")

    box(0.3, 0.7, 3.0, 0.9, "→ CRITICAL\n(needs review)", "#a52020")
    ax.text(1.8, 1.15, "→ CRITICAL\n(needs review)", ha="center", va="center",
            fontsize=10, color="white", fontweight="bold")
    arrow(1.8, 2.6, 1.8, 1.6, color="#a52020")

    box(6.7, 0.7, 3.0, 0.9, "→ HIGH (min)\n(needs review)", "#cc7000")
    ax.text(8.2, 1.15, "→ HIGH (min)\n(needs review)", ha="center", va="center",
            fontsize=10, color="white", fontweight="bold")
    arrow(8.2, 2.6, 8.2, 1.6, color="#cc7000")

    box(4.0, 2.6, 2.0, 0.9, "no override\n→ use bands", "#e7f7d8")
    arrow(5, 4.3, 5, 3.5, color="#1b6e1b")
    # bands list
    ax.text(5, 1.6,
            "Bands:\n≥0.85 critical · ≥0.65 high · ≥0.40 medium · else low",
            ha="center", fontsize=9, color="#333")

    save(fig, "fig_3_3_severity.png")


# ---------- Figure 3.4 : Database ER diagram ----------
def erd():
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.set_xlim(0, 8); ax.set_ylim(0, 7); ax.axis("off")

    # title strip
    ax.add_patch(Rectangle((0.5, 5.5), 7, 0.6, facecolor="#222"))
    ax.text(4, 5.8, "events", color="white", ha="center", va="center",
            fontsize=12, fontweight="bold")

    fields = [
        ("id",            "INTEGER  PK, AUTOINCREMENT"),
        ("timestamp",     "TEXT     NOT NULL  (ISO-8601)"),
        ("event_type",    "TEXT     NOT NULL  ('prompt' | 'image')"),
        ("input_summary", "TEXT     (prompt text or image filename)"),
        ("verdict",       "TEXT     NOT NULL  (allowed/blocked/clean/flagged)"),
        ("risk_score",    "REAL     0.0 – 1.0"),
        ("severity",      "TEXT     (low/medium/high/critical)"),
        ("details",       "TEXT     JSON (reasons, categories, ML info)"),
        ("reviewed",      "INTEGER  DEFAULT 0  (0 pending, 1 reviewed)"),
        ("analyst_note",  "TEXT     human reviewer note"),
    ]
    y = 5.2
    for i, (name, desc) in enumerate(fields):
        fill = "#f6f6f6" if i % 2 == 0 else "#ffffff"
        ax.add_patch(Rectangle((0.5, y - 0.42), 7, 0.42, facecolor=fill, edgecolor="#ccc"))
        ax.text(0.7, y - 0.21, name, fontsize=10, fontweight="bold", va="center")
        ax.text(2.6, y - 0.21, desc, fontsize=9, va="center", color="#333", family="monospace")
        y -= 0.42

    ax.text(4, 0.4,
            "SQLite database, WAL journal mode · one row per decision",
            ha="center", fontsize=9, style="italic", color="#444")
    save(fig, "fig_3_4_erd.png")


# ---------- Figure 3.5 : CNN architecture ----------
def cnn_arch():
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 4.5); ax.axis("off")

    layers = [
        ("Input\n32×32×3",        "#fff7d6"),
        ("Conv 32\n3×3 ReLU",     "#d6e8ff"),
        ("BatchNorm\n+ MaxPool",  "#cfe0f0"),
        ("Conv 64\n3×3 ReLU",     "#d6e8ff"),
        ("BatchNorm\n+ MaxPool",  "#cfe0f0"),
        ("Conv 128\n3×3 ReLU",    "#d6e8ff"),
        ("BatchNorm\n+ MaxPool",  "#cfe0f0"),
        ("Flatten\n+ Dropout 0.4","#e7d6ff"),
        ("Dense 128\nReLU",       "#e7f7d8"),
        ("Dense 1\nSigmoid",      "#fde2e2"),
    ]
    w = 1.15
    gap = 0.05
    x = 0.3
    centers = []
    for name, fill in layers:
        ax.add_patch(FancyBboxPatch((x, 1.7), w, 1.5, boxstyle="round,pad=0.04,rounding_size=0.1",
                                     linewidth=1.2, edgecolor="#222", facecolor=fill))
        ax.text(x + w/2, 2.45, name, ha="center", va="center", fontsize=9)
        centers.append(x + w/2)
        x += w + gap

    for i in range(len(centers) - 1):
        ax.add_patch(FancyArrowPatch((centers[i] + w/2 - 0.05, 2.45),
                                     (centers[i+1] - w/2 + 0.05, 2.45),
                                     arrowstyle="-|>", mutation_scale=10,
                                     linewidth=1.0, color="#444"))

    ax.text(6.5, 0.9, "Output  =  P(synthetic)    ·    flagged iff  P(synthetic) ≥ 0.50",
            ha="center", fontsize=10, style="italic")
    save(fig, "fig_3_5_cnn.png")


# ---------- Figure 4.1 : Layer 1 dataset composition ----------
def l1_dataset():
    fig, ax = plt.subplots(figsize=(8, 5))
    cats = [
        ("ncii", 158, "#c0392b"),
        ("benign_art", 150, "#27ae60"),
        ("seed_safe", 95, "#16a085"),
        ("impersonation", 90, "#e67e22"),
        ("benign_portrait", 80, "#2ecc71"),
        ("jailbreak", 80, "#d35400"),
        ("seed_harmful", 74, "#a93226"),
        ("benign_edit", 70, "#1abc9c"),
        ("forgery", 65, "#cf6a17"),
        ("benign_fashion", 50, "#52be80"),
        ("minor_safety", 40, "#922b21"),
        ("benign_vocab_trap", 15, "#7dcea0"),
        ("benign_document", 14, "#76d7c4"),
        ("benign_ignore", 10, "#48c9b0"),
        ("benign_public_figure", 10, "#45b39d"),
    ]
    names = [c[0] for c in cats][::-1]
    counts = [c[1] for c in cats][::-1]
    colors = [c[2] for c in cats][::-1]
    ax.barh(names, counts, color=colors, edgecolor="#222", linewidth=0.6)
    for i, v in enumerate(counts):
        ax.text(v + 2, i, str(v), va="center", fontsize=8)
    ax.set_xlabel("Number of prompts")
    ax.set_title("Layer 1 prompt-dataset composition (n = 1,001)\nred = harmful, green = benign",
                 fontsize=11, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_4_1_l1_dataset.png")


# ---------- Figure 4.2 : Layer 1 metrics bar chart ----------
def l1_metrics():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = ["Precision", "Recall", "F1-score"]
    harmful = [0.9714, 1.0000, 0.9855]
    safe = [1.0000, 0.9697, 0.9846]
    x = range(len(labels))
    width = 0.35
    ax.bar([i - width/2 for i in x], harmful, width, label="harmful",
           color="#c0392b", edgecolor="#222")
    ax.bar([i + width/2 for i in x], safe, width, label="safe",
           color="#27ae60", edgecolor="#222")
    for i, v in enumerate(harmful):
        ax.text(i - width/2, v + 0.005, f"{v:.3f}", ha="center", fontsize=9)
    for i, v in enumerate(safe):
        ax.text(i + width/2, v + 0.005, f"{v:.3f}", ha="center", fontsize=9)
    ax.set_ylim(0.85, 1.05)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels)
    ax.set_ylabel("Score (0–1)")
    ax.set_title("Layer 1 classification report on the held-out set (n = 201)",
                 fontsize=11, fontweight="bold")
    ax.legend()
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_4_2_l1_metrics.png")


# ---------- Figure 4.3 : Layer 2 confusion matrix (redrawn for the report) ----------
def l2_cm():
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    cm = [[4777, 223], [238, 4762]]
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Predicted\nREAL", "Predicted\nAI-GENERATED"])
    ax.set_yticklabels(["Actual REAL", "Actual AI-GENERATED"])
    labels = [("TN", 0, 0), ("FP", 0, 1), ("FN", 1, 0), ("TP", 1, 1)]
    for name, i, j in labels:
        v = cm[i][j]
        color = "white" if v > 3000 else "black"
        ax.text(j, i - 0.22, name, ha="center", va="center", color="yellow",
                fontsize=11, fontweight="bold")
        ax.text(j, i + 0.18, f"{v}", ha="center", va="center", color=color,
                fontsize=15, fontweight="bold")
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Actual label")
    ax.set_title("Layer 2 confusion matrix, 10,000 held-out CIFAKE images\n"
                 "TP = AI correctly flagged · TN = real correctly kept",
                 fontsize=10, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    save(fig, "fig_4_3_l2_confusion.png")


# ---------- Figure 4.4 : Combined accuracy comparison ----------
def accuracy_compare():
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    layers = ["Layer 1\nhold-out", "Layer 1\n5-fold CV", "Layer 1\nchallenge (n=38)",
              "Layer 2\ntest accuracy", "Layer 2\nROC-AUC"]
    values = [0.9851, 0.9870, 1.0000, 0.9539, 0.9902]
    colors = ["#3498db", "#2980b9", "#1f618d", "#e67e22", "#cb4335"]
    bars = ax.bar(layers, values, color=colors, edgecolor="#222")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width()/2, v + 0.004, f"{v*100:.2f}%",
                ha="center", fontsize=9.5, fontweight="bold")
    ax.set_ylim(0.90, 1.03)
    ax.set_ylabel("Score (0–1)")
    ax.set_title("Headline accuracy of the learned layers",
                 fontsize=11, fontweight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_4_4_accuracy.png")


if __name__ == "__main__":
    architecture()
    dataflow()
    severity()
    erd()
    cnn_arch()
    l1_dataset()
    l1_metrics()
    l2_cm()
    accuracy_compare()
    print("\nAll diagrams generated in", OUT)
