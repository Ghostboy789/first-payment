# First Payment findings

**The grace-period contract fails the preset pilot rule.** Weekly profit clears the positive-gain
requirement among borrowers with recorded profit. The 95% upper bound on extra default is
11.09 percentage points, above the 2.00-point cap. The cap is a fixed pilot assumption.

## Reproduction

All three comparisons passed the fixed tolerance for coefficient, clustered standard error and
sample size. Block-adjusted estimates compare assignment to grace minus assignment to regular.

| Outcome | Paper effect / SE | Rebuilt effect / SE | Rebuilt 95% CI | n | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Loan unpaid in full at 52 weeks past due | 6.14 / 2.51 pp | 6.14 / 2.51 pp | 1.20 to 11.09 pp | 845 | PASS |
| Weekly household business profit | ₹906.6 / ₹373.8 | ₹906.6 / ₹373.8 | ₹168.7 to ₹1,644.4 | 752 | PASS |
| Loan spending on the business | ₹364.9 / ₹180.1 | ₹364.9 / ₹180.1 | ₹9.3 to ₹720.5 | 845 | PASS |

The investment fit adds loan-size indicators and the matching flag used by the deposited script.
The unrounded effect and SE gaps are in the [aggregate result file](../site/data/results.json).
Published references are Tables 1–3 of the original study. [Trial paper](https://doi.org/10.1257/aer.103.6.2196)

## Coverage and sensitivity

The paper’s methods report 93% completion of the Survey 2 loan-use module. The Table 1 note
says every client completed it. The replication file confirms 845 usable business-spending
values. Its Table 1 script adjusts for a flag marking 59 borrowers and computes the regular
reference mean from unflagged borrowers. The 786 unflagged records represent 93.0% of the
released cohort, matching the reported completion rate after rounding. These are file counts.
The deposit and appendix leave the flag’s meaning and interview provenance uncertain.
[Trial paper, Section II.A and Table 1](https://doi.org/10.1257/aer.103.6.2196) · [Supplemental appendix](https://www.aeaweb.org/articles/materials/2402) · [AEA deposit](https://doi.org/10.3886/E112672V1)

Excluding flagged records in a follow-up check gives an investment estimate of ₹343.7 more
per loan (95% CI −₹19.0 to ₹706.5, n=786). The interval crosses zero. This fit measures
sensitivity to the sample restriction. The pilot rule uses profit and default.

Profit was available for 379 of 425 regular borrowers and 373 of 420 grace borrowers. The
adjusted difference in recording was −0.61 percentage points (95% CI −4.87 to 3.65, n=845).
An income item was available for 387 regular and 382 grace borrowers. It is a follow-up proxy.
A similar recording rate is compatible with selective missingness in either arm.

| Profit scenario | Effect per week | 95% CI | n | Profit gate | Pilot |
| --- | ---: | ---: | ---: | --- | --- |
| Available cases, clipped to pooled p1 and p99 | ₹529.2 | ₹169.7 to ₹888.6 | 752 | PASS | FAIL |
| Available cases, dropped outside those cutoffs | ₹335.0 | −₹6.9 to ₹676.8 | 744 | FAIL | FAIL |
| Low endpoint under bounded missing profit | −₹1,012.8 | −₹1,481.3 to −₹544.2 | 845 | FAIL | FAIL |
| High endpoint under bounded missing profit | ₹2,012.2 | ₹1,523.1 to ₹2,501.3 | 845 | PASS | FAIL |

The p1 and p99 cutoffs are ₹0 and ₹13,766.6 per week, descriptive quantiles of observed profit.
Each missing-profit interval is conditional on the reported imputation and cutoffs. Under the
support assumption the endpoint estimates bound the completed-data coefficient for clipped
profit. The data leave the effect on uncapped profit for unobserved borrowers unresolved.

Within-batch permutations of whole loan groups gave two-sided p-values of 0.0267 for default,
0.0133 for deposited business spending and 0.8272 for profit recording (9,999 draws per outcome).
These are sharp-null p-values rather than effect sizes. The spending permutation uses the
block-only model. For the profit level, selection at follow-up prevents a straightforward
sharp-null permutation of the observed cases.

## Pricing

Using an assumed ₹8,000 exposure and 50% loss given default, added credit loss is ₹245.6 per
loan (95% CI ₹47.8 to ₹443.5). Recorded outstanding debt rose by ₹148.7 per loan
(95% CI −₹16.4 to ₹313.8, n=845). Outstanding balances can still be recovered.

At base exposure and loss severity, the break-even default increase is 0 points at ₹0 of new
lender contribution and 5.00 points at an illustrative ₹200 per loan. These are arithmetic
thresholds. They both fall below the trial's upper default bound. One week of the measured
borrower gain would be equivalent to 22.66 points of extra default loss (95% CI 4.22 to 41.11)
at the same assumed severity. The profit accrues to the borrower about three years later, and
the credit loss falls on the lender on the trial loan. The comparison illustrates scale.

## Interpretation

The trial compares entire contracts, including maturity and effective interest. It concerns
one lender in Kolkata and a cohort assigned in 2007. [Trial paper](https://doi.org/10.1257/aer.103.6.2196)

The analysis plan was the first commit. A separate calculation from the Stata file checked the
published aggregates using residualized least squares, an explicit cluster variance and
independent arithmetic for the blocked permutation statistic.
