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
`prior_factorization`, `posterior_factorization`.

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

The code uses `expm1` and `log1p` to avoid cancellation. It does not assume
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
true. The Lean toolchain was unavailable at authoring time; run `lake build`.

## UI reset behavior

All Streamlit sliders share explicit defaults in `ui_state.py`. The global
`Reset all assumptions` button restores all tabs. The self-contained HTML
demo has a separate reset for the compute-budget slider and axis zoom; it
provides only a fixed set of scenarios and not the full Streamlit inputs.
