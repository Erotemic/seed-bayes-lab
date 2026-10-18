"""Launch with: streamlit run src/seed_bayes_lab/app.py"""

from __future__ import annotations

import streamlit as st

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.evidence import (
    EVIDENCE_TITLE, EVIDENCE_OBSERVATION, EVIDENCE_LIMITS,
    EVIDENCE_LIKELIHOOD_NOTE, METHOD_OBSERVATION,
    evidence_sources_markdown,
)
from seed_bayes_lab.ui_state import initialize_assumptions, reset_assumptions
from seed_bayes_lab.plots import direction_heatmap, evidence_sweep, search_sweep
from seed_bayes_lab.search import method_observation_update, planted_success

st.set_page_config(page_title="Seed Bayes Lab", page_icon="∴", layout="wide")
st.title("Seed Bayes Lab")
st.caption("Explore assumptions. No slider default is an empirical estimate of a NIST backdoor.")

initialize_assumptions(st.session_state)
st.button(
    "Reset all assumptions",
    key="reset_all_assumptions",
    on_click=reset_assumptions,
    args=(st.session_state,),
    help="Restore every slider in both interactive tabs to its initial value.",
)
st.info(f"**{EVIDENCE_TITLE}**\n\n{EVIDENCE_OBSERVATION}")
st.caption(EVIDENCE_LIMITS)
st.markdown(evidence_sources_markdown())

bayes, search, assumptions = st.tabs(["Evidence / Bayes", "Search & publication", "Interpretation"])

with bayes:
    st.subheader("Three-world finite model")
    st.caption(EVIDENCE_LIKELIHOOD_NOTE)
    st.markdown("Worlds: **honest**, **attempted but failed**, **successfully planted backdoor**.")
    left, right = st.columns([1, 2], gap="large")
    with left:
        intent = st.slider("Prior P(malicious intent)", 0.0, 1.0, step=0.01, key="prior_intent")
        success = st.slider("P(successful backdoor | intent)", 0.0, 1.0, step=0.01, key="success_given_intent")
        st.markdown("**Likelihood of the discovered evidence**")
        honest_l = st.slider("P(E | honest)", 0.0, 1.0, step=0.01, key="likelihood_honest")
        failed_l = st.slider("P(E | malicious attempt, failed)", 0.0, 1.0, step=0.01, key="likelihood_failed")
        succeeded_l = st.slider("P(E | successfully backdoored)", 0.0, 1.0, step=0.01, key="likelihood_succeeded")
    prior = Prior.from_intent_success(intent, success)
    likelihoods = Likelihoods(honest_l, failed_l, succeeded_l)
    with right:
        try:
            result = update(prior, likelihoods)
        except ValueError:
            st.error("The assumed evidence has probability zero; conditioning is undefined.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("P(backdoor) before", f"{result.prior_backdoor:.2%}")
            c2.metric("P(backdoor) after", f"{result.posterior_backdoor:.2%}",
                      delta=f"{result.delta_backdoor:+.2%}", delta_color="inverse")
            c3.metric("P(intent) after", f"{result.posterior_intent:.2%}")
            st.plotly_chart(evidence_sweep(prior, likelihoods), use_container_width=True)
            st.markdown(
                f"**Direction:** {result.direction()} · "
                f"**Bayes factor (B vs. not B):** "
                f"{result.bayes_factor_backdoor if result.bayes_factor_backdoor is not None else 'undefined'}"
            )
    st.plotly_chart(direction_heatmap(prior, honest_l), use_container_width=True)
    st.caption("The heatmap varies both malicious-state likelihoods; its values are not observed data.")

with search:
    st.subheader("Method observation under 100% malicious intent")
    st.info(METHOD_OBSERVATION)
    st.markdown(
        "Set the chance of knowing a recognizable attack under each method. "
        "Set a publication rule. An observation of the restricted method T then "
        "conditions on both the published curve and the method used."
    )
    a, b, c = st.columns(3)
    with a:
        t_bits = st.slider("Timestamp method freedom (bits)", 5, 60, step=1, key="restricted_bits")
        u_bits = st.slider("Alternative method freedom (bits)", 5, 80, step=1, key="unrestricted_bits")
        compute = st.slider("Evaluation budget (bits)", 5, 80, step=1, key="compute_bits")
    with b:
        rarity = st.slider("Secret vulnerability rarity k (bits)", 5, 80, step=1, key="rarity_bits")
        know_t = st.slider("P(attack known | method T)", 0.0, 1.0, step=0.01, key="know_restricted")
        know_u = st.slider("P(attack known | method U)", 0.0, 1.0, step=0.01, key="know_unrestricted")
    with c:
        alpha = st.slider("Prior P(method T) before publication", 0.0, 1.0, step=0.01, key="prior_restricted")
        rho = st.slider("P(publish | failed attempt)", 0.0, 1.0, step=0.01, key="publish_failed")
        st.caption("P(publish | successful attempt) is fixed at 100% in this toy model.")
    st_t = planted_success(rarity, t_bits, compute, know_t)
    st_u = planted_success(rarity, u_bits, compute, know_u)
    comparison = method_observation_update(alpha, st_t, st_u, rho)
    x, y, z = st.columns(3)
    x.metric("P(B | published)",
             "undefined" if comparison.before is None else f"{comparison.before:.4%}")
    y.metric("P(B | published, T)",
             "undefined" if comparison.after is None else f"{comparison.after:.4%}")
    z.metric("Change", "undefined" if comparison.delta is None else f"{comparison.delta:+.4%}")
    st.plotly_chart(search_sweep(t_bits, u_bits, compute, know_t, know_u, alpha, rho),
                    use_container_width=True)
    st.info(
        "The search model assumes independently targetable curves, a fixed testing budget, "
        "and method choice before success is known. A hypothetical direct construction "
        "or method-dependent attack capability may violate those assumptions."
    )

with assumptions:
    st.markdown("""
    ### What the model actually proves

    The Bayesian direction in the three-world model is determined by the relative
    likelihood of the recovered evidence in the backdoored world versus the
    non-backdoored worlds. The search-model direction is non-increasing when the
    restricted method has no higher conditional success probability, the method
    is chosen before outcomes are observed, and publication is treated explicitly.

    ### What it does not prove

    It does not determine whether NIST P-256 was backdoored, establish a historical
    1997 search budget, estimate the prevalence of undiscovered vulnerabilities,
    or prove that timestamp-seeding was a compulsory restriction on designers.

    The Lean development proves the algebraic identities with explicit hypotheses.
    The Python charts instantiate hypotheses chosen by the user; they are not
    cryptographic evidence on their own.
    """)
