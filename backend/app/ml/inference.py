"""Authorship-model gateway.

No validated classifier ships with CodeProof. This reports the model as unavailable
until validated artifacts AND a loader exist. It never returns a random or invented
probability."""


def model_assessment() -> dict:
    return {
        "model_status": "unavailable",
        "model_version": None,
        "authorship_assessment": "inconclusive",
        "probability": None,
        "reason": ("No trained and validated authorship classifier is configured. "
                   "Only code metrics and structural analysis were performed."),
    }
