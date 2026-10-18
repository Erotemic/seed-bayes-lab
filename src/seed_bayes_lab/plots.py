"""Interactive Plotly figures built from the exact functions used in the tests."""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.search import (
    effective_search_success,
    method_observation_update,
    planted_success,
)


def evidence_sweep(prior: Prior, likelihoods: Likelihoods, samples: int = 201) -> go.Figure:
    """Posterior backdoor probability against P(evidence | successful backdoor)."""
    xs = np.linspace(0, 1, samples)
    posterior = []
    for l_succeeded in xs:
        trial = Likelihoods(likelihoods.honest, likelihoods.attempted_failed, float(l_succeeded))
        try:
            posterior.append(update(prior, trial).posterior_backdoor)
        except ValueError:
            posterior.append(float("nan"))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xs, y=posterior, name="P(backdoor | evidence)",
            mode="lines", line=dict(width=3),
            hovertemplate="P(E | B): %{x:.3f}<br>P(B | E): %{y:.3%}<extra></extra>",
        )
    )
    fig.add_hline(y=prior.backdoor, line_dash="dash", annotation_text="Prior P(B)")
    try:
        selected = update(prior, likelihoods)
        fig.add_trace(
            go.Scatter(
                x=[likelihoods.succeeded], y=[selected.posterior_backdoor],
                name="Current assumptions", mode="markers", marker=dict(size=12),
                hovertemplate="P(E | B): %{x:.3f}<br>P(B | E): %{y:.3%}<extra></extra>",
            )
        )
    except ValueError:
        pass
    fig.update_layout(
        template="plotly_white", title="How the evidence likelihood changes the posterior",
        xaxis_title="P(evidence | successful planted backdoor)",
        yaxis_title="P(successfully planted backdoor | evidence)",
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        xaxis=dict(range=[0, 1]),
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=35, r=25, t=55, b=65),
    )
    return fig


def direction_heatmap(prior: Prior, honest_likelihood: float, samples: int = 41) -> go.Figure:
    """The posterior-prior difference over two uncertain likelihood assumptions."""
    values = np.linspace(0, 1, samples)
    z = np.full((samples, samples), np.nan)
    for i, l_b in enumerate(values):
        for j, l_f in enumerate(values):
            try:
                result = update(prior, Likelihoods(honest_likelihood, float(l_f), float(l_b)))
                z[i, j] = result.delta_backdoor
            except ValueError:
                pass
    lim = max(float(np.nanmax(np.abs(z))), 1e-10)
    fig = go.Figure(
        go.Heatmap(
            x=values, y=values, z=z, zmin=-lim, zmax=lim,
            colorscale="RdBu", reversescale=True,
            colorbar=dict(title="Posterior - prior", tickformat="+.0%"),
            hovertemplate=(
                "P(E | failed attempt): %{x:.2f}"
                "<br>P(E | successful backdoor): %{y:.2f}"
                "<br>Update: %{z:+.3%}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        template="plotly_white", title="Direction of the Bayesian update",
        xaxis_title="P(evidence | attempted but failed)",
        yaxis_title="P(evidence | successful backdoor)",
        margin=dict(l=35, r=20, t=55, b=35),
    )
    return fig


def search_sweep(
    restricted_bits: float = 30,
    unrestricted_bits: float = 60,
    budget_bits: float = 36,
    known_restricted: float = 0.3,
    known_unrestricted: float = 0.3,
    prior_restricted: float = 0.5,
    publish_if_failed: float = 1.0,
    min_rarity: float = 15,
    max_rarity: float = 75,
    samples: int = 181,
) -> go.Figure:
    """Search success and Bayesian method observation versus vulnerability rarity."""
    xs = np.linspace(min_rarity, max_rarity, samples)
    st = [planted_success(float(k), restricted_bits, budget_bits, known_restricted) for k in xs]
    su = [planted_success(float(k), unrestricted_bits, budget_bits, known_unrestricted) for k in xs]
    before = []
    after = []
    for a, b in zip(st, su):
        result = method_observation_update(prior_restricted, a, b, publish_if_failed)
        before.append(result.before if result.before is not None else float("nan"))
        after.append(result.after if result.after is not None else float("nan"))
    fig = go.Figure()
    for name, ys, dashed in (
        ("Success with restricted method T", st, "solid"),
        ("Success with unrestricted method U", su, "solid"),
        ("P(B | published), before learning method", before, "dot"),
        ("P(B | published, T), after learning method", after, "dash"),
    ):
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=name, mode="lines", line=dict(width=2.5, dash=dashed),
            hovertemplate="Rarity: 2^-%{x:.1f}<br>Probability: %{y:.5%}<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_white", title="Selection freedom, attack knowledge, and publication policy",
        xaxis_title="Secret property rarity (k bits, q = 2^-k)",
        yaxis_title="Probability", yaxis=dict(tickformat=".0%", range=[0, 1.02]),
        legend=dict(orientation="h", y=-0.26),
        margin=dict(l=35, r=20, t=55, b=70),
    )
    return fig


def budget_slider_figure(
    restricted_bits: float = 30, unrestricted_bits: float = 60,
    rarity_min: float = 15, rarity_max: float = 65,
    budgets: tuple[int, ...] = (20, 24, 28, 30, 32, 36, 40, 44, 48, 52),
) -> go.Figure:
    """Standalone/offline interactive curve with a precomputed Plotly slider.

    The HTML works without a server, Python runtime, or external CDN.
    """
    xs = np.linspace(rarity_min, rarity_max, 201)

    def traces(b: int) -> list[go.Scatter]:
        result = []
        for name, freedom in (
            (f"Restricted ({restricted_bits:g} bits)", restricted_bits),
            (f"Unrestricted ({unrestricted_bits:g} bits)", unrestricted_bits),
        ):
            ys = [effective_search_success(float(k), freedom, float(b)) for k in xs]
            result.append(go.Scatter(
                x=xs, y=ys, name=name, mode="lines", line=dict(width=3),
                hovertemplate="Rarity: 2^-%{x:.1f}<br>Search success: %{y:.6%}<extra></extra>",
            ))
        return result

    initial = 36 if 36 in budgets else budgets[0]
    fig = go.Figure(data=traces(initial))
    fig.frames = [go.Frame(name=str(b), data=traces(b)) for b in budgets]
    steps = [dict(
        label=str(b), method="animate",
        args=[[str(b)], dict(frame=dict(duration=0, redraw=True),
                             transition=dict(duration=0), mode="immediate")],
    ) for b in budgets]
    fig.update_layout(
        template="plotly_white", title="Success probability versus secret-property rarity",
        xaxis_title="Vulnerability rarity (k bits, q = 2^-k)",
        yaxis_title="Probability of finding at least one candidate",
        yaxis=dict(tickformat=".0%", range=[0, 1.02]),
        sliders=[dict(active=budgets.index(initial), currentvalue=dict(prefix="Compute budget: 2^"),
                      pad=dict(t=48), steps=steps)],
        legend=dict(orientation="h", y=-0.36),
        margin=dict(l=40, r=25, t=60, b=120),
    )
    return fig
