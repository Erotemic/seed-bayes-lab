"""Launch with: streamlit run src/seed_bayes_lab/app.py"""

from __future__ import annotations

import streamlit as st

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.sensitivity import (
    SLIDER_SPECS, BAYES_SLIDERS, SEARCH_SLIDERS,
    analyze_slider, format_delta_pp, direction, BreakEvenRegion,
)
from seed_bayes_lab.evidence import (
    EVIDENCE_TITLE, EVIDENCE_SHORT, EVIDENCE_OBSERVATION, EVIDENCE_LIMITS,
    EVIDENCE_LIKELIHOOD_NOTE, METHOD_OBSERVATION,
    evidence_sources_markdown,
)
from seed_bayes_lab.ui_state import (
    EVIDENCE_PRESET_LABELS, active_evidence_preset, apply_evidence_preset,
    initialize_assumptions, reset_assumptions,
)
from seed_bayes_lab.glossary import (
    BAYES_EVENTS, BAYES_QUANTITIES, SEARCH_EVENTS, SEARCH_QUANTITIES,
    BAYES_PARAMETERS, SEARCH_PARAMETERS,
)
from seed_bayes_lab.plots import direction_heatmap, evidence_sweep, search_sweep
from seed_bayes_lab.search import method_observation_update, planted_success

st.set_page_config(page_title="Seed Bayes Lab", page_icon="∴", layout="wide")
st.title("Seed Bayes Lab")
st.caption("Explore assumptions. No slider default is an empirical estimate of a NIST backdoor.")
st.markdown("""
<style>
.endpoint-card{border:1px solid #dbe3eb;border-radius:10px;padding:7px 12px;
    min-height:82px;background:transparent;color:inherit}
.endpoint-card.right{text-align:right}
.endpoint-head{font-size:.70rem;font-weight:650;opacity:.72;letter-spacing:.035em}
.endpoint-main{display:flex;gap:8px;align-items:center;margin:3px 0}
.endpoint-card.right .endpoint-main{justify-content:flex-end}
.endpoint-icon{display:inline-flex;align-items:center;justify-content:center;
    width:27px;height:27px;border-radius:50%;font-size:18px;flex-shrink:0;
    background:#ebedf0;color:#45556b;font-weight:750}
.endpoint-card.decrease .endpoint-icon{background:#dcece6;color:#206b54}
.endpoint-card.increase .endpoint-icon{background:#fae5e0;color:#a54832}
.endpoint-number{font-size:1.0rem;font-variant-numeric:tabular-nums;font-weight:700}
.endpoint-posterior{font-size:.72rem;opacity:.72;font-variant-numeric:tabular-nums}
.break-even-companion{height:34px;position:relative;margin:-2px 12px 5px}
.break-even-companion-rail{position:absolute;top:5px;left:0;right:0;height:4px;background:#dee1e9;border-radius:4px}
.break-even-companion-bar{position:absolute;top:3px;height:9px;background:#9670c65c;border-radius:4px}
.break-even-companion-tick{position:absolute;top:0;height:17px;width:2px;background:#734baa;transform:translateX(-50%);box-shadow:0 0 0 1px white}
.break-even-companion-label{position:absolute;top:16px;left:50%;transform:translateX(-50%);background:#f2edf9;color:#674393;padding:1px 3px;font-size:.67rem;border-radius:3px;font-variant-numeric:tabular-nums;white-space:nowrap}
.break-even-companion-label.at-start{transform:translateX(-4%)}
.break-even-companion-label.at-end{transform:translateX(-96%)}
</style>
""", unsafe_allow_html=True)

initialize_assumptions(st.session_state)
st.button(
    "Reset all assumptions",
    key="reset_all_assumptions",
    on_click=reset_assumptions,
    args=(st.session_state,),
    help="Restore every slider in both interactive tabs to its initial value.",
)
st.info(f"**{EVIDENCE_TITLE}**\n\n{EVIDENCE_SHORT}")
with st.expander("Full evidence definition, limitations and sources"):
    st.markdown(EVIDENCE_OBSERVATION)
    st.markdown(EVIDENCE_LIMITS)
    st.markdown(evidence_sources_markdown())


def _endpoint_card(title: str, position: float | int, posterior: float | None,
                   evidence_delta: float | None, after_label: str, align: str) -> str:
    """Evidence update at a fixed endpoint, not change from the current dial."""
    move = direction(evidence_delta)
    icon = {"decrease": "↘", "increase": "↗", "unchanged": "→",
            "undefined": "?"}[move]
    formatted = format_delta_pp(evidence_delta)
    number = formatted.removeprefix("↘ ").removeprefix("↗ ")
    result = "undefined" if posterior is None else f"{posterior:.2%}"
    return (
        f'<div class="endpoint-card {align} {move}" role="group" '
        f'aria-label="{title} {position}; evidence update at endpoint (posterior minus prior): '
        f'{formatted}; {after_label} at endpoint {result}">'
        f'<div class="endpoint-head">{title} {position}</div>'
        f'<div class="endpoint-main"><span class="endpoint-icon" aria-hidden="true">'
        f'{icon}</span><span class="endpoint-number">{number}</span></div>'
        f'<div class="endpoint-posterior">{after_label} = {result}</div></div>'
    )


def _location_string(value: float, *, integer_step: bool) -> str:
    if integer_step and abs(value - round(value)) < 1e-7:
        return str(round(value))
    return f"{value:.2f}" if integer_step else f"{value:.3f}".rstrip("0").rstrip(".")


def _break_even_ruler(key: str, regions: tuple[BreakEvenRegion, ...]) -> str:
    """Companion ruler immediately below Streamlit's native slider.

    Streamlit doesn't expose custom tick positions on its slider track, so
    this independent, aligned miniature rail displays the same locations.
    """
    from html import escape

    spec = SLIDER_SPECS[key]
    percent = lambda x: 100.0 * (x - spec.minimum) / (spec.maximum - spec.minimum)
    bits = spec.step >= 1
    parts = ['<div class="break-even-companion" role="img" aria-label="']
    if regions:
        words = [f"break-even between {_location_string(r.start,integer_step=bits)} and "
                 f"{_location_string(r.end,integer_step=bits)}" if r.is_interval else
                 f"break-even at {_location_string(r.start,integer_step=bits)}" for r in regions]
        parts.append(escape('; '.join(words), quote=True))
    else:
        parts.append('No break-even in range')
    parts.append('"><div class="break-even-companion-rail"></div>')
    for region in regions:
        if region.is_interval:
            parts.append(f'<div class="break-even-companion-bar" '
                         f'style="left:{percent(region.start):.6f}%;'
                         f'width:{percent(region.end)-percent(region.start):.6f}%"></div>')
        for x in ([region.start,region.end] if region.is_interval else [region.start]):
            v = percent(x)
            align = 'at-start' if v < 12 else 'at-end' if v > 88 else ''
            label = ('≈' if region.interpolated else '') + _location_string(x,integer_step=bits)
            parts.append(f'<div class="break-even-companion-tick" style="left:{v:.6f}%">'
                         f'<span class="break-even-companion-label {align}">{escape(label)}</span>'
                         '</div>')
    return ''.join(parts) + '</div>'


def _break_even_caption(key: str, regions: tuple[BreakEvenRegion, ...]) -> str:
    spec = SLIDER_SPECS[key]
    bits = spec.step >= 1
    if not regions:
        return "No break-even point in range."
    descriptions = []
    for region in regions:
        low = _location_string(region.start,integer_step=bits)
        high = _location_string(region.end,integer_step=bits)
        if region.is_interval:
            descriptions.append(f"equality from {low} to {high}")
        else:
            descriptions.append(f"{'approximately ' if region.interpolated else ''}{low}")
    return "Break-even: " + "; ".join(descriptions) + "."


def sensitivity_slider(key: str) -> float | int:
    """Slider with large effect icons immediately below its left/right ends."""
    spec = SLIDER_SPECS[key]
    value = st.slider(spec.label, spec.minimum, spec.maximum, step=spec.step, key=key)
    sens = analyze_slider(st.session_state, key)
    st.markdown(_break_even_ruler(key, sens.break_evens), unsafe_allow_html=True)
    st.caption(_break_even_caption(key, sens.break_evens))
    after_label = "P(B | E)" if spec.group == "bayes" else "P(B | J,T)"
    left, right = st.columns(2)
    with left:
        st.markdown(_endpoint_card("MIN", spec.minimum, sens.left_posterior,
                                   sens.left_delta, after_label, "left"),
                    unsafe_allow_html=True)
    with right:
        st.markdown(_endpoint_card("MAX", spec.maximum, sens.right_posterior,
                                   sens.right_delta, after_label, "right"),
                    unsafe_allow_html=True)
    st.caption(
        f"**{sens.status}** · Full evidence-update Δ range: "
        f"{format_delta_pp(sens.minimum_delta)} to {format_delta_pp(sens.maximum_delta)}"
        + (f" · {sens.undefined_positions} undefined setting(s)"
           if sens.undefined_positions else "")
    )
    return value


def show_flip_summary(keys: tuple[str, ...]) -> None:
    sensitivities = [analyze_slider(st.session_state, key) for key in keys]
    flipped = [s.spec.label for s in sensitivities if s.can_reverse]
    current = sensitivities[0].current_direction
    if current == "unchanged":
        movable = [s.spec.label for s in sensitivities
                   if {"increase", "decrease"} & s.directions]
        st.info(
            "**Current evidence update: zero.** "
            f"{len(movable)} of {len(keys)} controls can move the update away from "
            "zero while other inputs stay fixed. "
            + ("Controls: " + ", ".join(movable) + "." if movable
               else "No individual control changes its direction.")
        )
        return
    st.info(
        f"**Current direction: {current}.** "
        f"{len(flipped)} of {len(keys)} controls can reverse it "
        "by themselves while other inputs stay fixed. "
        + ("Reversing controls: " + ", ".join(flipped) + "." if flipped
           else "No individual control can reverse it.")
    )


bayes, search, glossary, assumptions = st.tabs([
    "Evidence / Bayes", "Search & publication", "Notation glossary", "Interpretation",
])

with bayes:
    st.subheader("Three-world finite model")
    st.caption(EVIDENCE_LIKELIHOOD_NOTE)
    st.caption("B denotes a deliberately planted backdoor; I denotes intent to plant one.")
    st.caption("Endpoint arrows show the evidence update at MIN/MAX. The purple tick on the companion ruler marks Δ = 0; a purple segment marks an equality interval. These locations depend only on the other dials. Approximate ticks may lie between selectable slider steps.")
    st.markdown("Worlds: **honest**, **attempted but failed**, **successfully planted backdoor**.")
    left, right = st.columns([1, 2], gap="large")
    with left:
        st.markdown("**Evidence likelihood scenarios**")
        st.caption(
            "Starts neutral: P(E | H) = P(E | F) = P(E | B) = 0.50. "
            "Equal likelihoods leave P(B) unchanged; this is a modeling baseline, "
            "not an assessment of the historical discovery."
        )
        active = active_evidence_preset(st.session_state)
        preset_columns = st.columns(3, gap="small")
        for (name, label), column in zip(EVIDENCE_PRESET_LABELS.items(), preset_columns):
            with column:
                st.button(
                    label,
                    key=f"preset_{name}",
                    type="primary" if name == active else "secondary",
                    on_click=apply_evidence_preset,
                    args=(st.session_state, name),
                    use_container_width=True,
                    help="Illustrative probabilities, not measured historical evidence",
                )
        st.caption(
            "Current scenario: " +
            (EVIDENCE_PRESET_LABELS[active] if active else "Custom likelihoods")
        )
        intent = sensitivity_slider("prior_intent")
        st.caption("The 0.50 default is symmetric for illustration, not an estimated historical probability.")
        success = sensitivity_slider("success_given_intent")
        st.markdown("**Likelihood of the discovered evidence**")
        honest_l = sensitivity_slider("likelihood_honest")
        failed_l = sensitivity_slider("likelihood_failed")
        succeeded_l = sensitivity_slider("likelihood_succeeded")
    show_flip_summary(tuple(spec.key for spec in BAYES_SLIDERS))
    prior = Prior.from_intent_success(intent, success)
    likelihoods = Likelihoods(honest_l, failed_l, succeeded_l)
    with right:
        try:
            result = update(prior, likelihoods)
        except ValueError:
            st.error("The assumed evidence has probability zero; conditioning is undefined.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("P(B)", f"{result.prior_backdoor:.2%}")
            c1.caption("Before observing E")
            c2.metric("P(B | E)", f"{result.posterior_backdoor:.2%}",
                      delta=f"{result.delta_backdoor:+.2%}", delta_color="inverse")
            c2.caption("After observing E")
            c3.metric("P(I | E)", f"{result.posterior_intent:.2%}")
            c3.caption("Malicious intent after E")
            st.plotly_chart(evidence_sweep(prior, likelihoods), use_container_width=True)
            st.markdown(
                f"**Direction:** {result.direction()} · "
                f"**Bayes factor (B vs. not B):** "
                f"{result.bayes_factor_backdoor if result.bayes_factor_backdoor is not None else 'undefined'}"
            )
    heatmap = direction_heatmap(prior, honest_l)
    st.plotly_chart(heatmap, use_container_width=True)
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
        t_bits = sensitivity_slider("restricted_bits")
        u_bits = sensitivity_slider("unrestricted_bits")
        compute = sensitivity_slider("compute_bits")
    with b:
        rarity = sensitivity_slider("rarity_bits")
        know_t = sensitivity_slider("know_restricted")
        know_u = sensitivity_slider("know_unrestricted")
    with c:
        alpha = sensitivity_slider("prior_restricted")
        rho = sensitivity_slider("publish_failed")
        st.caption("P(publish | successful attempt) is fixed at 100% in this toy model.")
    st.caption("Endpoint arrows show Δ = P(B | J,T) − P(B | J) at MIN/MAX. Purple ticks/segments on the companion rulers mark Δ = 0. This conditions on T, not E.")
    show_flip_summary(tuple(spec.key for spec in SEARCH_SLIDERS))
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

def _show_entries(entries) -> None:
    st.table([{"Notation": entry.symbol, "Exact definition": entry.definition,
              "Qualification": entry.qualification} for entry in entries])


def _show_parameters(entries) -> None:
    st.table([{"Slider / notation": f"{entry.symbol}  ·  {SLIDER_SPECS[entry.key].label}",
              "Exact meaning": entry.definition, "Assumptions": entry.qualification}
              for entry in entries])


with glossary:
    st.subheader("Event notation and model assumptions")
    st.caption("The two models use different observations. E is observed historical provenance; T is a hypothetical actual method restriction. Every number below is a user-chosen assumption, not historical calibration.")
    st.markdown("### Finite Bayes model · Evidence / Bayes tab")
    st.markdown("The elementary outcomes are **Ω = {H, F, B}**. Exactly one occurs. The sample space describes a single published curve's historical outcome, not uniformly distributed seeds.")
    _show_entries(BAYES_EVENTS)
    st.markdown("#### Probability notation and evidence update")
    _show_entries(BAYES_QUANTITIES)
    st.markdown("#### The five Bayesian input dials")
    _show_parameters(BAYES_PARAMETERS)
    st.markdown("### Search and publication model · separate tab")
    st.markdown("Here **I is fixed as true**; the designer chooses T or U before evaluating candidate curves. J represents publication. Conditioning on T after J is not conditioning on E.")
    _show_entries(SEARCH_EVENTS)
    st.markdown("#### Search formulas and conditioning")
    _show_entries(SEARCH_QUANTITIES)
    st.markdown("#### The eight search-model input dials")
    _show_parameters(SEARCH_PARAMETERS)
    st.markdown("### How to read the slider-end icons")
    st.markdown("**↘ evidence decreases backdoor probability**, **↗ evidence increases it**, **→ unchanged**, **? undefined**. Each icon shows **Δupdate = posterior − prior** at the dial's endpoint, holding all others fixed. It is not movement relative to the current posterior. Purple break-even ticks show where Δupdate = 0, and purple segments show equality intervals. The Streamlit version puts these ticks on a companion ruler directly below the native slider. Interpolated ticks may lie between selectable settings. Neither the ticks nor endpoint badges change when their own slider moves. **CAN REVERSE** checks every selectable position, not just MIN/MAX.")


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
