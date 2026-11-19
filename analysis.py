"""Reproduce three paper rows and apply the fixed pilot rule."""

import json

import duckdb
import numpy as np
import statsmodels.formula.api as smf
from scipy.stats import t

from config import SITE_DIR

DEFAULT_CAP = 2.0
PROFIT_FLOOR = 0.0
EXPOSURE = 8_000
BASE_LGD = 0.50
RI_DRAWS = 9_999
RI_SEED = 112672

PAPER = {
    "default_52w": (6.14, 2.51, 845, 0.005),
    "profit": (906.6, 373.8, 752, 0.05),
    "investment": (364.9, 180.1, 845, 0.05),
}
BALANCE = {"age": 1, "married": 100, "education": 1, "household_size": 1, "baseline_business": 100}


def t_interval(effect, se, groups):
    margin = t.ppf(0.975, groups - 1) * se
    return [float(effect - margin), float(effect + margin)]


def fit(data, outcome, *, scale=1, controls=""):
    observed = data.dropna(subset=[outcome])
    model = smf.ols(f"{outcome} ~ assigned_grace + C(block_id){controls}", observed)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        raise ValueError(f"Singular design for {outcome}")
    groups = observed.group_id.nunique()
    result = model.fit(
        cov_type="cluster",
        cov_kwds={"groups": observed.group_id},
        use_t=True,
    )
    effect = float(result.params["assigned_grace"] * scale)
    se = float(result.bse["assigned_grace"] * scale)
    return {
        "effect": effect,
        "se": se,
        "ci": t_interval(effect, se, groups),
        "n": len(observed),
        "groups": groups,
    }


def compare(estimate, published):
    effect, se, n, tolerance = published
    effect_gap = estimate["effect"] - effect
    se_gap = estimate["se"] - se
    return {
        "paper_effect": effect,
        "paper_se": se,
        "paper_n": n,
        "paper_ci": t_interval(effect, se, estimate["groups"]),
        "effect_gap": effect_gap,
        "se_gap": se_gap,
        "pass": abs(effect_gap) <= tolerance and abs(se_gap) <= tolerance and estimate["n"] == n,
    }


def pilot(default_upper, profit_lower, *, cap=DEFAULT_CAP, floor=PROFIT_FLOOR):
    default_pass = default_upper <= cap
    profit_pass = profit_lower > floor
    return {
        "default_pass": default_pass,
        "profit_pass": profit_pass,
        "pass": default_pass and profit_pass,
    }


def pricing(default, profit):
    cases = []
    for lgd in (0.25, BASE_LGD, 0.75, 1.00):
        loss_per_default = EXPOSURE * lgd
        cases.append(
            {
                "lgd": lgd,
                "loss": default["effect"] * loss_per_default / 100,
                "ci": [value * loss_per_default / 100 for value in default["ci"]],
            }
        )
    base = EXPOSURE * BASE_LGD
    borrower_pd = 100 * profit["effect"] / base
    borrower_interval = [100 * value / base for value in profit["ci"]]
    return {
        "exposure": EXPOSURE,
        "base_lgd": BASE_LGD,
        "scenarios": cases,
        "lender_break_even": [{"contribution": net, "pd_pp": 100 * net / base} for net in (0, 200)],
        "borrower_equivalent": {
            "pd_pp": borrower_pd,
            "ci": borrower_interval,
            "outside_feasible_range": max(borrower_pd, *borrower_interval) > 100,
        },
    }


def stress_profit(data, default_upper):
    lower, upper = data.profit.quantile([0.01, 0.99], interpolation="linear")
    bounded = data.profit.clip(lower, upper)
    grace = data.assigned_grace.eq(1)
    scenarios = {
        "winsor": data.assign(profit=bounded),
        "trim": data.loc[data.profit.between(lower, upper)],
        "missing_low": data.assign(profit=bounded.fillna(grace.map({True: lower, False: upper}))),
        "missing_high": data.assign(profit=bounded.fillna(grace.map({True: upper, False: lower}))),
    }
    results = {}
    for name, frame in scenarios.items():
        estimate = fit(frame, "profit")
        results[name] = {**estimate, "decision": pilot(default_upper, estimate["ci"][0])}
    return {"cutoffs": [float(lower), float(upper)], "scenarios": results}


def randomization(data, groups, *, draws=RI_DRAWS, seed=RI_SEED):
    columns = ["default_52w", "investment", "profit_recorded"]
    groups = groups.sort_values(["block_id", "group_id"])
    totals = data.groupby("group_id")[columns].sum().loc[groups.group_id].to_numpy()
    assignment = groups.assigned_grace.to_numpy()
    rng = np.random.Generator(np.random.PCG64(seed))
    shuffled = np.tile(assignment, (draws, 1))
    share = np.empty(len(groups))
    for positions in groups.groupby("block_id", sort=True).indices.values():
        labels = assignment[positions]
        share[positions] = labels.mean()
        shuffled[:, positions] = [rng.permutation(labels) for _ in range(draws)]
    centered = assignment - share
    # Every group has five borrowers, and every draw preserves block counts.
    denominator = np.square(centered) @ groups.borrowers.to_numpy()
    observed = centered @ totals / denominator
    null = (shuffled - share) @ totals / denominator
    counts = (np.abs(null) >= np.abs(observed) - 1e-12).sum(axis=0)
    return {
        "draws": draws,
        "seed": seed,
        "outcomes": {
            name: {
                "effect": float(value),
                "exceedances": int(count),
                "p": float((count + 1) / (draws + 1)),
            }
            for name, value, count in zip(columns, observed, counts, strict=True)
        },
    }


def summarize(data, groups, availability):
    default = fit(data, "default_52w", scale=100)
    profit = fit(data, "profit")
    investment = fit(
        data,
        "investment",
        controls=" + loan_use_flag + C(loan_size, Treatment(reference=10000))",
    )
    estimates = {"default_52w": default, "profit": profit, "investment": investment}
    decision = pilot(default["ci"][1], profit["ci"][0])
    return {
        "trial": {
            "blocks": int(groups.block_id.nunique()),
            "availability": availability,
            "balance": {
                name: {
                    "arm_means": [
                        float(data.loc[data.assigned_grace.eq(arm), name].mean() * scale)
                        for arm in (0, 1)
                    ],
                    **fit(data, name, scale=scale),
                }
                for name, scale in BALANCE.items()
            },
        },
        "estimates": estimates,
        "reproduction": {
            name: compare(estimate, PAPER[name]) for name, estimate in estimates.items()
        },
        "decision": {"cap": DEFAULT_CAP, "floor": PROFIT_FLOOR, **decision},
        "pricing": {**pricing(default, profit), "outstanding": fit(data, "outstanding_52w")},
        "robustness": {
            "profit_coverage": fit(data, "profit_recorded", scale=100),
            "profit_stress": stress_profit(data, default["ci"][1]),
            "randomization": randomization(data, groups),
        },
    }


def analyze(database, output=SITE_DIR / "data" / "results.json"):
    settings = {"memory_limit": "4GB"}
    with duckdb.connect(str(database), read_only=True, config=settings) as connection:
        data = connection.sql("""
            select * from borrowers join outcomes using (borrower_id) order by borrower_id
        """).df()
        groups = connection.sql("select * from loan_groups order by block_id, group_id").df()
        coverage = connection.sql("""
            select assigned_grace, count(*) as borrowers, count(distinct group_id) as groups,
                count(default_52w) as default_observed, count(investment) as investment_observed,
                count(profit) as profit_observed,
                count_if(survey3_income_recorded) as income_observed,
                count_if(survey3_income_recorded and profit is null) as income_without_profit,
                count_if(loan_use_flag = 1) as loan_use_flagged
            from borrowers join outcomes using (borrower_id)
            group by assigned_grace order by assigned_grace
        """)
        keys = coverage.columns
        availability = [dict(zip(keys, row, strict=True)) for row in coverage.fetchall()]
    results = summarize(data, groups, availability)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(output)
    return results
