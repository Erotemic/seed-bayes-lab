"""Event-space definitions and slider assumptions shared by both UIs.

The first model is a finite three-world probability space; the second is a
separate conditional model of searches and publication. Keep their observations
E and T distinct so the displayed Bayesian deltas cannot be conflated.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    symbol: str
    definition: str
    qualification: str = ""


@dataclass(frozen=True)
class ParameterEntry:
    key: str
    symbol: str
    definition: str
    qualification: str = ""


BAYES_EVENTS = (
    Entry("Ω = {H, F, B}",
          "The exhaustive, mutually exclusive outcomes in the finite Bayes model.",
          "One published curve is modeled as belonging to exactly one world."),
    Entry("H", "No malicious attempt to plant a backdoor was made.",
          "The honest/no-attempt world; B is false."),
    Entry("F", "A malicious attempt was made, but it did not produce a planted backdoor.",
          "The attempted-but-failed world; B is false."),
    Entry("B", "A deliberately planted exploitable weakness is present in the published curve.",
          "This does not mean an accidental weakness, a vulnerable application, or malicious intent alone."),
    Entry("I = F ∪ B", "The designer intended or attempted to plant a backdoor.",
          "I can be true while B is false; P(B) = P(I) × P(B | I)."),
    Entry("¬B = H ∪ F", "The published curve has no deliberately planted backdoor.",
          "Includes both no-attempt and failed-attempt worlds."),
    Entry("E", "The published NIST prime-curve seeds match reconstructible lrand48 streams "
          "with plausible 1997–1998 timestamp initializations, including P-256 candidate 1,842.",
          "A retrospective observation. E does not establish impartial clock reading, no restarts, "
          "the stopping rule, or that a backdoor exists or does not exist."),
)

BAYES_QUANTITIES = (
    Entry("P(B)", "Probability of an intentionally planted backdoor before incorporating E.",
          "An illustrative prior, conditional on whatever background knowledge the model assumes."),
    Entry("P(B | E)", "Probability of that same event B after conditioning on E.",
          "Defined only if P(E) > 0."),
    Entry("P(I | E)", "Probability of malicious intent after observing E.",
          "This can differ in direction from the probability of successful backdooring."),
    Entry("P(E | H), P(E | F), P(E | B)",
          "Assumed likelihoods of observing the recovered evidence in each world.",
          "Hypothetical modeling inputs, not measured frequencies from the historical record."),
    Entry("Δupdate", "Posterior − prior, P(B | E) − P(B), in percentage points.",
          "The can-reverse indicator scans the sign of this quantity."),
    Entry("Δendpoint(x)", "P(B | E; x=end) − P(B; x=end), in percentage points.",
          "This control is fixed to one endpoint while all others remain at their current values. "
          "The result is independent of this control's current position."),
    Entry("Break-even(x)", "Position(s) of dial x where P(B | E) = P(B), holding all other controls fixed.",
          "Purple ticks mark isolated equality points; purple bars mark intervals. "
          "Interpolated points between discrete steps may not be selectable. "
          "Impossible evidence is never equality."),
)

SEARCH_EVENTS = (
    Entry("I", "Malicious intent is assumed certain in this separate search model.",
          "Every attempted construction seeks a deliberate backdoor."),
    Entry("T", "The designer actually uses the restricted timestamp method.",
          "T describes a stronger historical restriction than observing E."),
    Entry("U = ¬T", "The designer uses the alternative, less restricted method.",
          "T and U are exhaustive in this simplified two-method model."),
    Entry("K", "The adversary knows a usable, efficiently recognizable attack property.",
          "Knowledge probabilities can depend on the selected method."),
    Entry("B", "A planted backdoor is successfully produced by the attempted search.",
          "In this search model, success is tied to knowledge and an independent candidate search."),
    Entry("J", "The attempted curve is published.",
          "This model assumes P(J | B) = 1 and P(J | ¬B) = ρ."),
    Entry("E (first tab)", "Reconstructed historical seed provenance.",
          "NOT interchangeable with T. This second tab conditions on T among published curves."),
)

SEARCH_QUANTITIES = (
    Entry("P(B | J)", "Backdoor probability among published attempted curves, before observing T.",
          "Already conditions on publication."),
    Entry("P(B | J, T)", "Backdoor probability among published curves using method T.",
          "Defined only if P(J ∩ T) > 0."),
    Entry("q = 2^(−k)", "Hypothetical fraction of eligible curves exhibiting a recognizable weakness.",
          "Independence and efficient recognition are assumptions, not historical facts."),
    Entry("N = 2^min(b, c)", "Effective candidate count for freedom b and compute-budget c bits.",
          "The model treats the candidate tests as independent draws."),
    Entry("sT, sU", "Probability the attack succeeds under T and U, respectively.",
          "sT = P(K | T) × [1 − (1 − q)^NT], analogously for U."),
    Entry("ρ", "Probability a failed attempt is nevertheless published.",
          "A successfully planted backdoor always publishes in this toy model."),
    Entry("Δupdate (search)", "P(B | J, T) − P(B | J), in percentage points.",
          "This is a method-observation update, NOT an update from E."),
    Entry("Δendpoint (search)",
          "P(B | J,T; x=end) − P(B | J; x=end).",
          "Fix this dial to its endpoint; all other dials stay at their current values. "
          "Undefined if conditioning has probability zero."),
    Entry("Break-even(x) (search)", "Settings x for which P(B | J,T) = P(B | J).",
          "Search equality can hold on an entire range if both strategies have "
          "equal effective search budgets. Conditioning must be defined."),
)

BAYES_PARAMETERS = (
    ParameterEntry("prior_intent", "P(I)", "Prior chance the designer intended to plant a backdoor.",
                   "0.5 is a symmetric demonstration prior, not a historical estimate."),
    ParameterEntry("success_given_intent", "P(B | I)",
                   "Prior chance the published curve contains a deliberately planted backdoor, given intent.",
                   "This is a conditional success assumption."),
    ParameterEntry("likelihood_honest", "P(E | H)",
                   "Chance of observing the reconstructed evidence in the no-attempt world."),
    ParameterEntry("likelihood_failed", "P(E | F)",
                   "Chance of observing the reconstructed evidence after a failed malicious attempt."),
    ParameterEntry("likelihood_succeeded", "P(E | B)",
                   "Chance of observing the reconstructed evidence if the backdoor was planted successfully."),
)

SEARCH_PARAMETERS = (
    ParameterEntry("restricted_bits", "bT", "Log₂ number of candidate choices reachable using T.",
                   "A hypothetical candidate freedom, not a verified 1997 search effort."),
    ParameterEntry("unrestricted_bits", "bU", "Log₂ number of candidate choices reachable using U."),
    ParameterEntry("compute_bits", "c", "Log₂ number of candidates the attacker could evaluate."),
    ParameterEntry("rarity_bits", "k", "Negative log₂ frequency of eligible curves with the secret property."),
    ParameterEntry("know_restricted", "P(K | T)", "Chance the adversary knows a usable attack with T."),
    ParameterEntry("know_unrestricted", "P(K | U)", "Chance the adversary knows a usable attack with U."),
    ParameterEntry("prior_restricted", "P(T)", "Probability method T was selected before seeing success."),
    ParameterEntry("publish_failed", "ρ", "Chance a failed malicious attempt is still published."),
)



RESTRICTION_EVENTS = (
    Entry("I", "The designer attempted to plant a backdoor.",
          "We assume P(I|E)=P(I). This requires a particular likelihood under not-I."),
    Entry("B", "The published curve has a deliberately planted backdoor.",
          "B implies I; an accidental weakness is excluded."),
    Entry("E", "Observed historical reconstruction of the timestamp-seeded generation process.",
          "Same evidence as in the likelihood model, so the updates cannot be multiplied."),
    Entry("T", "Genuinely binding restriction on an attacker's candidate selection.",
          "Stronger than merely having a published seed compatible with lrand48."),
    Entry("not T", "No meaningfully binding restriction on attacker selection.",
          "T and not-T partition attempted designs, conditional on I."),
)

RESTRICTION_QUANTITIES = (
    Entry("p = P(I)", "Probability of malicious intent before E.",
          "P(I|E)=p is assumed, not derived from the seed history."),
    Entry("t = P(T|I)", "Prior belief in a genuinely restricting method."),
    Entry("eT = P(E|I,T)", "Likelihood of provenance evidence given intent and restriction."),
    Entry("eU = P(E|I,not T)", "Likelihood of provenance evidence given intent without restriction."),
    Entry("D = P(E|I)", "t×eT + (1−t)×eU.",
          "We additionally set P(E|not I)=D; this is the exact fixed-intent assumption."),
    Entry("P(T|I,E)", "t×eT / D, derived by Bayes' theorem.",
          "Undefined if D=0. Prior t=0 or 1 cannot move under possible evidence."),
    Entry("sU = P(B|I,not T)", "Success probability without effective restriction.",
          "Remains unchanged after E given I and not-T, by assumption."),
    Entry("sT = P(B|I,T)", "Success probability when restricted.",
          "Not forced below sU; the assertion sT≤sU is a testable modeling premise."),
    Entry("P(B)", "p×[(1−t)×sU+t×sT].",
          "Before conditioning on E."),
    Entry("P(B|E)", "p×[(1−P(T|I,E))×sU+P(T|I,E)×sT].",
          "Valid only for positive D under the stated invariance assumptions."),
    Entry("Δupdate", "p×t×(1−t)×(eT−eU)×(sT−sU)/D.",
          "Positive/negative sign determined by two differences when p>0, 0<t<1."),
    Entry("Break-even", "Δ=0 if p=0, t=0, t=1, eT=eU, or sT=sU (for D>0).",
          "No posterior when D=0, so impossible evidence is not equality."),
)

RESTRICTION_PARAMETERS = (
    ParameterEntry("restriction_intent", "p", "Prior probability of intent, held fixed by E.",
                   "If p=0, all conditionals on I are counterfactual."),
    ParameterEntry("restriction_before", "t", "Prior P(T|I)."),
    ParameterEntry("restriction_evidence_t", "eT", "P(E|I,T) likelihood if restricted."),
    ParameterEntry("restriction_evidence_u", "eU", "P(E|I,not T) likelihood if unrestricted."),
    ParameterEntry("restriction_success_u", "sU", "P(B|I,not T) unrestricted success chance."),
    ParameterEntry("restriction_success_t", "sT", "P(B|I,T) restricted success chance.",
                   "When sT>sU, the constrained method makes attack success more likely in this scenario."),
)

def all_parameter_keys() -> set[str]:
    return {e.key for e in (*BAYES_PARAMETERS, *SEARCH_PARAMETERS, *RESTRICTION_PARAMETERS)}
