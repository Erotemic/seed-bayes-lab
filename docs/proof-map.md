# Formal theorem to Python map

| Lean declaration | Python calculation | Statement |
|---|---|---|
| `evidence_partition` | `update()` | Evidence normalization from three mutually exclusive worlds |
| `bayes_backdoor_cross` | `update()` | Cross-multiplied Bayes rule for B |
| `prior_factorization` | `Prior.success_given_intent` | P(B) = P(I) P(B|I) |
| `posterior_factorization` | `Update.conditional_success_after` | P(B|E) = P(I|E) P(B|I,E) |
| `bayes_odds_cross` | `Update.bayes_factor_backdoor` | Cross-multiplied odds relation |
| `posterior_lt_prior_iff` | `Update.delta_backdoor` | P(B|E) < P(B) iff l_B < P(E) |
| `posterior_lt_prior_iff_likelihood_ratio` | `Update.likelihood_given_no_backdoor` | P(B|E) < P(B) iff l_B < P(E|not B) |
| `certain_intent` | `Prior.from_intent_success(1, ...)` | P(B|E) = P(B|I,E) when I is certain |
| `restricted_delta` | `method_observation_update(..., rho=1)` | Exact update for ex ante method choice |
| `restricted_nonincreasing` | `method_observation_update(..., rho=1)` | Direction when sT <= sU |
| `restricted_strict` | same | Strict version |
| `publish_only_success` | `method_observation_update(..., rho=0)` | Publication-only-on-success selection effect |
| `always_publish` | `method_observation_update(..., rho=1)` | Publication is uninformative if universal |

The numeric independent-candidate formula has not been formalized in Lean.
It is a separate hypothetical cryptanalytic model and tested numerically in
`tests/test_search.py`. The primary Lean objective is Bayesian correctness.
