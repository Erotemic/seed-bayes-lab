import Mathlib

/-!
# Finite Bayesian updates for deliberate parameter selection

There are exactly three mutually exclusive worlds:
* `honest`: no deliberate attempt to implant a backdoor;
* `failed`: the designer tried to implant a backdoor but did not succeed;
* `backdoor`: an attempt succeeded and the published parameter is backdoored.

A prior assigns masses to these worlds. An evidence model assigns a
conditional likelihood for an observed event in each world. We work with
real-valued finite probabilities, not measure-theoretic conditional probability.

The main theorems are algebraic identities with explicit nonzero/positivity
conditions. They **do not** assert anything about a real cryptographic curve.
-/

namespace SeedBayes

/-- Probabilities for the three mutually exclusive worlds. -/
structure Prior where
  honest : ℝ
  failed : ℝ
  backdoor : ℝ
  honest_nonneg : 0 ≤ honest
  failed_nonneg : 0 ≤ failed
  backdoor_nonneg : 0 ≤ backdoor
  sum_one : honest + failed + backdoor = 1

/-- The likelihood of seeing evidence E in each world. -/
structure Likelihood where
  honest : ℝ
  failed : ℝ
  backdoor : ℝ
  honest_nonneg : 0 ≤ honest
  failed_nonneg : 0 ≤ failed
  backdoor_nonneg : 0 ≤ backdoor
  honest_le_one : honest ≤ 1
  failed_le_one : failed ≤ 1
  backdoor_le_one : backdoor ≤ 1

/-- Unconditional prior probability of malicious intent. -/
def priorIntent (p : Prior) : ℝ := p.failed + p.backdoor

/-- Unconditional prior probability of a successfully planted backdoor. -/
def priorBackdoor (p : Prior) : ℝ := p.backdoor

/-- Prior mass for the absence of a planted backdoor. -/
def priorNotBackdoor (p : Prior) : ℝ := p.honest + p.failed

/-- Probability of evidence E (the law of total probability). -/
def evidenceMass (p : Prior) (e : Likelihood) : ℝ :=
  p.honest * e.honest + p.failed * e.failed + p.backdoor * e.backdoor

/-- Joint mass P(intent and E), before normalization. -/
def intentEvidenceMass (p : Prior) (e : Likelihood) : ℝ :=
  p.failed * e.failed + p.backdoor * e.backdoor

/-- Joint mass P(not backdoored and E), before normalization. -/
def notBackdoorEvidenceMass (p : Prior) (e : Likelihood) : ℝ :=
  p.honest * e.honest + p.failed * e.failed

/-- P(backdoor | intent), only interpreted when prior intent has positive mass. -/
noncomputable def successGivenIntent (p : Prior) : ℝ :=
  p.backdoor / priorIntent p

/-- P(backdoor | E), only interpreted when P(E) > 0. -/
noncomputable def posteriorBackdoor (p : Prior) (e : Likelihood) : ℝ :=
  p.backdoor * e.backdoor / evidenceMass p e

/-- P(intent | E), only interpreted when P(E) > 0. -/
noncomputable def posteriorIntent (p : Prior) (e : Likelihood) : ℝ :=
  intentEvidenceMass p e / evidenceMass p e

/-- P(backdoor | intent, E), when both conditioning events have positive mass. -/
noncomputable def posteriorSuccessGivenIntent (p : Prior) (e : Likelihood) : ℝ :=
  p.backdoor * e.backdoor / intentEvidenceMass p e

/-- P(not backdoored | E). -/
noncomputable def posteriorNotBackdoor (p : Prior) (e : Likelihood) : ℝ :=
  notBackdoorEvidenceMass p e / evidenceMass p e

/-- P(E | not backdoored), when the prior non-backdoor mass is positive. -/
noncomputable def evidenceGivenNotBackdoor (p : Prior) (e : Likelihood) : ℝ :=
  notBackdoorEvidenceMass p e / priorNotBackdoor p

/-- The unnormalized posterior masses sum to P(E). -/
theorem evidence_partition (p : Prior) (e : Likelihood) :
    evidenceMass p e =
      intentEvidenceMass p e + p.honest * e.honest := by
  unfold evidenceMass intentEvidenceMass
  ring

/-- Bayes' formula in cross-multiplied form. -/
theorem bayes_backdoor_cross (p : Prior) (e : Likelihood)
    (hE : evidenceMass p e ≠ 0) :
    posteriorBackdoor p e * evidenceMass p e =
      priorBackdoor p * e.backdoor := by
  unfold posteriorBackdoor priorBackdoor
  field_simp [hE]

/-- Multiplicative decomposition of the prior backdoor probability. -/
theorem prior_factorization (p : Prior) (hI : priorIntent p ≠ 0) :
    priorBackdoor p = priorIntent p * successGivenIntent p := by
  unfold priorBackdoor successGivenIntent
  field_simp [hI]

/-- Multiplicative decomposition after conditioning on evidence. -/
theorem posterior_factorization (p : Prior) (e : Likelihood)
    (hE : evidenceMass p e ≠ 0)
    (hIE : intentEvidenceMass p e ≠ 0) :
    posteriorBackdoor p e =
      posteriorIntent p e * posteriorSuccessGivenIntent p e := by
  unfold posteriorBackdoor posteriorIntent posteriorSuccessGivenIntent
  field_simp [hE, hIE] <;> ring

/-- Cross-multiplied posterior odds form of Bayes' rule. -/
theorem bayes_odds_cross (p : Prior) (e : Likelihood)
    (hE : evidenceMass p e ≠ 0) :
    posteriorBackdoor p e * notBackdoorEvidenceMass p e =
      posteriorNotBackdoor p e * (priorBackdoor p * e.backdoor) := by
  unfold posteriorBackdoor posteriorNotBackdoor priorBackdoor
  field_simp [hE]

/-- The posterior changes downward precisely when the evidence likelihood
    under a backdoor is below its unconditional likelihood. -/
theorem posterior_lt_prior_iff (p : Prior) (e : Likelihood)
    (hE : 0 < evidenceMass p e) (hB : 0 < p.backdoor) :
    posteriorBackdoor p e < priorBackdoor p ↔
      e.backdoor < evidenceMass p e := by
  unfold posteriorBackdoor priorBackdoor
  constructor
  · intro h
    have hmul : p.backdoor * e.backdoor <
        p.backdoor * evidenceMass p e := by
      have h' := (div_lt_iff₀ hE).mp h
      nlinarith
    exact (mul_lt_mul_iff_of_pos_left hB).mp hmul
  · intro h
    apply (div_lt_iff₀ hE).mpr
    have hmul := (mul_lt_mul_iff_of_pos_left hB).mpr h
    nlinarith

/-- The total mass of the complement of B plus the mass of B is one. -/
theorem complement_partition (p : Prior) :
    priorNotBackdoor p + p.backdoor = 1 := by
  unfold priorNotBackdoor
  linarith [p.sum_one]

/-- The direction of the Bayesian update is determined by the evidence's
    relative likelihood under B versus not-B. All the quantities on the right
    are conditional likelihoods, NOT empirical estimates. -/
theorem posterior_lt_prior_iff_likelihood_ratio (p : Prior) (e : Likelihood)
    (hE : 0 < evidenceMass p e) (hB : 0 < p.backdoor)
    (hN : 0 < priorNotBackdoor p) :
    posteriorBackdoor p e < priorBackdoor p ↔
      e.backdoor < evidenceGivenNotBackdoor p e := by
  rw [posterior_lt_prior_iff p e hE hB]
  have hNE : notBackdoorEvidenceMass p e =
      priorNotBackdoor p * evidenceGivenNotBackdoor p e := by
    unfold evidenceGivenNotBackdoor
    field_simp [ne_of_gt hN] <;> ring
  have hZ : evidenceMass p e =
      p.backdoor * e.backdoor + notBackdoorEvidenceMass p e := by
    unfold evidenceMass notBackdoorEvidenceMass
    ring
  rw [hZ, hNE]
  have hMass : p.backdoor + priorNotBackdoor p = 1 := by
    linarith [complement_partition p]
  have hIdent : e.backdoor =
      (p.backdoor + priorNotBackdoor p) * e.backdoor := by
    rw [hMass]
    ring
  constructor
  · intro h
    have hmul : priorNotBackdoor p * e.backdoor <
        priorNotBackdoor p * evidenceGivenNotBackdoor p e := by
      nlinarith [hIdent]
    exact (mul_lt_mul_iff_of_pos_left hN).mp hmul
  · intro h
    have hmul := (mul_lt_mul_iff_of_pos_left hN).mpr h
    nlinarith [hIdent]

/-- When intent is certain, the probability of a planted backdoor is the
    conditional success probability given intent, even after evidence. -/
theorem certain_intent (p : Prior) (e : Likelihood)
    (h : p.honest = 0) :
    posteriorBackdoor p e = posteriorSuccessGivenIntent p e := by
  simp [posteriorBackdoor, posteriorSuccessGivenIntent,
    evidenceMass, intentEvidenceMass, h]

/-- A rational-valued example, with prior P(B)=1/4 and posterior P(B|E)=1/7. -/
noncomputable def examplePrior : Prior where
  honest := 1 / 2
  failed := 1 / 4
  backdoor := 1 / 4
  honest_nonneg := by norm_num
  failed_nonneg := by norm_num
  backdoor_nonneg := by norm_num
  sum_one := by norm_num

noncomputable def exampleEvidence : Likelihood where
  honest := 1 / 2
  failed := 1 / 2
  backdoor := 1 / 4
  honest_nonneg := by norm_num
  failed_nonneg := by norm_num
  backdoor_nonneg := by norm_num
  honest_le_one := by norm_num
  failed_le_one := by norm_num
  backdoor_le_one := by norm_num

example : posteriorBackdoor examplePrior exampleEvidence = 1 / 7 := by
  norm_num [posteriorBackdoor, evidenceMass, examplePrior, exampleEvidence]

end SeedBayes
