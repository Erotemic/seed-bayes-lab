# Lean ↔ production calculation map

This document maps the mathematical calculations to the **actual** Python and
browser code. The historical seed evidence and any hypothetical probability
inputs are **not** established by Lean: only the conditional algebra is.

## Core Bayes and exact slider break-even

| Lean declaration | Production code | Covered identity |
|---|---|---|
| `evidence_partition`, `bayes_backdoor_cross` | `model.update()` | Finite normalization and Bayes' rule |
| `prior_factorization`, `posterior_factorization` | `Prior.success_given_intent`, `Update.conditional_success_after` | Backdoor = intent × success |
| `bayes_odds_cross` | `Update.bayes_factor_backdoor` | Odds identity |
| `posterior_lt_prior_iff_likelihood_ratio` | `Update.direction()` | Downward update iff evidence favors not-B |
| `certain_intent` | `Prior.from_intent_success(1, ...)` | Intent-certain scenario |
| `priorOfIntent`, `posterior_of_intent_agrees` | `Prior.from_intent_success`, `offline.js:finiteBayes` | Three-world prior and five-slider posterior agree |
| `bayes_delta_formula` | `Update.delta_backdoor`, `sensitivity._zero_numerator` | Exact polynomial numerator of delta |
| `bayes_delta_negative_iff`, `bayes_delta_positive_iff` | `sensitivity.direction` | Strict sign of update with positive evidence |
| `bayes_break_even_iff`, `bayes_break_even_likelihood_iff` | `sensitivity.break_even_regions` | Algebraic conditions for equal posterior and prior |
| `scalar_delta_agrees`, `scalar_numerator_agrees` | `offline.js:finiteBayes`, `sensitivity._zero_numerator` | Scalar formulas are the same finite model |

## Search and publication

| Lean declaration | Production code | Covered identity |
|---|---|---|
| `restricted_delta`, `restricted_nonincreasing` | `search.method_observation_update(...,rho=1)` | Ex ante method-mixture direction |
| `independent_success_zero`, `independent_success_succ` | `search.independent_search_success`, `offline.js:independentSearch` | `1-(1-q)^N` and its recurrence for natural-number trials |
| `independent_success_mono` | Same | More independent trials never hurts for `0≤q≤1` |
| `effective_success_mono_freedom`, `effective_success_mono_budget` | `search.effective_search_success` | Increasing candidate or compute count cannot reduce success |
| `planted_success_mono_freedom` | `search.planted_success` | Monotonicity after multiplying by a nonnegative chance of knowing the attack |
| `publicationMass`, `mixturePublicationMass` | `search.publish_probability`, `search.method_observation_update` | Publication normalization |
| `joint_restricted_publication` | `MethodUpdate.after`, `offline.js:publishedMethodUpdate` | `P(B|J,T) = st/P(J|T)` with `P(T)>0` |
| `publication_delta_formula` | `MethodUpdate.delta`, `offline.js:publishedMethodUpdate` | Exact difference `rho(1-alpha)(st-su)/(P(J|T)P(J))` |
| `publication_break_even_iff` | `sensitivity._zero_numerator` | Equal conditional posteriors iff one of three factors is zero |
| `publication_restricted_nonincreasing` | `search.method_observation_update` | Direction with positive publication denominators |
| `restricted_publish_only_success` | `search.method_observation_update(...,rho=0)` | Publishing only successes conditions away failures |

The Lean search model uses natural **counts** of independent trials. Python
and JavaScript also offer a real-valued interpolation in bits, implemented by
`expm1`/`log1p`; the floating-point interpolation and chart root detection
are **not** fully formalized in Lean.


## MAGNET static source annotations

The [MAGNET index](../theory/index.yaml) binds stable statement IDs to local
Lean declarations. The [link specification](../theory/link-spec.yaml) tells the
full MAGNET static analyzer which Python source files to scan. References such
as `SeedBayes.Publication.Delta::hPt` identify named hypotheses, not guessed
source line numbers.

The production modules use `@theory.approximates(...)` because the Lean
identities are exact real arithmetic while the implementation evaluates them
using floating-point operations. Conformance tests use `@theory.tests(...)`
to point to the claims exercised by Lean-proved rational fixtures. `assumes`
marks proof obligations that a numerical result depends upon; `checks` marks
explicit domain guards. Neither relation means MAGNET has proved Python
implements Lean.

`aiq-magnet-theory` supplies these inert decorators without pulling in the
full MAGNET toolkit. For a full static link and premise-coverage report, install
`aiq-magnet` separately and run `python scripts/report_theory.py`.
The repository's normal pytest suite checks the links without requiring that
optional dependency.

## The cross-language proof bridge

`tests/formal_cases.json` specifies exact rational input parameters for:

- 9 Bayesian world/evidence configurations, including zero and certain intent,
  evidence for and against a backdoor, and an exact break-even.
- 8 publication-conditioned method configurations, including publication-only
  success, equal success, and positive/negative updates.
- 7 independent-search configurations with natural trial counts `2^b`.

`scripts/generate_formal_fixtures.py` evaluates those formulas using Python's
exact `fractions.Fraction`, then produces `SeedBayes/Fixtures.lean`. This is not
taking a floating-point output from the production model as an oracle: the
Lean file independently **proves** each expected value with `norm_num`. The
proof file is imported by `SeedBayes.lean`, so `lake build SeedBayes` checks it.

`tests/test_formal_conformance.py` checks that the generated proof file is
fresh, then evaluates the **production** `model.py`, `search.py`, and `offline.js`
functions against the same exact rational answers. Existing property tests
and Python–JavaScript parity tests cover more slider settings and edge cases.

Run every check with a single strict command:

```bash
uv run python scripts/verify_formal.py
```

It requires an installed Lean v4.32.0 toolchain, Mathlib cache/dependencies,
Node.js, and the Python dev dependencies. It exits with a failure if Lean
cannot build or any parity test fails. The ordinary Python suite is also
runnable without Lean via `uv run pytest`.

**Verification boundary:** Proving the formulas and the finite exact test
vectors does not prove arbitrary IEEE-754 evaluations, numerical root finding,
Plotly rendering, or the correctness of assumed historical likelihoods. A
successful Lean build plus conformance suite substantially improves confidence
in the code's arithmetic while keeping those limits explicit.

**Status in the artifact-authoring environment:** Python/JavaScript tests were
run; the Lean toolchain and Mathlib were unavailable, so the new Lean source
has not been compiled here. Successful compilation must be confirmed on a
Lean-equipped machine before describing the overlay as formally verified.
