import Mathlib

/-!
# Effective restriction as an alternative explanation of evidence E

This module proves only the probability arithmetic. It does not infer any
historical probability, nor connect the observed E to an actually restrictive
procedure. In particular the equations assume P(I|E)=P(I),
P(B|I,T,E)=P(B|I,T), and P(B|I,not T,E)=P(B|I,not T).
Publication selection is outside this model.

Parameters: p=P(I), s=P(B|I,not T), t0=P(T|I), t1=P(T|I,E),
r=P(B|I,T)/s when s>0. Values are probabilities with r in [0,1].
-/

namespace SeedBayes

/-- Multiplicative success factor at a given conditional belief in restriction. -/
def restrictionFactor (t r : ℝ) : ℝ := 1 - t * (1 - r)

/-- Marginal backdoor probability before learning E. -/
def restrictionBefore (p s t0 r : ℝ) : ℝ :=
  p * s * restrictionFactor t0 r

/-- Marginal backdoor probability after learning E. -/
def restrictionAfter (p s t1 r : ℝ) : ℝ :=
  p * s * restrictionFactor t1 r

/-- Signed evidence update; NOT combined with the three-world likelihood update. -/
def restrictionDelta (p s t0 t1 r : ℝ) : ℝ :=
  restrictionAfter p s t1 r - restrictionBefore p s t0 r

/-- The polynomial implemented directly in Python and JavaScript. -/
def restrictionDeltaPolynomial (p s t0 t1 r : ℝ) : ℝ :=
  -(p * s) * (t1 - t0) * (1 - r)

/-- Exact update: a change in the belief that an attacker was restricted. -/
theorem restriction_delta_formula (p s t0 t1 r : ℝ) :
    restrictionDelta p s t0 t1 r = restrictionDeltaPolynomial p s t0 t1 r := by
  unfold restrictionDelta restrictionDeltaPolynomial restrictionAfter restrictionBefore restrictionFactor
  ring

/-- If the evidence increases belief in genuine restriction and that restriction
    does not improve attack success, the update cannot be positive. -/
theorem restriction_nonincrease (p s t0 t1 r : ℝ)
    (hp : 0 ≤ p) (hs : 0 ≤ s) (ht : t0 ≤ t1) (hr : r ≤ 1) :
    restrictionDelta p s t0 t1 r ≤ 0 := by
  rw [restriction_delta_formula]
  unfold restrictionDeltaPolynomial
  have h : 0 ≤ p * s * (t1 - t0) * (1 - r) :=
    mul_nonneg (mul_nonneg (mul_nonneg hp hs) (sub_nonneg.mpr ht))
      (sub_nonneg.mpr hr)
  nlinarith

/-- Strict decrease when all four factors really contribute. -/
theorem restriction_strict_decrease (p s t0 t1 r : ℝ)
    (hp : 0 < p) (hs : 0 < s) (ht : t0 < t1) (hr : r < 1) :
    restrictionDelta p s t0 t1 r < 0 := by
  rw [restriction_delta_formula]
  unfold restrictionDeltaPolynomial
  have h : 0 < p * s * (t1 - t0) * (1 - r) :=
    mul_pos (mul_pos (mul_pos hp hs) (sub_pos.mpr ht))
      (sub_pos.mpr hr)
  nlinarith

/-- Exact break-even characterization: no intent, no baseline chance, no change
    in belief, or a restriction that makes no difference. -/
theorem restriction_break_even_iff (p s t0 t1 r : ℝ) :
    restrictionDelta p s t0 t1 r = 0 ↔
      p = 0 ∨ s = 0 ∨ t1 = t0 ∨ r = 1 := by
  have hRewrite : restrictionDelta p s t0 t1 r =
      -(p * s * (t1 - t0) * (1 - r)) := by
    rw [restriction_delta_formula]
    unfold restrictionDeltaPolynomial
    ring
  rw [hRewrite]
  simp only [neg_eq_zero]
  constructor
  · intro h
    rcases (mul_eq_zero.mp h) with hleft | hright
    · rcases (mul_eq_zero.mp hleft) with hleft | htime
      · rcases (mul_eq_zero.mp hleft) with hp | hs
        · exact Or.inl hp
        · exact Or.inr (Or.inl hs)
      · exact Or.inr (Or.inr (Or.inl (sub_eq_zero.mp htime)))
    · have hr : 1 = r := sub_eq_zero.mp hright
      exact Or.inr (Or.inr (Or.inr hr.symm))
  · intro h
    rcases h with hp | hs | htime | hr
    · simp [hp]
    · simp [hs]
    · simp [htime]
    · simp [hr]

/-- Equal prior and posterior restriction beliefs always give a neutral update. -/
theorem restriction_unchanged (p s t r : ℝ) :
    restrictionDelta p s t t r = 0 := by
  simp [restrictionDelta, restrictionAfter, restrictionBefore]

end SeedBayes
