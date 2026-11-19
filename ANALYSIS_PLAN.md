# First Payment analysis plan

Fixed on 19 November 2026 after checking archive structure and outcome availability and before fitting any models or computing treatment effects. Published estimates were already known. This plan fixes the design of a retrospective analysis.

## Trial and outcomes

The unit in the file is one randomized borrower household (`slid`). Assignment is at the loan-group level (`sec_group_name`), within the nine batches in `Stratification_Dummies`. `sec_treat = 1` is assignment to the grace-period contract. Analyze by assignment. The trial compares two contracts, with differences in payment timing, maturity and effective interest, at one Kolkata lender in 2007. Later business profit and earlier repayment describe different horizons.

| Outcome | Definition | Paper comparison |
| --- | --- | --- |
| Default | `not_finished_aug19`, 1 if the loan was unpaid in full at 52 weeks after its scheduled final instalment. Report differences in percentage points (pp). | Table 3 panel A column 3, 6.14 pp, SE 2.51 pp, n=845 |
| Profit | `Profit`, reported weekly household business profit in rupees from Survey 3, roughly three years after disbursement, referring to currently or most recently operating businesses. Use uncapped available values including zero. | Table 2 panel A column 1, ₹906.6/week, SE ₹373.8/week, n=752 |
| Investment | `Business_Expenditures`, rupees from the trial loan spent on inventory and raw materials, equipment and operating costs, from the deposited loan-use measure. | Table 1 panel A row 1 column 2, ₹364.9/loan, SE ₹180.1/loan, n=845 |

The three comparisons use the paper's minimally adjusted columns. Fit borrower OLS with an intercept and block indicators. The Table 3 script uses `Stratification`, which uniquely abbreviates the released block field. The Table 2 deduplication is a no-op for the unique household key. For Table 1, also include the deposited `Match3rd_in3rd` flag and loan-size category indicators, omitting the largest amount. Include every record in the fit. The flag restricts the Table 1 regular-arm reference mean only. The paper's text and table note describe different Survey 2 coverage. Report both and use the nonmissing deposited outcome, without treating file availability as survey response.

All intervals for coefficients are two-sided 95% t intervals on the treatment coefficient, using loan-group clustered CR1 standard errors with the factor G/(G−1) × (N−1)/(N−K) and G−1 degrees of freedom. G is the number of observed groups and K is the design rank including the intercept. Compare estimate and SE separately with the published values. Reproduced requires the published n and absolute discrepancies no larger than half the last printed unit for each value (0.005 pp for default, ₹0.05 for profit and investment). Use the unrounded fit and show any failed comparison and its gaps. A published reference interval, if displayed, is approximate and uses its printed coefficient and SE with the matching group t critical value.

## Pilot decision

Use default and profit from the block-only specifications above. The default analysis includes all randomized households. The profit estimate contrasts assigned arms among borrowers with recorded profit, so a full-cohort causal interpretation needs assumptions about selection.

- Profit clears the rule when its 95% lower endpoint is strictly greater than ₹0 per week. A pilot must offer credible positive borrower benefit before taking on more credit risk.
- Default clears the rule when its 95% upper endpoint is at most 2.00 pp above regular. This illustrative risk budget permits at most two additional loans unpaid per 100 at the trial horizon. No actual lender policy is assumed.
- PASS requires both checks. Use unrounded endpoints. The site starts at these thresholds and lets readers change them as scenarios. A failed gate is reported as a failure to clear the preset evidence rule.

## Expected loss and break-even

Use the default effect as incremental PD at the trial horizon and calculate the credit-loss-only surcharge per loan as ΔPD × EAD × LGD, with the same EAD and LGD in both arms. Use the study's modal ₹8,000 original principal as an illustrative exposure proxy and LGD scenarios of 25%, 50% (base), 75% and 100%. Multiply the default interval endpoints by the same scale. Also fit the effect on `Outstanding_Loan_Amount_Default` with the block-only model, as a comparison measured at the horizon. Outstanding debt is not ultimate net loss.

Compare this one-time lender loss with one week of the estimated borrower profit difference at Survey 3. Treat that comparison as a scale illustration across horizons. Do not extrapolate profit or assume the lender can collect it. Calculate the break-even default increase as incremental lender contribution before incremental credit loss divided by EAD × LGD. Use ₹0 additional contribution for the unchanged nominal charges illustration and ₹200 as a separate hypothetical net contribution scenario at base LGD. Show the borrower-side equivalent if one week of the measured profit were used as the budget, with endpoints scaled in parallel and any threshold over 100% flagged as outside a feasible probability change. The fixed scenario inputs have no sampling interval. The calculation omits funding, payment timing, operating costs and price responses, so it is not an APR or a financial viability estimate.

## Sensitivity and trial checks

- Report randomized group and borrower counts and the observed versus missing outcomes by arm, with a separate Survey 3 income-item availability count. These are cohort counts. Fit a block-only effect on whether profit was recorded, with a 95% interval. Report available-case arm means and adjusted differences with intervals and n for baseline age, marital status, schooling, household size and business ownership. Use the documented missing flags to restore unavailable baseline values to missing.
- Tail checks on available-case profit use pooled p1 and p99 computed by linear interpolation. Winsorize to both cutoffs or drop observations strictly outside them, keeping boundary ties. Refit the block-only model and rerun the pilot gate for each.
- Missing-profit stress: for the bounded outcome obtained by clipping profit to the same p1 and p99, assume unobserved bounded profit can be anywhere between those cutoffs. For the low endpoint, fill missing grace observations at p1 and regular at p99. Reverse for the high endpoint. Refit on the full cohort, report both endpoints and separate scenario-specific t intervals conditional on the cutoffs and imputations, and rerun the pilot rule for each scenario. These are bounds on the completed-data coefficient for the specified bounded outcome. The two fitted intervals are not a confidence interval for an identified set or for the original uncapped profit effect. No assumptions about monotone response.
- Randomization inference for 52-week default, deposited business investment and profit observation status. Sort blocks and groups, permute the observed assignments of whole groups within each block, preserving its treatment count, and share 9,999 draws from NumPy PCG64 seeded with 112672. Use the absolute block-only treatment coefficient, count ties as at least as extreme (tolerance 1e−12 in outcome units), and report (1 + exceedances)/(1 + draws). The investment permutation uses the released full-cohort measure and block-only model, separate from Table 1. No sharp-null test for the profit level, because the profit response pattern could itself depend on assignment.
- Halt on nonunique household records, nonbinary assignment or default, invalid group nesting, a block lacking both arms, or missing default, investment or design fields. Treat missing profit as recorded, and mark analyses unavailable if they lack identifying variation. Do not substitute a different outcome or relax a failed comparison. Record deviations before executing the changed specification.
- Independently verify all published aggregates, inferences and scenario calculations from the Stata source. Sort inputs before modeling and resampling and verify identical generated bytes across repeated runs.

## Sources

Field, Pande, Papp and Rigol (2013), *American Economic Review* 103(6), 2196–2226. [Paper](https://doi.org/10.1257/aer.103.6.2196) · [AEA data and code, project 112672 V1](https://doi.org/10.3886/E112672V1)

## Follow-up on loan-use coverage

Added on 19 November 2026 after the primary results and before running the subset model below.
Section II.A reports 93% Survey 2 loan-use coverage. Table 1 fits 845 records. The released
flag `Match3rd_in3rd` equals zero for 786 of 845 borrowers (93.0%). This is a numerical match.
The deposit does not establish which records came from original Survey 2 interviews.

Run one exploratory sensitivity on the Table 1 investment outcome. Exclude records where
`Match3rd_in3rd = 1`. Refit the original borrower-level regression with batch and loan-size
fixed effects, omitting the now-constant flag. Use the same loan-group clustered CR1 95% t
interval. Report n, effect and interval, and report whether the interval still lies entirely
above zero. This is a comparison of fitted results under a sample restriction. The provenance
and selection of the restricted sample are unverified. The full-record fit remains the paper
comparison. This check has no role in the profit and default pilot rule.
