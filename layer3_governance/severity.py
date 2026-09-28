"""
Layer 3 - Severity scoring & human-review routing.

Maps a numeric risk score (0.0 - 1.0) plus context categories to a severity
band, and decides when a case must be escalated to a human analyst. This
mirrors the seminar's requirement (Section 4.1 / 5.2) that fully automated
systems be complemented by human oversight for cases above a threshold.
"""

# Ordered high -> low. The first threshold the score meets wins.
SEVERITY_BANDS = [
    (0.85, "critical"),
    (0.65, "high"),
    (0.40, "medium"),
    (0.0, "low"),
]
_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# Most serious categories - forced to CRITICAL even at a moderate score
# (NCII and any sexualisation of a minor).
CRITICAL_CATEGORIES = {"minor_safety", "ncii"}

# Serious-but-not-critical categories - bumped to at least HIGH at a moderate
# score (identity deepfakes and document/currency forgery).
HIGH_CATEGORIES = {"impersonation", "forgery"}

# Backwards-compatible alias (anything here triggers escalation review).
ESCALATE_CATEGORIES = CRITICAL_CATEGORIES | HIGH_CATEGORIES


def _band(risk_score):
    for threshold, label in SEVERITY_BANDS:
        if risk_score >= threshold:
            return label
    return "low"


def score_to_severity(risk_score, categories=None):
    """Convert a risk score (+ optional category tags) into a severity band."""
    categories = set(categories or [])
    if categories & CRITICAL_CATEGORIES and risk_score >= 0.40:
        return "critical"
    severity = _band(risk_score)
    if categories & HIGH_CATEGORIES and risk_score >= 0.40:
        # Escalate to at least "high" (never downgrade if already critical).
        if _RANK[severity] < _RANK["high"]:
            severity = "high"
    return severity


def needs_human_review(severity):
    """High and critical cases require analyst sign-off."""
    return severity in ("high", "critical")
