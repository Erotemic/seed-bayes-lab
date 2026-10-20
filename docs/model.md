# Bayesian model and assumptions

## The target event

`B` means a successfully planted, deliberate mathematical weakness in the
published curve parameters. `I` means intent to try. By definition `B` implies
`I`. An accidental flaw is not `B`; it requires another event class if included.
The three exhaustive worlds in `Prior` are:

| World | Event | Prior mass | Evidence likelihood |
|---|---|---:|---:|
| H | not I | h | l_H |
| F | I and not B | f | l_F |
| B | I and B | b | l_B |

with nonnegative masses `h + f + b = 1` and likelihoods in `[0,1]`.

The application uses a specific historical observation `E`: published NIST
prime-curve seeds reproduce as outputs from `lrand48` streams initialized with
values corresponding to Unix timestamps in 1997-1998. P-256 matches candidate
1842. This reconstruction does not prove that the original designers used the
clock impartially or never restarted. See `src/seed_bayes_lab/evidence.py` for
the UI text and primary-source links. **Numerical likelihoods are assumptions**
about how likely this composite observation is under each world, not empirical
estimates obtained from seed data.

## Starting assumptions and illustrative presets

The default three evidence likelihoods are all `0.50`:
`P(E | H) = P(E | F) = P(E | B)`. Under this **neutral evidence** baseline,
conditioning on E leaves all three world probabilities unchanged, provided E
has positive probability. This is a useful reference state for testing the
sign of an update, **not** an inference that the recovered historical evidence
is in fact neutral. Similarly, the default `P(I) = 0.50` is an illustrative
symmetric prior, not a historical estimate.

The interface offers two further *hypothetical* likelihood scenarios:

- **Favors benign:** `(0.80, 0.60, 0.20)` for `(H, F, B)`; this was the
  original demo's default before the neutral-baseline change.
- **Favors backdoor:** `(0.20, 0.60, 0.80)` for `(H, F, B)`.

Selecting a preset changes only these three inputs. Custom edits are allowed,
and Reset restores the neutral baseline. Nothing in the historical reconstruction
calibrates the three numbers, and presets are not statements of historical
plausibility. The search/publication tab has its own observation and retains
its independent default settings.

This observed `E` has evidence probability

`Z = h*l_H + f*l_F + b*l_B`.

When `Z > 0`, conditioning gives:

- `P(B | E) = b*l_B / Z`;
- `P(I | E) = (f*l_F + b*l_B) / Z`;
- `P(B | I) = b / (f+b)` if `f+b > 0`;
- `P(B | I,E) = b*l_B / (f*l_F+b*l_B)` when its denominator is positive.

Consequently:

`P(B|E) = P(I|E) * P(B|I,E)`

and, when prior conditionals are defined,

`P(B) = P(I) * P(B|I)`.

Dividing those identities gives the intent/success multiplier decomposition
from the discussion, provided none of the required denominators is zero.

## What determines the update's direction

If `0 < b < 1` and `Z > 0`, then

`P(B|E) < b  iff  l_B < P(E|not B)`

where `P(E|not B) = (h*l_H+f*l_F)/(h+f)`.

The strict inequality reverses for an increased posterior, and equality means
no update. The ratio of these two likelihoods is the **Bayes factor**:

`BF_{B:notB} = l_B / P(E|not B)`.

Thus the sign comes from the relative evidence likelihood, not solely from
knowing that the algorithm's candidate set is smaller.

With `h=0` (intent certain), the sign still depends on `l_B` versus `l_F`.
With `f=0` and `h=0` (success certain), no evidence of positive prior
probability can change P(B)=1.

Lean: `posterior_lt_prior_iff_likelihood_ratio`, `certain_intent`,
`prior_factorization`, `posterior_factorization`, and the new
`bayes_delta_formula` / `bayes_break_even_likelihood_iff`. These prove that
when E is possible:

`P(B|E)-P(B) = b * ((h+f)*l_B - h*l_H - f*l_F) / Z`.

This is the exact polynomial numerator used by the break-even tick logic;
it is not an approximation based on rounded percentages.

## Search mechanism: deliberately additional assumptions

The Plotly curves for candidate searching assume:

1. A designer **knows** a usable, efficiently recognizable secret weakness
   with probability `p_known` (supplied rather than inferred).
2. Conditional on that knowledge, distinct eligible candidate curves each
   satisfy the secret property independently with chance `q = 2^-k`.
3. An attacker has access to `2^freedom_bits` candidates and can evaluate
   `2^budget_bits` of them, so trials are `min` of these two counts.
4. The search algorithm succeeds if it sees at least one vulnerable candidate.

Under these assumptions:

`search_success = 1 - (1 - 2^-k) ** (2**min(freedom_bits,budget_bits))`.

`success_probability = p_known * search_success`.

Lean `SeedBayes/Search.lean` proves the Bernoulli recurrence and monotonicity
for a **natural number of independent trials**, as well as min(freedom,budget)
monotonicity. `SeedBayes/Fixtures.lean` checks exact probability examples for
integer bit counts. For fractional UI slider coordinates, the code uses
`expm1` and `log1p` to avoid cancellation. It does not assume
that every secret attack works this way. Correlated vulnerabilities, adaptive
construction, special algebraic structure, ability to recognize weaknesses,
and procedural legitimacy are not proved by this formula.

## How method choice changes the answer

Assume the designer chooses between methods T and U *before* trying the
attack. Let `alpha = P(T)` and method-specific success rates be `sT,sU`.
Assume the observation tells us which method was used without error.

Without publication selection:

`P(B) = alpha*sT + (1-alpha)*sU`;

`P(B | observed T) = sT`.

The exact difference is `(1-alpha)*(sT-sU)`. If `sT <= sU`, this is
nonpositive. The Lean theorem `restricted_nonincreasing` encodes that algebra.

**Crucial:** Search-set inclusion can show that an *optimal attacker with the
same capabilities* is no worse off with more available candidates. That alone
does not prove `sT <= sU` after conditioning on **which kind of adversary would
choose each method**, if available attack capabilities differ between the
methods. The app permits different `p_known` inputs to demonstrate this.

## Conditioning on publication

For each method g, suppose an attempt succeeds with probability `s_g`. All
successful attempts are published, and a failed attempt is published with
probability `rho` independent of method. The publication probability is

`P(Published | g) = s_g + rho*(1-s_g)`.

Before learning g, after learning only that a curve was published:

`P(B | Published) = (alpha*sT + (1-alpha)*sU) /
    (alpha*P(Published|T) + (1-alpha)*P(Published|U))`.

After learning the published method was T:

`P(B | Published,T) = sT / P(Published|T)`.

The exact delta between observing T and not observing it, given publication,
is proved in `SeedBayes/Publication.lean`:

`P(B|J,T)-P(B|J) = rho*(1-alpha)*(sT-sU)/(P(J|T)*P(J))`.

When the denominators are positive, the equality cases are `rho=0`,
`alpha=1`, or `sT=sU`. A conditional P(B|J,T) is defined only if the
method T has positive prior probability. The Lean proof states the needed
nonzero/positivity assumptions, and Python explicitly returns `None` for
impossible observations.

At `rho=1`, publication provides no evidence. At `rho=0`, and for positive
success chance, every published curve is successful by construction. This is
not an assertion about how real standards bodies choose curves; it shows why
publication assumptions must be stated explicitly.

## Why the 2026 discovery does not settle the premises

The reconstruction supports that certain published seeds are outputs of a
1990s generator initialized to values corresponding to timestamps. It does
not prove that the programmers used an actual clock read, that they never
restarted it, or that the recovered first acceptable candidate was selected
without extra undisclosed criteria. Effective search budgets and the
frequency / detectability of undiscovered secret weaknesses are also unknown.

**The model does not assign priors to these unknown historical facts.** It
lets the user ask under which precise assumptions the Bayesian direction
changes.

## Reproducibility / proof boundary

Python tests exercise the three-world identities, Bayes odds, zero-probability
cases, search monotonicity and publication selection. Lean files prove the
finite algebra for symbolic real variables (with positivity assumptions).
Neither numerical tests nor Lean can establish that the historical inputs are
true. The additional symbolic identities and 24 exact regression configurations
are in `SeedBayes/Calculations.lean`, `SeedBayes/Publication.lean`,
`SeedBayes/Search.lean`, and `SeedBayes/Fixtures.lean`. Python and the offline
JavaScript are checked against the same exact values; see
[proof-map.md](proof-map.md). The Lean toolchain was unavailable at authoring
time; run `lake build SeedBayes` before claiming those new proofs are verified.

## Offline/Streamlit interactions and one-dial sensitivity

Both the Streamlit interface and the fully self-contained HTML application
use the same thirteen hypothetical controls, reset defaults, observation
labels, and probability formulas. The standalone HTML bundles Plotly and
requires no server. JavaScript numerical calculations are tested against the
Python `model.py` and `search.py` implementations, including boundary cases.

The prior `P(I)=0.50` is a symmetric illustrative default, not an empirical
claim and not a unique representation of an absence of knowledge. The two
Bayesian output labels, `P(B)` and `P(B | E)`, refer to the **same backdoor
event** before and after conditioning on the stated evidence. In the other
model the before/after pair explicitly conditions on a published curve.

For every slider `x`, `sensitivity.py` computes

`delta(x) = posterior_backdoor(x) - prior_backdoor(x)`.

All other sliders are held fixed. Every selectable position of `x` (not just
its endpoints) is enumerated, and the status answers whether the current
strict sign of `delta` can be reversed by moving only `x`. Equality `delta=0`
is *not* a reversal. A conditional probability whose denominator is zero is
reported as undefined and never counted as equality. Small floating-point
differences below `1e-13` are treated as numerically indistinguishable from
zero when classifying the sign.

The **left and right endpoint icons** show the *evidence update* at each
fixed endpoint, in percentage points, NOT posterior movement relative to
the dial's current position:

- Bayes tab: `P(B | E; x=endpoint) - P(B; x=endpoint)`.
- Search tab: `P(B | J,T; x=endpoint) - P(B | J; x=endpoint)`.

Other dials are held at their current values when evaluating an endpoint.
Thus the endpoint arrows for `x` are **invariant** when `x` itself moves,
but may change when other dials move. Crucially, if the dial changes a
prior, the prior in the subtraction must also be evaluated at that
endpoint, not at the current live setting. The small percentage underneath
is the posterior at that endpoint. Arrows indicate the sign of the
evidence update, including equality or undefined conditioning.

The **CAN REVERSE** status and full update range scan every selectable
position of that same evidence-update formula, including interior extrema.
Equality is not a strict reversal; undefined conditioning is not zero.
The glossary specifies every event and distinguishes observation E from T.

This sensitivity test is a property of the *current hypothetical model*, not
historical evidence for or against an actual backdoor.

## Break-even locations on interactive controls

For each dial `x`, the interfaces show purple break-even ticks where the
*evidence update* is zero, not where the posterior equals the posterior at
the dial's current live position. The Bayes tab solves

`P(B | E; x) - P(B; x) = 0`, conditional on `P(E)>0`.

The search tab solves

`P(B | J,T; x) - P(B | J; x) = 0`, conditional on `P(J∩T)>0`.

The other dials are fixed during this calculation; therefore changing `x`
does not move its own tick, but moving another dial can. A shaded purple
segment means equality holds on a range, for example when both search methods
are capped by the same compute budget. Interpolated roots are marked `≈`
when they fall between selectable positions. An undefined posterior never
creates a break-even tick.

To avoid falsely declaring break-even merely because a probability update
rounds to zero, the root detector analyzes the algebraic **numerator** of
`posterior - prior`, rather than the `1e-13` tolerance used for displaying
direction. For the search model, it preserves strict ordering between unequal
finite trial counts even when floating-point success probabilities round to
1. Search is numerical across the slider lattice with sign-changing roots
refined by bisection; undetected tangencies between samples remain possible.

Streamlit displays a companion ruler underneath its native slider (native
custom ticks are not supported). Standalone HTML overlays ticks directly on
its slider. The root finder itself is numerical; Lean proves the exact break-even
numerators and algebraic equality conditions, but not slider interpolation,
floating-point handling, or canvas placement.

## Alternative effective-restriction explanation of E

This is a **separate interpretation of the same historical evidence E**, not
an extra factor to apply after the three-world likelihood model. Let `T` mean
that the generation method truly restricted the adversary's ability to find
or construct a weak curve, not merely that the output matches `lrand48`.

Assumptions:

1. `p = P(I|E) = P(I)` (intent stays fixed).
2. `s = P(B|I,not T,E) = P(B|I,not T)` (baseline success invariant given method).
3. `P(B|I,T,E) = P(B|I,T) = r*s` with `0 <= r <= 1`.
4. `t0=P(T|I)` and `t1=P(T|I,E)` represent before/after restriction beliefs.
5. Publication selection is ignored. The backdoor event requires intent.

Applying total probability conditional on intent:

```text
P(B)   = p*s*[1 - t0*(1-r)]
P(B|E) = p*s*[1 - t1*(1-r)]
Delta  = -p*s*(t1-t0)*(1-r)
```

`SeedBayes/Restriction.lean` proves the difference and break-even identities,
and non-increase given `p>=0`, `s>=0`, `t0<=t1`, and `r<=1`. The probabilities
are hypothetical; Lean does not establish the historical assumptions.

**Conditioning support:** if `P(I)>0` and `P(E|I)>0`, a prior `t0=0` implies
`t1=0` and prior `t0=1` implies `t1=1`. The UI flags combinations that violate
this. At `P(I)=0`, `P(T|I)` is technically undefined, so conditional success
rates should be understood as counterfactual parameters. Their algebraic
extension remains useful for slider boundary illustrations.

The likelihood and restriction views have separate priors/sliders on purpose:
combining their deltas would double-count E without a larger joint model.
