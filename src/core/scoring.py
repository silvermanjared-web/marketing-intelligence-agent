"""
Signal scoring engine for email triage.

Scores incoming messages by urgency, relevance, and noise level using
weighted pattern matching. Designed for marketing operations where the
inbox is a firehose of vendor updates, platform alerts, campaign
notifications, and actual human requests.

Scoring tiers:
    >= 8  CRITICAL  — requires immediate attention
    >= 4  IMPORTANT — meaningful but not time-sensitive
    <  4  NOISE     — suppress or batch-process

Each pattern carries a weight and a human-readable reason so the
briefing agent can explain *why* something surfaced.
"""

import re

# Work domains — messages from these get a baseline priority bump.
# Replace with your organization's actual domains.
WORK_DOMAINS: set[str] = {
    "company.com",
    "agency-partner.com",
    "media-vendor.com",
}

# Noise domains — collapse into counts, never surface individually.
NOISE_DOMAINS: set[str] = {
    "linkedin.com",
    "facebookmail.com",
    "noreply",
    "no-reply",
    "mailer",
    "notifications",
    "marketing",
    "promo",
}

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# (regex, score_weight, human_reason)
CRITICAL_PATTERNS: list[tuple[str, int, str]] = [
    (r"\burgent\b", 3, "marked urgent"),
    (r"action required", 3, "action required"),
    (r"\basap\b", 3, "ASAP"),
    (r"final notice|last chance", 3, "deadline pressure"),
    (r"overdue|past due", 3, "overdue"),
    (r"account.{0,20}(?:locked|suspended|terminated)", 4, "account issue"),
    (r"security alert|unauthorized|fraud", 4, "security alert"),
    (r"respond by|due (?:today|tomorrow|eod|end of day)", 3, "deadline"),
    (r"escalat", 3, "escalation"),
]

IMPORTANT_PATTERNS: list[tuple[str, int, str]] = [
    (r"\binvoice\b|payment (?:due|required)", 2, "payment/invoice"),
    (r"approval (?:needed|required|pending)", 2, "needs approval"),
    (r"(?:re|fwd):\s", 1, "thread/reply"),
    (r"(?:checking in|following up|follow up|quick question)", 2, "direct outreach"),
    (r"(?:meeting|call|sync|standup|check-in)\b", 1, "meeting-related"),
    (r"(?:budget|forecast|report|deadline|deliverable)", 1, "work artifact"),
    (r"sign.?in.{0,15}(?:new|unusual)", 2, "sign-in alert"),
    (r"(?:campaign|performance|conversion|roas|cpa|cpl)\b", 1, "campaign metric"),
    (r"(?:launch|go.live|deploy|publish)\b", 2, "launch event"),
    (r"(?:client|stakeholder|executive)\b.*(?:review|feedback|question)", 2, "stakeholder request"),
]

# (regex, score_weight) — negative weights pull score down
NOISE_PATTERNS: list[tuple[str, int]] = [
    (r"unsubscribe", -2),
    (r"view (?:in browser|online|email)", -1),
    (r"newsletter", -2),
    (r"daily digest", -1),
    (r"off|% off|free shipping|limited time|shop now|deal", -2),
    (r"you(?:'re| are) (?:invited|eligible|selected|approved) (?:to|for)", -1),
]


def triage_score(
    subject: str,
    body: str,
    source: str = "api",
    domain: str = "",
) -> tuple[int, list[str]]:
    """Score a message for triage priority.

    Args:
        subject: Email subject line.
        body: Email body text (preview or full).
        source: Data source identifier (e.g., "api", "imap", "webhook").
                Work-source messages get a baseline bump.
        domain: Sender domain for work-domain detection.

    Returns:
        Tuple of (score, reasons) where score maps to triage tiers
        and reasons is a list of human-readable trigger descriptions.
    """
    text = f"{subject} {body}".lower()
    score = 0
    reasons: list[str] = []

    # Source bonus: work email channels are inherently higher priority.
    if source in ("work", "internal"):
        score += 3
    if domain in WORK_DOMAINS:
        score += 2

    # Critical signals — high-weight, unambiguous urgency markers.
    for pattern, weight, reason in CRITICAL_PATTERNS:
        if re.search(pattern, text):
            score += weight
            reasons.append(reason)

    # Important signals — moderate weight, contextually meaningful.
    for pattern, weight, reason in IMPORTANT_PATTERNS:
        if re.search(pattern, text):
            score += weight
            if reason not in reasons:
                reasons.append(reason)

    # Noise penalties — pull score down for obvious bulk/promo content.
    for pattern, weight in NOISE_PATTERNS:
        if re.search(pattern, text):
            score += weight  # weight is negative

    return score, reasons
