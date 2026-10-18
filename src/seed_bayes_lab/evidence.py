"""What E denotes in the model; this is evidence, not a prior assignment."""

from __future__ import annotations

EVIDENCE_TITLE = "Observed evidence E: reconstructed seed provenance"

EVIDENCE_OBSERVATION = (
    "The published seeds for NIST P-192, P-224, P-256, P-384, and P-521 "
    "can be reproduced as outputs of the C-library `lrand48` generator "
    "initialized with numbers corresponding to Unix timestamps in 1997-1998. "
    "Multiple published values fit the reconstructed generator streams. "
    "For P-256, the published seed is candidate 1,842."
)

EVIDENCE_LIMITS = (
    "This reconstruction does **not** establish that the original programmer "
    "read the wall clock without retries, how many candidate streams were tried, "
    "or why some candidates passing the currently reconstructed checks were "
    "skipped. It does not demonstrate the presence or absence of a backdoor."
)

EVIDENCE_LIKELIHOOD_NOTE = (
    "The P(E | honest), P(E | attempted-but-failed), and "
    "P(E | successful-backdoor) sliders are **hypothetical likelihoods of "
    "observing this reconstruction** under each world. They are not measured "
    "from the historical record."
)

METHOD_OBSERVATION = (
    "In the second model, observation T means that the published curve came "
    "from the *restricted timestamp method*, after publication. "
    "This is a stronger assumption than E alone: matching the historical "
    "generator does not prove the designer's search was truly restricted."
)

SOURCES = (
    ("Anthropic: Claude reveals ECDSA curve origins",
     "https://www.anthropic.com/research/ecdsa-curve-origins"),
    ("Filippo Valsorda: The NIST Elliptic Curves Seeds Bounty Has Been Claimed",
     "https://words.filippo.io/seeds-solved/"),
)


def evidence_sources_markdown() -> str:
    """A source line for Streamlit's Markdown renderer."""
    return "Sources: " + " · ".join(f"[{label}]({url})" for label, url in SOURCES)
