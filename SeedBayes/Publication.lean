import SeedBayes.Selection

/-!
# Publication-conditioned selection between two methods

The method is selected *before* the attempt. Conditional success is `st` or
`su`; success always publishes, failure publishes independently with chance
`rho`. These are assumptions of this finite toy model, not historical claims.
-/

namespace SeedBayes

/-- P(J | method) for a success probability s and failed-publication rate rho. -/
def publicationMass (s rho : ℝ) : ℝ := s + (1 - s) * rho

/-- P(J) after mixing the two methods before their outcomes are known. -/
def mixturePublicationMass (alpha st su rho : ℝ) : ℝ :=
  alpha * publicationMass st rho + (1 - alpha) * publicationMass su rho

/-- P(B | J), before the publication reveals which method was used. -/
noncomputable def mixturePublishedBackdoor (alpha st su rho : ℝ) : ℝ :=
  mixedSuccess alpha st su / mixturePublicationMass alpha st su rho

/-- P(B | J,T) after learning the published curve used the restricted method.
    Defined as a quotient; interpreting it as a conditional probability also
    requires P(T)>0 and P(J|T)>0. -/
noncomputable def restrictedPublishedBackdoor (st rho : ℝ) : ℝ :=
  st / publicationMass st rho

/-- Joint-event conditioning agrees with the simplified after-probability. -/
theorem joint_restricted_publication (alpha st rho : ℝ)
    (hAlpha : alpha ≠ 0) (hPt : publicationMass st rho ≠ 0) :
    (alpha * st) / (alpha * publicationMass st rho) =
      restrictedPublishedBackdoor st rho := by
  unfold restrictedPublishedBackdoor
  field_simp [hAlpha, hPt] <;> ring

/-- Exact difference used by Python `MethodUpdate.delta` and the offline JS.
    Notice that `alpha` does NOT disappear from the mixed denominator. -/
theorem publication_delta_formula (alpha st su rho : ℝ)
    (hPt : publicationMass st rho ≠ 0)
    (hJ : mixturePublicationMass alpha st su rho ≠ 0) :
    restrictedPublishedBackdoor st rho -
      mixturePublishedBackdoor alpha st su rho =
    rho * (1 - alpha) * (st - su) /
      (publicationMass st rho * mixturePublicationMass alpha st su rho) := by
  unfold restrictedPublishedBackdoor mixturePublishedBackdoor
  field_simp [hPt, hJ]
  unfold mixturePublicationMass publicationMass mixedSuccess
  ring

/-- The numerator used for publication-model break-even ticks. -/
def publicationDeltaNumerator (alpha st su rho : ℝ) : ℝ :=
  rho * (1 - alpha) * (st - su)

/-- On possible conditioning events, break-even has exactly three algebraic
    causes: never publish failures, always use T, or equal success rates. -/
theorem publication_break_even_iff (alpha st su rho : ℝ)
    (hPt : publicationMass st rho ≠ 0)
    (hJ : mixturePublicationMass alpha st su rho ≠ 0) :
    restrictedPublishedBackdoor st rho =
      mixturePublishedBackdoor alpha st su rho ↔
    rho = 0 ∨ alpha = 1 ∨ st = su := by
  have hDen : publicationMass st rho *
      mixturePublicationMass alpha st su rho ≠ 0 := mul_ne_zero hPt hJ
  have hDelta := publication_delta_formula alpha st su rho hPt hJ
  constructor
  · intro h
    have hz : restrictedPublishedBackdoor st rho -
        mixturePublishedBackdoor alpha st su rho = 0 := sub_eq_zero.mpr h
    rw [hDelta] at hz
    have hz' : rho * (1 - alpha) * (st - su) = 0 := by
      have hm := congrArg (fun x : ℝ =>
        x * (publicationMass st rho * mixturePublicationMass alpha st su rho)) hz
      simpa [hDen] using hm
    rcases (mul_eq_zero.mp hz') with ha | hb
    · rcases (mul_eq_zero.mp ha) with hRho | hAlpha
      · exact Or.inl hRho
      · exact Or.inr (Or.inl (by linarith))
    · exact Or.inr (Or.inr (by linarith))
  · intro h
    apply sub_eq_zero.mp
    rw [hDelta]
    rcases h with hr | ha | hs
    · simp [hr]
    · simp [ha]
    · simp [hs]

/-- Under the model's nonnegative failed-publication rate, restricted methods
    with no larger success chance cannot produce a positive update. -/
theorem publication_restricted_nonincreasing (alpha st su rho : ℝ)
    (hAlpha : alpha ≤ 1) (hRho : 0 ≤ rho)
    (hSuccess : st ≤ su)
    (hPt : 0 < publicationMass st rho)
    (hJ : 0 < mixturePublicationMass alpha st su rho) :
    restrictedPublishedBackdoor st rho ≤
      mixturePublishedBackdoor alpha st su rho := by
  have hDelta := publication_delta_formula alpha st su rho
    (ne_of_gt hPt) (ne_of_gt hJ)
  have hNum : publicationDeltaNumerator alpha st su rho ≤ 0 := by
    unfold publicationDeltaNumerator
    have hLeft : 0 ≤ rho * (1 - alpha) :=
      mul_nonneg hRho (sub_nonneg.mpr hAlpha)
    exact mul_nonpos_of_nonneg_of_nonpos hLeft (sub_nonpos.mpr hSuccess)
  have hDen : 0 < publicationMass st rho *
      mixturePublicationMass alpha st su rho := mul_pos hPt hJ
  have hFrac :
      rho * (1 - alpha) * (st - su) /
        (publicationMass st rho * mixturePublicationMass alpha st su rho) ≤ 0 :=
    (div_le_iff₀ hDen).mpr (by simpa [publicationDeltaNumerator] using hNum)
  linarith

/-- Successful attempts publishing while failed attempts never do forces
    P(B|J,T)=1, provided publication is possible under T. -/
theorem restricted_publish_only_success (st : ℝ) (hs : 0 < st) :
    restrictedPublishedBackdoor st 0 = 1 := by
  simp [restrictedPublishedBackdoor, publicationMass, ne_of_gt hs]

end SeedBayes
