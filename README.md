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
  heatmap, and a no-server budget slider. Every graph has labeled X/Y axes;
  probability axes show percentages, search rarity uses bits, and heatmap
  colorbars report the evidence update in percentage points.
- `src/seed_bayes_lab/app.py`: Streamlit explorer with editable assumptions, explicit
  recovered-evidence description, source links, and reset-all button.
- `src/seed_bayes_lab/sensitivity.py`: complete one-dial-at-a-time directional
  scans, including flip detection, fixed endpoint effects, break-even roots and
  equality intervals.
- `src/seed_bayes_lab/offline.js`: equivalent JavaScript calculations for the
  full offline HTML application, with parity tests against Python.
- `src/seed_bayes_lab/evidence.py`: shared observed-evidence definition.
- `src/seed_bayes_lab/glossary.py`: shared finite-world events, search/publication
  events, all thirteen input meanings, and display notation for both interfaces.
- `src/seed_bayes_lab/ui_state.py`: centralized **neutral evidence** defaults, illustrative
  evidence-likelihood presets, and reset behavior.
- `examples/interactive_demo.html`: generated, self-contained offline explorer
  with all thirteen sliders, icon-led endpoint effects, purple break-even
  ticks/segments, a detailed notation glossary, live charts, reset, and
  direction-reversal hints.
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

Open the local address printed by Streamlit. Both apps initially set
`P(E | H) = P(E | F) = P(E | B) = 0.50`, so the recovered evidence causes
**no prior-to-posterior change** by assumption. This is a symmetric
*likelihood example*, not a claim that the actual discovery is neutral.
Choose **Favors benign** (`0.80 / 0.60 / 0.20`) or **Favors backdoor**
(`0.20 / 0.60 / 0.80`) to explore alternative assumptions, or edit the
likelihood sliders individually. Presets change only the three evidence
likelihoods; they do not reset intent, success, or search settings. The
**Reset all assumptions** button restores all controls, including the neutral
baseline. A compact evidence
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

The global reset restores all thirteen controls to the neutral baseline in either interface. Both
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

A **purple tick on a slider** marks a break-even value where the evidence
update equals zero (posterior equals prior). A **purple segment** marks a
range of such values. The tick is calculated with every other dial fixed;
changing the marked dial itself leaves its tick in place, while changing a
different dial can move the tick. The offline HTML draws ticks directly over
the slider tracks. Because Streamlit's native slider does not expose custom
tick positions, its version draws an aligned companion ruler immediately
beneath the native slider.

For roots between slider steps, the tick shows an **approximately equal**
interpolated value; it may not be possible to select that exact value with
the discrete slider. A missing tick means no zero was detected within the
range. Undefined conditioning is not equality. Roots are found using the
algebraic numerator of the probability update, so an extremely small but
nonzero update is not falsely labeled equal merely because it rounds to
"≈0 pp". In search scenarios where finite-precision arithmetic saturates
at probability 1, the calculation preserves the strict sign implied by
unequal search budgets rather than drawing a false equality interval. The
numerical scan could still miss an interior tangency without sign change.

The **CAN REVERSE** indicator scans the same evidence-update delta at
*all selectable* positions (including interior ones), and reports whether
moving this dial can change the sign relative to its current configuration.
An interpolated zero between steps need not be selectable. Equality is not
a strict reversal. The glossary defines all events and parameters. Evidence
E is not the same as search-model observation T.

The default `P(I)=0.50` is a **symmetric demonstration prior**, not a factual
assessment or a claim that maximum entropy automatically represents ignorance.
The neutral evidence likelihoods are likewise a *deliberate baseline*, not an
empirical likelihood ratio.

An alternative without uv:

```bash
python -m pip install -e '.[dev,app]'
python -m pytest
python -m streamlit run src/seed_bayes_lab/app.py
```

## Lean formalization and code conformance

The Lean source now covers the complete finite Bayesian update, the exact
break-even numerator, both signs of the update, the publication-conditioned
method mixture, and independent-trial search probability with natural trial
counts. This intentionally stops short of a formal cryptographic attack or a
floating-point JavaScript runtime.

Install [elan](https://github.com/leanprover/elan), with Lean v4.32.0 pinned
by `lean-toolchain`. Mathlib is pinned by `lakefile.toml`.

```bash
lake update
lake exe cache get
uv sync --extra dev --extra app
uv run python scripts/verify_formal.py
```

`verify_formal.py` is strict: it checks the generated Lean fixture module,
requires `lake build SeedBayes` to pass, and runs the full Python test suite
(including Node.js comparisons against the actual offline HTML math kernels).
Missing Lean or Node makes the strict check fail rather than silently skip.
The ordinary `uv run pytest` command works without a Lean installation.

The core conformance bridge consists of:

- `tests/formal_cases.json`: 24 exact rational model scenarios.
- `scripts/generate_formal_fixtures.py`: generates `SeedBayes/Fixtures.lean`
  with exact rational expected results and `norm_num` proofs.
- `tests/test_formal_conformance.py`: independently exercises the production
  Python and offline JavaScript calculations against those same answers.
- `SeedBayes/Calculations.lean`, `Publication.lean`, `Search.lean`: symbolic
  results valid for whole families of probabilities, not just examples.

You can regenerate the proofs with
`python scripts/generate_formal_fixtures.py`, then check with
`lake build SeedBayes`. The fixture generator refuses to verify a stale
Lean file.

**Verification:** Run `uv run pytest` to check Python, the offline JavaScript
kernels (when Node.js is installed), and cross-language fixtures. The strict
`uv run python scripts/verify_formal.py` additionally requires Lean and
Mathlib, builds `SeedBayes`, and checks fixture synchronization. Test counts
and previously observed build statuses are deliberately not baked into this
README; validate your current checkout rather than trusting a stale count.
See [docs/proof-map.md](docs/proof-map.md) for a theorem-to-function audit
and the remaining boundaries of formalization.


### Source-level theory links (MAGNET)

Python computations and conformance tests now carry static
[`aiq-magnet-theory`](https://pypi.org/project/aiq-magnet-theory/)
annotations. This tiny runtime dependency consists of **no-op** decorators:

```python
import magnet_theory as theory

@theory.approximates("SeedBayes.Search.Independent")
def independent_search_success(rarity_bits: float, trials_bits: float) -> float:
    ...
```

A matching [MAGNET theory index](theory/index.yaml) resolves stable annotation
IDs to exact Lean declarations and named proof premises; see
[the mapping spec](theory/link-spec.yaml). For example,
`SeedBayes.Bayes.UpdateDelta::hE` records the assumption that the evidence
probability is nonzero. The source distinguishes `checks` (runtime guard),
`assumes` (relies on an obligation proved/checked elsewhere), `approximates`
(floating-point or bits-interpolated code), and `tests` (numeric conformance
against rational Lean fixtures).

The full MAGNET package adds a static extractor and premise-coverage report,
without executing annotated application code. If it is installed, generate a
report using:

```bash
python scripts/report_theory.py --output theory/report.json
```

The core `aiq-magnet-theory` package is installed by default; **full
`aiq-magnet` is optional** and only needed to generate that report.
`uv run pytest` validates the index against current Lean declarations and
Python annotations without requiring the full MAGNET package.

**Scope:** these annotations record which claims and premises code relates to.
They do not prove Python semantics, floating-point correctness, or the
historical likelihood assumptions. The strict Lean-plus-Python/JavaScript
fixture checks described above remain the executable conformance gate.

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

$$
 P(B\mid E)<P(B)\quad\Longleftrightarrow\quad
 P(E\mid B)<P(E\mid\neg B).
$$

The theorem `posterior_lt_prior_iff_likelihood_ratio` states this for the
finite model. The input likelihoods are not derived from the seed discovery:
they **are the assumptions whose plausibility needs to be investigated**.

For a separately assumed *ex ante* choice of generator, write `s_T` for
conditional attack success with the timestamp method and `s_U` for the
alternative. If `alpha` is the prior chance of T, then:

$$
 s_T - (\alpha s_T +(1-\alpha)s_U)
   = (1-\alpha)(s_T-s_U).
$$

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
