import SeedBayes.Finite

/-!
# The finite Bayesian arithmetic used by the interactive application

The historical meaning of the observation is outside this formalization.
The proofs establish algebraic identities for the stated finite model;
all probabilities and likelihoods are inputs, not historical estimates.
-/

namespace SeedBayes

/-- Construct the three mutually exclusive worlds from `P(I)` and `P(B | I)`.
    This is exactly the construction in Python `Prior.from_intent_success`. -/
def priorOfIntent (intent success : ℝ)
    (hIntent0 : 0 ≤ intent) (hIntent1 : intent ≤ 1)
    (hSuccess0 : 0 ≤ success) (hSuccess1 : success ≤ 1) : Prior where
  honest := 1 - intent
  failed := intent * (1 - success)
  backdoor := intent * success
  honest_nonneg := sub_nonneg.mpr hIntent1
  failed_nonneg := mul_nonneg hIntent0 (sub_nonneg.mpr hSuccess1)
  backdoor_nonneg := mul_nonneg hIntent0 hSuccess0
  sum_one := by ring

/-- The scalar form used by the browser's five Bayesian sliders. -/
noncomputable def posteriorOfIntent
    (intent success likelihoodHonest likelihoodFailed likelihoodBackdoor : ℝ) : ℝ :=
  (intent * success * likelihoodBackdoor) /
    ((1 - intent) * likelihoodHonest +
     (intent * (1 - success)) * likelihoodFailed +
     (intent * success) * likelihoodBackdoor)

/-- Unconditional likelihood of E, written in the same five parameters. -/
def evidenceOfIntent (intent success lh lf lb : ℝ) : ℝ :=
  (1 - intent) * lh + (intent * (1 - success)) * lf +
    (intent * success) * lb

/-- Conditional intent probability P(I|E), also displayed by the browser. -/
noncomputable def posteriorIntentOfIntent
    (intent success lh lf lb : ℝ) : ℝ :=
  ((intent * (1 - success)) * lf + (intent * success) * lb) /
    evidenceOfIntent intent success lh lf lb

/-- The browser's scalar calculation is definitionally the three-world posterior. -/
theorem posterior_of_intent_agrees (intent success : ℝ)
    (hIntent0 : 0 ≤ intent) (hIntent1 : intent ≤ 1)
    (hSuccess0 : 0 ≤ success) (hSuccess1 : success ≤ 1)
    (e : Likelihood) :
    posteriorBackdoor (priorOfIntent intent success
      hIntent0 hIntent1 hSuccess0 hSuccess1) e =
    posteriorOfIntent intent success e.honest e.failed e.backdoor := by
  rfl

/-- Evidence update displayed in the UI (in probability units, not percentage points). -/
noncomputable def bayesDelta (p : Prior) (e : Likelihood) : ℝ :=
  posteriorBackdoor p e - priorBackdoor p

/-- The exact polynomial numerator used for break-even ticks. -/
def bayesDeltaNumerator (p : Prior) (e : Likelihood) : ℝ :=
  p.backdoor * (priorNotBackdoor p * e.backdoor - notBackdoorEvidenceMass p e)

/-- The UI's break-even numerator is the numerator of the exact update. -/
theorem bayes_delta_formula (p : Prior) (e : Likelihood)
    (hE : evidenceMass p e ≠ 0) :
    bayesDelta p e = bayesDeltaNumerator p e / evidenceMass p e := by
  have hMass : priorNotBackdoor p + p.backdoor = 1 :=
    complement_partition p
  have hAux : e.backdoor - evidenceMass p e =
      priorNotBackdoor p * e.backdoor - notBackdoorEvidenceMass p e := by
    calc
      e.backdoor - evidenceMass p e =
          (priorNotBackdoor p + p.backdoor) * e.backdoor -
            evidenceMass p e := by rw [hMass]; ring
      _ = priorNotBackdoor p * e.backdoor -
            notBackdoorEvidenceMass p e := by
          unfold priorNotBackdoor evidenceMass notBackdoorEvidenceMass
          ring
  calc
    bayesDelta p e =
        (p.backdoor * (e.backdoor - evidenceMass p e)) /
          evidenceMass p e := by
      unfold bayesDelta posteriorBackdoor priorBackdoor
      field_simp [hE]
    _ = bayesDeltaNumerator p e / evidenceMass p e := by
      rw [hAux]
      rfl

/-- The evidence update is negative precisely when its numerator is negative.
    Requires the evidence actually to be possible. -/
theorem bayes_delta_negative_iff (p : Prior) (e : Likelihood)
    (hE : 0 < evidenceMass p e) :
    bayesDelta p e < 0 ↔ bayesDeltaNumerator p e < 0 := by
  rw [bayes_delta_formula p e (ne_of_gt hE)]
  rw [div_lt_iff₀ hE]
  simp

/-- Positive posterior update, with the same conditioning requirement. -/
theorem bayes_delta_positive_iff (p : Prior) (e : Likelihood)
    (hE : 0 < evidenceMass p e) :
    0 < bayesDelta p e ↔ 0 < bayesDeltaNumerator p e := by
  rw [bayes_delta_formula p e (ne_of_gt hE)]
  rw [lt_div_iff₀ hE]
  simp

/-- A break-even is exact equality, not a numerically small change.
    Zero prior backdoor probability is a separate, degenerate route to equality. -/
theorem bayes_break_even_iff (p : Prior) (e : Likelihood)
    (hE : 0 < evidenceMass p e) :
    bayesDelta p e = 0 ↔
      p.backdoor = 0 ∨
      priorNotBackdoor p * e.backdoor = notBackdoorEvidenceMass p e := by
  rw [bayes_delta_formula p e (ne_of_gt hE)]
  simp [bayesDeltaNumerator, ne_of_gt hE, mul_eq_zero, sub_eq_zero]

/-- If both B and its complement have positive prior mass, break-even occurs
    precisely when the evidence likelihoods under B and not-B agree. -/
theorem bayes_break_even_likelihood_iff (p : Prior) (e : Likelihood)
    (hE : 0 < evidenceMass p e)
    (hB : 0 < p.backdoor)
    (hN : 0 < priorNotBackdoor p) :
    bayesDelta p e = 0 ↔
      e.backdoor = evidenceGivenNotBackdoor p e := by
  rw [bayes_break_even_iff p e hE]
  have hBne : p.backdoor ≠ 0 := ne_of_gt hB
  simp only [hBne, false_or]
  unfold evidenceGivenNotBackdoor
  constructor
  · intro h
    apply (eq_div_iff (ne_of_gt hN)).mpr
    simpa [mul_comm] using h
  · intro h
    have hh := (eq_div_iff (ne_of_gt hN)).mp h
    simpa [mul_comm] using hh

/-- A particularly direct scalar update formula for the five browser inputs. -/
noncomputable def scalarBayesDelta
    (intent success lh lf lb : ℝ) : ℝ :=
  posteriorOfIntent intent success lh lf lb - intent * success

/-- Exact scalar break-even numerator, used by both interactive interfaces. -/
def scalarBayesNumerator (intent success lh lf lb : ℝ) : ℝ :=
  (intent * success) *
    (((1 - intent) + intent * (1 - success)) * lb -
      ((1 - intent) * lh + (intent * (1 - success)) * lf))

/-- Agreement of the scalar break-even numerator with the finite model. -/
theorem scalar_numerator_agrees (intent success : ℝ)
    (hIntent0 : 0 ≤ intent) (hIntent1 : intent ≤ 1)
    (hSuccess0 : 0 ≤ success) (hSuccess1 : success ≤ 1)
    (e : Likelihood) :
    scalarBayesNumerator intent success e.honest e.failed e.backdoor =
      bayesDeltaNumerator (priorOfIntent intent success
        hIntent0 hIntent1 hSuccess0 hSuccess1) e := by
  rfl

/-- The scalar delta is the same update as the finite three-world model. -/
theorem scalar_delta_agrees (intent success : ℝ)
    (hIntent0 : 0 ≤ intent) (hIntent1 : intent ≤ 1)
    (hSuccess0 : 0 ≤ success) (hSuccess1 : success ≤ 1)
    (e : Likelihood) :
    scalarBayesDelta intent success e.honest e.failed e.backdoor =
      bayesDelta (priorOfIntent intent success
        hIntent0 hIntent1 hSuccess0 hSuccess1) e := by
  rfl

end SeedBayes
