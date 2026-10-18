import Mathlib

/-!
# A fixed, ex ante choice between two methods

This deliberately does NOT formalize cryptographic search, pseudorandomness,
or the behavior of an adaptive adversary. We state method-specific conditional
success rates as real parameters and prove the directional conclusions that
follow when method choice is fixed before the attack outcome is observed.
-/

namespace SeedBayes

/-- Success probability before learning the method, if method T is chosen with
    probability alpha and U with probability 1-alpha. -/
def mixedSuccess (alpha restricted unrestricted : ℝ) : ℝ :=
  alpha * restricted + (1 - alpha) * unrestricted

/-- Exact change after learning that the selected method was T. -/
theorem restricted_delta (alpha restricted unrestricted : ℝ) :
    restricted - mixedSuccess alpha restricted unrestricted =
      (1 - alpha) * (restricted - unrestricted) := by
  unfold mixedSuccess
  ring

/-- If T is no more effective than U, learning T cannot increase the
    success probability. The crucial effectiveness ordering is a hypothesis. -/
theorem restricted_nonincreasing
    (alpha restricted unrestricted : ℝ)
    (hAlpha : alpha ≤ 1) (h : restricted ≤ unrestricted) :
    restricted ≤ mixedSuccess alpha restricted unrestricted := by
  have ha : 0 ≤ 1 - alpha := sub_nonneg.mpr hAlpha
  have hd : 0 ≤ unrestricted - restricted := sub_nonneg.mpr h
  have hp := mul_nonneg ha hd
  unfold mixedSuccess
  nlinarith

/-- The update is strictly negative if U is strictly better and T was not
    already certain before observing the method. -/
theorem restricted_strict
    (alpha restricted unrestricted : ℝ)
    (hAlpha : alpha < 1) (h : restricted < unrestricted) :
    restricted < mixedSuccess alpha restricted unrestricted := by
  have ha : 0 < 1 - alpha := sub_pos.mpr hAlpha
  have hd : 0 < unrestricted - restricted := sub_pos.mpr h
  have hp := mul_pos ha hd
  unfold mixedSuccess
  nlinarith

/-- Toy publication policy: all successful attempts publish; failed attempts
    publish with probability rho. P(success | published) is this quotient. -/
noncomputable def publishedSuccess (success rho : ℝ) : ℝ :=
  success / (success + (1 - success) * rho)

/-- Conditioning publication on success makes the posterior success
    probability 1 whenever publication is possible. -/
theorem publish_only_success (s : ℝ) (hs : 0 < s) :
    publishedSuccess s 0 = 1 := by
  simp [publishedSuccess, ne_of_gt hs]

/-- At rho = 1, observing publication provides no information. -/
theorem always_publish (s : ℝ) : publishedSuccess s 1 = s := by
  unfold publishedSuccess
  have h : s + (1 - s) * 1 = (1 : ℝ) := by ring
  rw [h]
  simp

end SeedBayes
