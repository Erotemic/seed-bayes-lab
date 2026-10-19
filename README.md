# Seed Bayes Lab

A small Python package and Lean 4 library for auditing Bayesian claims about the
provenance of cryptographic parameters. The application is deliberately narrow:
**formalize the probability algebra and visualize sensitivity to assumptions**.
It does not try to formalize elliptic curves, SHA-1, `lrand48`, or cryptanalysis.

The modeled outcome is **a deliberately planted backdoor**, not an accidental
vulnerability. Every numerical parameter is a hypothetical input. Nothing in
this repository estimates the actual probability that NIST P-256 is backdoored.

## What's included

- `src/seed_bayes_lab/model.py`: exact three-world Bayes calculations for
  *honest*, *attempted-but-failed*, and *successful deliberate backdoor*.
- `src/seed_bayes_lab/search.py`: illustrative independent-candidate search,
  limits from candidate freedom and computing budget, and publication selection.
- `src/seed_bayes_lab/plots.py`: reusable Plotly interactive curves, a directional
  heatmap, and a no-server budget slider.
- `src/seed_bayes_lab/app.py`: Streamlit explorer with editable assumptions, explicit
  recovered-evidence description, source links, and reset-all button.
- `src/seed_bayes_lab/sensitivity.py`: complete one-dial-at-a-time directional
  scans, including flip detection, endpoint effects, and interior extrema.
- `src/seed_bayes_lab/offline.js`: equivalent JavaScript calculations for the
  full offline HTML application, with parity tests against Python.
- `src/seed_bayes_lab/evidence.py`: shared observed-evidence definition.
- `src/seed_bayes_lab/glossary.py`: shared finite-world events, search/publication
  events, all thirteen input meanings, and display notation for both interfaces.
- `src/seed_bayes_lab/ui_state.py`: centralized slider defaults and reset behavior.
- `examples/interactive_demo.html`: generated, self-contained offline explorer
  with all thirteen sliders, icon-led endpoint effects, a detailed notation
  glossary, live charts, reset, and direction-reversal hints.
- `SeedBayes/Finite.lean`: finite Bayesian identities, odds form, factorization,
  likelihood-ratio criterion for a decreasing posterior, and 100%-intent case.
- `SeedBayes/Selection.lean`: when observing the more constrained method must
  decrease (or leave unchanged) the conditional success probability.
- `tests/`: numerical identities, boundary cases, sensitivity and plots.

## Quick start (Ubuntu + uv)

From the root of this repository:

```bash
uv sync --extra dev --extra app
uv run pytest
uv run streamlit run src/seed_bayes_lab/app.py
```

Open the local address printed by Streamlit. The **Reset all assumptions**
button restores every control in both interactive models. A compact evidence
summary appears above the tabs; expand it for the complete observation,
limitations, and historical source links.
Use the **Evidence / Bayes** tab to
change the three likelihoods and priors, and **Search & publication** to vary
seed freedom, vulnerability rarity, search budget, chance of knowing an attack,
and policy for publishing unsuccessful attempts.

For the **complete shareable application**, open
`examples/interactive_demo.html` in a browser (no server, internet, Python,
Streamlit, or CDN needed). It now provides every assumption slider, live Bayes
and search plots, visual endpoint badges, a full notation glossary tab,
and a global reset.
The HTML is several megabytes because Plotly is embedded. To regenerate it:

```bash
uv run seed-bayes-demo examples/interactive_demo.html
```

The global reset restores all thirteen controls in either interface. Both
interfaces describe the historical observation E, distinguish it from the
stronger method-observation T, and report before/after probabilities using
`P(B)` and `P(B | E)` (or `P(B | published)` and
`P(B | published,T)` in the search tab).

The **icon at each slider endpoint** shows the evidence update at that
fixed endpoint, not movement relative to the slider's live setting. In the
Bayes tab the endpoint delta is

`Δendpoint = P(B | E; x=endpoint) - P(B; x=endpoint)`

in **percentage points**; the search tab uses
`P(B | J,T; x=endpoint) - P(B | J; x=endpoint)`.
All other sliders remain at their current values. Consequently, moving a
slider does **not** change its own MIN/MAX badges; changing *other*
sliders can. Below the signed arrow is the posterior at that endpoint.
An upward red arrow means evidence increases the backdoor probability,
a downward green arrow means it decreases it, neutral means no update,
and a question mark means conditioning is undefined.

The **CAN REVERSE** indicator scans the same evidence-update delta at
*all* positions (including interior ones), and reports whether moving this
dial can change its sign relative to the current configuration. Equality
is not a strict reversal. The glossary defines all events and parameters.
Evidence E is not the same as search-model observation T.

The default `P(I)=0.50` is a **symmetric demonstration prior**, not a factual
assessment or a claim that maximum entropy automatically represents ignorance.

An alternative without uv:

```bash
python -m pip install -e '.[dev,app]'
python -m pytest
python -m streamlit run src/seed_bayes_lab/app.py
```

## Lean formalization

Install [elan](https://github.com/leanprover/elan), then from this repo:

```bash
lake update
lake exe cache get
lake build
```

The Lean toolchain and Mathlib dependency are pinned to **v4.32.0**. The proofs
are independent of any probabilistic cryptanalysis model. Each theorem states
its nonzero/positivity hypotheses. None requires a full measure-theory event
space; `Prior` and `Likelihood` are three-element finite tables encoded as
structures.

**Validation status:** Python tests have been executed, including Python–JavaScript
parity checks for the offline calculations. The initial
Lean build reported noncomputable real-division definitions and deprecated
order-multiplication lemma usage. Those sources have been corrected using
`noncomputable def` and `mul_lt_mul_iff_of_pos_left`. The environment used
for this update has no Lean toolchain or Mathlib cache, so the revised files
have **not been compiled here**. Run `lake build` to verify these fixes.
There are no `sorry`/axiom shortcuts in the supplied files.

## Observed evidence versus assumed likelihoods

The event **E** shown in the app is the reconstruction reported by Anthropic
and independently investigated by Filippo Valsorda: published NIST prime-curve
seeds match C-library `lrand48` streams initialized with integers corresponding
to plausible 1997-1998 Unix timestamps; in particular, P-256 is candidate 1842.
This does **not** establish that the clock was read impartially, why certain
candidate curves were skipped, or how many generator restarts occurred.

The three `P(E | world)` inputs express **assumed** probabilities of observing
that reconstruction under a benign world, a failed malicious attempt, or a
successful malicious attempt. They are not probabilities learned from the
reconstructed seeds. Likewise, the second app tab's observation T (restricted
method) is a stronger hypothetical assumption, not a proven historical limit.

Sources: [Anthropic](https://www.anthropic.com/research/ecdsa-curve-origins) and
[Filippo Valsorda](https://words.filippo.io/seeds-solved/).

## Python example

```python
from seed_bayes_lab import Likelihoods, Prior, update

# These probabilities are ILLUSTRATIVE, not inferred from historical records.
p = Prior.from_intent_success(intent=1.0, success_given_intent=0.4)
e = Likelihoods(honest=0.9, attempted_failed=0.8, succeeded=0.1)
result = update(p, e)

print(result.prior_backdoor)       # 0.4
print(result.posterior_backdoor)   # 0.076923...
print(result.direction())          # decrease
```

Even with P(intent) = 1, evidence can change P(successful backdoor).

## Central mathematical result

For a nondegenerate prior and evidence with positive probability:

\[
 P(B\mid E)<P(B)\quad\Longleftrightarrow\quad
 P(E\mid B)<P(E\mid\neg B).
\]

The theorem `posterior_lt_prior_iff_likelihood_ratio` states this for the
finite model. The input likelihoods are not derived from the seed discovery:
they **are the assumptions whose plausibility needs to be investigated**.

For a separately assumed *ex ante* choice of generator, write `s_T` for
conditional attack success with the timestamp method and `s_U` for the
alternative. If `alpha` is the prior chance of T, then:

\[
 s_T - (\alpha s_T +(1-\alpha)s_U)
   = (1-\alpha)(s_T-s_U).
\]

Thus the update is nonpositive when `s_T <= s_U`. This theorem needs no model
of vulnerability density, but the **ordering of conditional success rates is
an explicit hypothesis**, not a consequence of recognizing `lrand48`.

See [docs/model.md](docs/model.md) for every conditioning and independence
assumption, especially the danger of conditioning on published attempts.

## Non-goals and interpretative boundaries

1. Discovering timestamp provenance is not the same as proving that the clock
   was read once or that timestamps were chosen impartially.
2. The independent candidate model assumes a secret weakness with an
   efficiently recognizable property occurring independently in eligible
   curves. It cannot rule out targeted constructions.
3. `publishedSuccess` is an illustrative mechanism for selection bias. A
   publication-only-after-success policy can make P(success | published)=1,
   even if individual attempts very rarely succeed.
4. Lean proves arithmetic implications given premises, not the premises' truth
   about a historical event.

## References

- [Mathlib conditional probability](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/ConditionalProbability.html)
- [SafeCurves rigidity](https://safecurves.cr.yp.to/rigid.html)
- [Filippo Valsorda's seed reconstruction](https://words.filippo.io/)

## License

MIT. See `LICENSE`.
