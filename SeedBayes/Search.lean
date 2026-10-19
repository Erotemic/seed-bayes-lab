import Mathlib

/-!
# Independent candidate search, conditional on an explicitly assumed q

This is the idealized random-search model only. It does not assert that
vulnerable elliptic curves are distributed independently or that the designer
could evaluate a certain number of candidates in 1997.

N is a natural number of actual independent trials. The interactive app also
allows fractional *bits* of effective effort; those are a numerical
interpolation, not a claim about a fractional number of independent trials.
-/

namespace SeedBayes

/-- Probability of at least one hit among `n` independent Bernoulli(q) draws. -/
def independentSuccess (q : ℝ) (n : ℕ) : ℝ := 1 - (1 - q) ^ n

/-- No candidate gives no success. -/
theorem independent_success_zero (q : ℝ) : independentSuccess q 0 = 0 := by
  simp [independentSuccess]

/-- One additional independent draw succeeds if earlier draws already
    succeeded, or if they failed and the new draw succeeds. -/
theorem independent_success_succ (q : ℝ) (n : ℕ) :
    independentSuccess q (n + 1) =
      independentSuccess q n + (1 - independentSuccess q n) * q := by
  simp only [independentSuccess, pow_succ]
  ring

/-- With valid per-candidate probability q, more independent trials cannot
    decrease the chance of at least one success. -/
theorem independent_success_mono (q : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (m n : ℕ) (hmn : m ≤ n) :
    independentSuccess q m ≤ independentSuccess q n := by
  induction n, hmn using Nat.le_induction with
  | base => exact le_refl _
  | succ n _ ih =>
      have hb : 0 ≤ 1 - q := sub_nonneg.mpr hq1
      have hrest : 0 ≤ 1 - independentSuccess q n := by
        have hp : 0 ≤ (1 - q) ^ n := pow_nonneg hb n
        unfold independentSuccess
        linarith
      have hstep : 0 ≤ (1 - independentSuccess q n) * q :=
        mul_nonneg hrest hq0
      calc
        independentSuccess q m ≤ independentSuccess q n := ih
        _ ≤ independentSuccess q (n + 1) := by
          rw [independent_success_succ]
          linarith

/-- Effective trial count is limited by both the available candidate set
    and the amount of computation affordable to the attacker. -/
def effectiveSuccess (q : ℝ) (freedom budget : ℕ) : ℝ :=
  independentSuccess q (min freedom budget)

/-- Increasing candidate freedom cannot lower success probability if the
    computational budget and the attack distribution remain fixed. -/
theorem effective_success_mono_freedom (q : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (f₁ f₂ budget : ℕ) (hf : f₁ ≤ f₂) :
    effectiveSuccess q f₁ budget ≤ effectiveSuccess q f₂ budget := by
  unfold effectiveSuccess
  apply independent_success_mono q hq0 hq1
  omega

/-- Increasing computational budget cannot lower success probability under
    the same fixed candidate family and per-candidate distribution. -/
theorem effective_success_mono_budget (q : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (freedom b₁ b₂ : ℕ) (hb : b₁ ≤ b₂) :
    effectiveSuccess q freedom b₁ ≤ effectiveSuccess q freedom b₂ := by
  unfold effectiveSuccess
  apply independent_success_mono q hq0 hq1
  omega

/-- Independent search multiplied by the probability of knowing an exploitable
    property in the first place. Assumes independence of those stages. -/
def plantedSuccess (know q : ℝ) (freedom budget : ℕ) : ℝ :=
  know * effectiveSuccess q freedom budget

/-- Search monotonicity persists under nonnegative probability of knowledge. -/
theorem planted_success_mono_freedom (know q : ℝ)
    (hKnow : 0 ≤ know) (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (f₁ f₂ budget : ℕ) (hf : f₁ ≤ f₂) :
    plantedSuccess know q f₁ budget ≤ plantedSuccess know q f₂ budget := by
  unfold plantedSuccess
  exact mul_le_mul_of_nonneg_left
    (effective_success_mono_freedom q hq0 hq1 f₁ f₂ budget hf) hKnow

end SeedBayes
