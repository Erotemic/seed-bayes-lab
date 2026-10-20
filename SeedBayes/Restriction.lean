import Mathlib

/-!
# Bayes-derived belief in an effective restriction

Finite, purely algebraic probability model. No cryptographic assumptions are
proved here. With `I` intent, `T` an effective restriction, `B` planted
backdoor, and `E` observed provenance, parameters are
`p=P(I)`, `t=P(T|I)`, `eT=P(E|I,T)`, `eU=P(E|I,not T)`,
`sU=P(B|I,not T)`, `sT=P(B|I,T)`.

The model explicitly assumes: (a) E does not alter attack success conditional
on intent and T, and (b) the evidence likelihood under no intent equals
`t*eT+(1-t)*eU`, which makes `P(I|E)=P(I)` for nonzero evidence mass.
It is an ALTERNATIVE explanation of E, not an additional update to combine
with the existing three-world likelihood model.
-/

namespace SeedBayes

/-- P(E|I), and (by assumption) P(E|not I). -/
def restrictionEvidenceMass (t eT eU : ℝ) : ℝ := t * eT + (1 - t) * eU

/-- P(T|I,E) obtained by Bayes' theorem; requires positive evidence mass. -/
noncomputable def restrictionPosteriorBelief (t eT eU : ℝ) : ℝ :=
  t * eT / restrictionEvidenceMass t eT eU

/-- P(B) in the effective-restriction interpretation. -/
def restrictionBefore (p t sU sT : ℝ) : ℝ :=
  p * ((1 - t) * sU + t * sT)

/-- P(B|E), with P(I|E)=p and success rates unchanged given I,T. -/
noncomputable def restrictionAfter (p t eT eU sU sT : ℝ) : ℝ :=
  p * ((1 - restrictionPosteriorBelief t eT eU) * sU +
    restrictionPosteriorBelief t eT eU * sT)

/-- Signed posterior-minus-prior update. -/
noncomputable def restrictionDelta (p t eT eU sU sT : ℝ) : ℝ :=
  restrictionAfter p t eT eU sU sT - restrictionBefore p t sU sT

/-- Exact numerator used for direction and break-even sliders. -/
def restrictionDeltaNumerator (p t eT eU sU sT : ℝ) : ℝ :=
  p * t * (1 - t) * (eT - eU) * (sT - sU)

/-- The posterior belief in T differs from the prior by this exact amount. -/
theorem restriction_belief_shift (t eT eU : ℝ)
    (hD : restrictionEvidenceMass t eT eU ≠ 0) :
    restrictionPosteriorBelief t eT eU - t =
      t * (1 - t) * (eT - eU) / restrictionEvidenceMass t eT eU := by
  unfold restrictionPosteriorBelief
  field_simp [hD]
  simp only [restrictionEvidenceMass]
  ring

/-- The unconditional intent probability remains p if the likelihood
    of E under not-I is set equal to the marginal likelihood under I. -/
theorem restriction_intent_invariant (p t eT eU : ℝ)
    (hD : restrictionEvidenceMass t eT eU ≠ 0) :
    p * restrictionEvidenceMass t eT eU /
      ((1 - p) * restrictionEvidenceMass t eT eU +
       p * restrictionEvidenceMass t eT eU) = p := by
  have hsum : (1 - p) * restrictionEvidenceMass t eT eU +
      p * restrictionEvidenceMass t eT eU = restrictionEvidenceMass t eT eU := by ring
  rw [hsum]
  field_simp [hD]

/-- The update depends only on the belief change and the success-rate gap. -/
theorem restriction_delta_shift (p t eT eU sU sT : ℝ) :
    restrictionDelta p t eT eU sU sT =
      p * (restrictionPosteriorBelief t eT eU - t) * (sT - sU) := by
  unfold restrictionDelta restrictionAfter restrictionBefore
  ring

/-- Exact rational delta: all six inputs are probabilities, and no free
    posterior belief or success ratio is supplied. -/
theorem restriction_delta_formula (p t eT eU sU sT : ℝ)
    (hD : restrictionEvidenceMass t eT eU ≠ 0) :
    restrictionDelta p t eT eU sU sT =
      restrictionDeltaNumerator p t eT eU sU sT /
        restrictionEvidenceMass t eT eU := by
  rw [restriction_delta_shift, restriction_belief_shift t eT eU hD]
  unfold restrictionDeltaNumerator
  ring

/-- Equal evidence likelihoods imply no change, when conditioning is defined. -/
theorem restriction_neutral_evidence (p t e sU sT : ℝ)
    (hD : restrictionEvidenceMass t e e ≠ 0) :
    restrictionDelta p t e e sU sT = 0 := by
  rw [restriction_delta_formula p t e e sU sT hD]
  simp [restrictionDeltaNumerator]

/-- The restriction cannot increase the chance of backdooring if evidence
    favors T and T makes a successful attack no easier. -/
theorem restriction_nonincrease (p t eT eU sU sT : ℝ)
    (hp : 0 ≤ p) (ht0 : 0 ≤ t) (ht1 : t ≤ 1)
    (he : eU ≤ eT) (hs : sT ≤ sU)
    (hD : 0 < restrictionEvidenceMass t eT eU) :
    restrictionDelta p t eT eU sU sT ≤ 0 := by
  rw [restriction_delta_formula p t eT eU sU sT (ne_of_gt hD)]
  unfold restrictionDeltaNumerator
  have hpos : 0 ≤ p * t * (1 - t) * (eT - eU) := by
    exact mul_nonneg (mul_nonneg (mul_nonneg hp ht0) (sub_nonneg.mpr ht1))
      (sub_nonneg.mpr he)
  have hneg : sT - sU ≤ 0 := sub_nonpos.mpr hs
  exact div_nonpos_of_nonpos_of_nonneg
    (mul_nonpos_of_nonneg_of_nonpos hpos hneg) (le_of_lt hD)

/-- Strict decrease for nondegenerate intent, prior, evidence advantage and
    attack disadvantage under restriction. -/
theorem restriction_strict_decrease (p t eT eU sU sT : ℝ)
    (hp : 0 < p) (ht0 : 0 < t) (ht1 : t < 1)
    (he : eU < eT) (hs : sT < sU)
    (hD : 0 < restrictionEvidenceMass t eT eU) :
    restrictionDelta p t eT eU sU sT < 0 := by
  rw [restriction_delta_formula p t eT eU sU sT (ne_of_gt hD)]
  unfold restrictionDeltaNumerator
  have hpos : 0 < p * t * (1 - t) * (eT - eU) := by
    exact mul_pos (mul_pos (mul_pos hp ht0) (sub_pos.mpr ht1)) (sub_pos.mpr he)
  have hneg : sT - sU < 0 := sub_neg.mpr hs
  exact div_neg_of_neg_of_pos (mul_neg_of_pos_of_neg hpos hneg) hD

/-- If E favors restriction but the restricted method instead makes attack
    success more likely, the observed evidence strictly raises backdoor risk. -/
theorem restriction_strict_increase (p t eT eU sU sT : ℝ)
    (hp : 0 < p) (ht0 : 0 < t) (ht1 : t < 1)
    (he : eU < eT) (hs : sU < sT)
    (hD : 0 < restrictionEvidenceMass t eT eU) :
    0 < restrictionDelta p t eT eU sU sT := by
  rw [restriction_delta_formula p t eT eU sU sT (ne_of_gt hD)]
  unfold restrictionDeltaNumerator
  have hpos : 0 < p * t * (1 - t) * (eT - eU) := by
    exact mul_pos (mul_pos (mul_pos hp ht0) (sub_pos.mpr ht1)) (sub_pos.mpr he)
  exact div_pos (mul_pos hpos (sub_pos.mpr hs)) hD

/-- A break-even requires a zero factor in the exact numerator. -/
theorem restriction_break_even_iff (p t eT eU sU sT : ℝ)
    (hD : restrictionEvidenceMass t eT eU ≠ 0) :
    restrictionDelta p t eT eU sU sT = 0 ↔
      p = 0 ∨ t = 0 ∨ t = 1 ∨ eT = eU ∨ sT = sU := by
  rw [restriction_delta_formula p t eT eU sU sT hD]
  have hn : (restrictionDeltaNumerator p t eT eU sU sT /
      restrictionEvidenceMass t eT eU = 0) ↔
      restrictionDeltaNumerator p t eT eU sU sT = 0 := by
    constructor
    · intro h
      have hm := congrArg (fun x : ℝ => x * restrictionEvidenceMass t eT eU) h
      simpa [hD] using hm
    · intro h
      simp [h]
  rw [hn]
  unfold restrictionDeltaNumerator
  have hOne : ((0 : ℝ) = 1 - t) ↔ t = 1 := by
    constructor
    · intro h
      linarith
    · intro h
      linarith
  simp [mul_eq_zero, sub_eq_zero, eq_comm, or_assoc, hOne]

end SeedBayes
