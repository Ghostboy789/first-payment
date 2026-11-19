"""Render the portfolio pages from the aggregate result file."""

import json

from config import SITE_DIR

PAPER = "https://doi.org/10.1257/aer.103.6.2196"
DEPOSIT = "https://doi.org/10.3886/E112672V1"
PAGES = {
    "index": "Overview",
    "trial": "The trial",
    "reproduction": "Reproduction",
    "decision": "The decision",
    "pricing": "Pricing",
    "robustness": "Robustness",
    "limits": "Data and limits",
}
OUTCOMES = {
    "default_52w": ("Default at 52 weeks past due", "pp", 2),
    "profit": ("Weekly business profit", "₹/week", 1),
    "investment": ("Loan spending on the business", "₹/loan", 1),
}


def number(value, digits=2):
    return f"{value:,.{digits}f}".replace("-", "−")


def signed(value, digits=2):
    return ("+" if value > 0 else "") + number(value, digits)


def interval(bounds, digits=2):
    return f"{number(bounds[0], digits)} to {number(bounds[1], digits)}"


def status(passes):
    return "PASS" if passes else "FAIL"


def table(headers, rows, caption):
    headings = "".join(f'<th scope="col" role="columnheader">{header}</th>' for header in headers)
    row_html = []
    for name, *values in rows:
        cells = "".join(
            f'<td role="cell"><span class="cell-label" aria-hidden="true">{label}</span>'
            f"{value}</td>"
            for label, value in zip(headers[1:], values, strict=True)
        )
        row_html.append(f'<tr role="row"><th scope="row" role="rowheader">{name}</th>{cells}</tr>')
    return (
        f'<table role="table"><caption>{caption}</caption>'
        f'<thead role="rowgroup"><tr role="row">{headings}</tr></thead>'
        f'<tbody role="rowgroup">{"".join(row_html)}</tbody></table>'
    )


def shell(slug, body):
    names = list(PAGES)
    next_page = names[(names.index(slug) + 1) % len(names)]
    nav = "".join(
        f'<a href="{key}.html"{" aria-current=page" if key == slug else ""}>{name}</a>'
        for key, name in PAGES.items()
    )
    next_label = "Back to" if next_page == "index" else "Next"
    interaction = '  <script src="decision.js" defer></script>\n' if slug == "decision" else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="description" content="A Kolkata microfinance trial, reviewed as a credit pilot.">
  <title>{PAGES[slug]} · First Payment</title>
  <link rel="stylesheet" href="style.css">
  <script src="theme.js" defer></script>
{interaction}</head>
<body>
  <a class="skip" href="#content">Skip to content</a>
  <header class="wrap masthead">
    <a class="wordmark" href="index.html">First Payment</a>
    <label class="theme" hidden>
      <span>Theme</span>
      <select id="theme">
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
    <nav aria-label="Study pages">{nav}</nav>
  </header>
  <main id="content" class="wrap" tabindex="-1">
    {body}
    <div class="next">
      <a href="{next_page}.html">{next_label} · {PAGES[next_page]}</a>
    </div>
  </main>
  <footer class="wrap masthead footer">
    <a href="https://github.com/Ghostboy789">Medhansh Shekhawat</a>
    <a href="{PAPER}">Trial paper</a>
    <a href="{DEPOSIT}">Replication deposit</a>
  </footer>
</body>
</html>
"""


def page_header(slug, title, lede):
    return f"""<header class="page-header">
      <p class="label">{PAGES[slug]}</p>
      <h1>{title}</h1>
      <p class="lede">{lede}</p>
    </header>"""


def overview(results):
    cards = []
    for key, (label, unit, digits) in OUTCOMES.items():
        est = results["estimates"][key]
        cards.append(f"""<div><dt>{label}</dt>
          <dd><strong>{signed(est["effect"], digits)}</strong> {unit}</dd>
          <dd class="note">95% CI {interval(est["ci"], digits)} · n={est["n"]}</dd></div>""")
    pilot = results["decision"]
    default_upper = results["estimates"]["default_52w"]["ci"][1]
    return f"""<section class="hero" aria-labelledby="headline">
      <div>
        <p class="label">Kolkata · Microfinance</p>
        <h1 id="headline">When should the first payment be due?</h1>
        <p class="lede">A longer wait before repayment raised reported weekly business profit
        among borrowers with follow-up data. The estimated rise in default was too large for
        this pilot rule.</p>
        <a class="primary" href="decision.html">Try the risk-tolerance sliders</a>
      </div>
      <div>
        <figure class="schedule" aria-labelledby="schedule-title">
          <h2 id="schedule-title">When repayment started</h2>
          <p class="schedule-origin"><span aria-hidden="true"></span> Loan disbursed</p>
          <div class="arm arm-regular">
            <div class="arm-label"><strong>Regular</strong><span>After two weeks</span></div>
            <div class="track" aria-hidden="true"><span></span></div>
          </div>
          <div class="arm arm-grace">
            <div class="arm-label"><strong>Grace period</strong><span>After two months</span></div>
            <div class="track" aria-hidden="true"><span></span></div>
          </div>
          <figcaption>Approximate schedule. Both contracts used fortnightly
          instalments.</figcaption>
        </figure>
        <p class="verdict"><strong>Pilot {status(pilot["pass"])}</strong>
        <span>Default upper bound {number(default_upper)} pp · cap {number(pilot["cap"])} pp</span>
        </p>
      </div>
    </section>
    <section class="chapter" aria-labelledby="readout">
      <h2 id="readout">What changed</h2>
      <div>
        <dl class="metrics">{"".join(cards)}</dl>
        <p class="note">Effects compare assignment to the two contracts. The profit measure was
        taken around three years after disbursement.</p>
      </div>
    </section>"""


def trial(results):
    trial_data = results["trial"]
    control, grace = trial_data["availability"]
    total = control["borrowers"] + grace["borrowers"]
    groups = control["groups"] + grace["groups"]
    blocks = trial_data["blocks"]
    coverage_rows = [
        ("Default observed / missing", "default_observed"),
        ("Loan spending observed / missing", "investment_observed"),
        ("Profit observed / missing", "profit_observed"),
        ("Survey 3 income item observed / missing", "income_observed"),
    ]
    coverage = table(
        ("Outcome", "Regular", "Grace period"),
        [
            (label, *(f"{arm[key]} / {arm['borrowers'] - arm[key]}" for arm in (control, grace)))
            for label, key in coverage_rows
        ],
        "Recorded fields by assigned arm. Counts describe the deposited cohort.",
    )
    balance_rows = [
        ("Age (years)", "age", ""),
        ("Married (%)", "married", " pp"),
        ("Schooling (years)", "education", ""),
        ("Household size", "household_size", ""),
        ("Household had a business (%)", "baseline_business", " pp"),
    ]
    balance = table(
        ("Measure", "Regular", "Grace period", "Adjusted difference and 95% CI", "n"),
        [
            (
                label,
                *(number(mean) for mean in record["arm_means"]),
                f"{signed(record['effect'])}{unit}<br>{interval(record['ci'])}{unit}",
                record["n"],
            )
            for label, key, unit in balance_rows
            for record in (trial_data["balance"][key],)
        ],
        "Available-case baseline means and block-adjusted differences, grace minus regular.",
    )
    attrition = results["robustness"]["profit_coverage"]
    return (
        page_header(
            "trial",
            "Two contracts, one randomized trial.",
            f"Village Financial Services assigned {groups} loan groups in {blocks} batches. "
            f"The experiment followed {total} borrowers in Kolkata.",
        )
        + f"""
    <section class="chapter">
      <h2>What changed</h2>
      <div><p>Groups were formed and loans approved before assignment. The regular arm had
      {control["groups"]} groups and the grace arm had {grace["groups"]}. The grace contract
      also changed maturity and effective interest, even though nominal charges stayed the same.</p>
      <p>Lender records tracked repayment. The loan-use survey measured how the loan was spent.
      The three-year survey asked about profits for current or most recently operating businesses.
      </p></div>
    </section>
    <section class="chapter wide"><h2>Follow-up coverage</h2>
      {coverage}
      <p>Profit was missing despite a recorded income item for {control["income_without_profit"]}
      regular and {grace["income_without_profit"]} grace borrowers. The adjusted difference in
      profit coverage was {signed(attrition["effect"])} pp
      (95% CI {interval(attrition["ci"])} pp, n={attrition["n"]}).
      Income item availability is a proxy for Survey 3 coverage.</p>
    </section>
    <section class="chapter wide"><h2>Baseline balance</h2>
      {balance}
      <p>Marital status was the clearest observed baseline difference. The intervals are descriptive
      and are shown individually, with no joint balance claim.</p>
    </section>"""
    )


def reproduction(results):
    estimates = results["estimates"]
    comparisons = results["reproduction"]
    rows = []
    for key, (label, unit, digits) in OUTCOMES.items():
        est, paper = estimates[key], comparisons[key]
        rows.append(
            (
                f"{label} ({unit})",
                f"{signed(paper['paper_effect'], digits)}<br>{interval(paper['paper_ci'], digits)}",
                f"{signed(est['effect'], digits)}<br>{interval(est['ci'], digits)}",
                f"{number(paper['paper_se'], digits)} / {number(est['se'], digits)}",
                f"{signed(paper['effect_gap'], 4)} / {signed(paper['se_gap'], 4)}",
                f"{paper['paper_n']} / {est['n']}",
                status(paper["pass"]),
            )
        )
    passes = sum(item["pass"] for item in comparisons.values())
    return (
        page_header(
            "reproduction",
            "Three estimates, checked against the paper.",
            f"{passes} of {len(comparisons)} comparisons met the preset rule for the coefficient, "
            "standard error and sample size.",
        )
        + f"""
    <section class="chapter wide"><h2>Published and rebuilt</h2>
      {
            table(
                (
                    "Outcome",
                    "Paper and 95% CI",
                    "Rebuilt and 95% CI",
                    "SE, paper / rebuilt",
                    "Gaps, effect / SE",
                    "n, paper / rebuilt",
                    "Match",
                ),
                rows,
                "Paper intervals approximate the printed assignment effects.",
            )
        }
      <p>Gaps are rebuilt minus paper. The matching tolerance was half the last printed unit.
      All three fits use batch fixed effects and loan-group clustered uncertainty. The investment
      fit also adjusts for loan size and the deposited matching flag.</p>
      <p><a href="{PAPER}">Field, Pande, Papp and Rigol · Tables 1–3</a></p>
    </section>"""
    )


def decision(results):
    default, profit = (results["estimates"][key] for key in ("default_52w", "profit"))
    fixed = results["decision"]
    rows = []
    for key, name, est, limit, bound, maximum, step, unit, digits in (
        ("default", "Maximum extra default", default, fixed["cap"], "upper", 20, "0.01", "pp", 2),
        (
            "profit",
            "Minimum weekly profit gain",
            profit,
            fixed["floor"],
            "lower",
            2000,
            "1",
            "₹/week",
            1,
        ),
    ):
        endpoint = est["ci"][1 if bound == "upper" else 0]
        band = [100 * value / maximum for value in est["ci"]]
        passes = fixed[key + "_pass"]
        rows.append(f"""<div class="gate" data-passing="{str(passes).lower()}">
          <h3><label for="{key}-limit">{name}</label></h3>
          <p id="{key}-evidence" class="note">95% CI {interval(est["ci"], digits)} {unit} ·
          {bound.capitalize()} bound <strong>{number(endpoint, digits)} {unit}</strong>
          · n={est["n"]}</p>
          <div class="control-line" hidden>
            <span>Scenario threshold</span>
            <span id="{key}-value">{number(limit, digits)} {unit}</span>
          </div>
          <div class="band" aria-hidden="true" style="--low:{band[0]:.6f}%;--high:{band[1]:.6f}%;
          --threshold:{100 * limit / maximum:.6f}%"><span></span></div>
          <input id="{key}-limit" type="range" min="0" max="{maximum}" step="{step}" value="{limit}"
            aria-describedby="{key}-evidence" hidden>
          <div class="axis" aria-hidden="true"><span>0</span><span>{maximum:,} {unit}</span></div>
          <p class="gate-result"><strong id="{key}-status">{status(passes)}</strong></p>
        </div>""")
    return (
        page_header(
            "decision",
            "The pilot fails its default cap."
            if not fixed["default_pass"]
            else "The evidence meets the default cap.",
            "Compare the confidence interval endpoints with the thresholds. Both checks must pass.",
        )
        + f"""
    <section class="decision-lab" aria-labelledby="lab-heading"
      data-upper="{default["ci"][1]}" data-lower="{profit["ci"][0]}">
      <div class="lab-head">
        <div><h2 id="lab-heading">Test a risk tolerance</h2>
        <p class="note">The shaded band is the estimate’s 95% interval.
        The vertical line is the threshold.</p></div>
        <button type="button" id="reset" hidden>Reset thresholds</button>
      </div>
      {"".join(rows)}
      <div class="verdict" role="status" aria-live="polite" aria-atomic="true">
        <strong id="joint-status">Pilot {status(fixed["pass"])}</strong>
        <span id="joint-detail">Preset default cap {number(fixed["cap"])} pp ·
        profit must exceed ₹{number(fixed["floor"], 0)}/week.</span>
      </div>
      <p id="slider-fallback" class="note">Turn on JavaScript to change the thresholds.</p>
    </section>
    <section class="chapter"><h2>How to read it</h2><div>
      <p>Extra default clears its gate when the upper endpoint is within the cap.
      The profit gate requires the lower endpoint to be strictly above the floor.</p>
      <p>The pilot starts at two extra defaults per 100 borrowers and credible positive profit.
      Changing the sliders tests a scenario. The original decision stays fixed.</p>
    </div></section>"""
    )


def pricing_page(results):
    price = results["pricing"]
    profit = results["estimates"]["profit"]
    base = next(row for row in price["scenarios"] if row["lgd"] == price["base_lgd"])
    out = price["outstanding"]
    scenario_table = table(
        ("Loss given default", "Extra loss per loan", "95% CI"),
        [
            (
                f"{row['lgd']:.0%}" + (" · base" if row == base else ""),
                f"₹{number(row['loss'], 1)}",
                f"₹{interval(row['ci'], 1)}",
            )
            for row in price["scenarios"]
        ],
        f"Scenario exposure ₹{price['exposure']:,}. Intervals carry uncertainty in extra default.",
    )
    break_even = table(
        ("Fixed lender contribution", "Break-even default increase"),
        [
            (f"₹{number(row['contribution'], 0)} per loan", f"{number(row['pd_pp'])} pp")
            for row in price["lender_break_even"]
        ],
        "Lender scenarios at base loss given default. Fixed inputs have no sampling interval.",
    )
    proxy = price["borrower_equivalent"]
    feasibility = (
        " Part of that range exceeds the feasible 100-point probability change."
        if proxy["outside_feasible_range"]
        else ""
    )
    return (
        page_header(
            "pricing",
            "What would the extra defaults cost?",
            f"Under the base assumptions, extra loss is ₹{number(base['loss'], 1)} per loan "
            f"(95% CI ₹{interval(base['ci'], 1)}).",
        )
        + f"""
    <section class="chapter wide"><h2>A credit-loss surcharge</h2>
      <p class="formula">Extra default × exposure × loss given default</p>
      {scenario_table}
      <p>Exposure uses original principal as a proxy for the balance at risk. Loss given default is
      the share of that exposure the lender fails to recover. The scenarios hold both fixed across
      arms. Outstanding debt in the data rose by ₹{number(out["effect"], 1)} per loan
      (95% CI ₹{interval(out["ci"], 1)}, n={out["n"]}). That balance can still be recovered.</p>
    </section>
    <section class="chapter wide"><h2>Where loss breaks even</h2>
      {break_even}
      <p>Break-even equals the lender’s additional contribution divided by exposure times loss
      given default. Both illustrative thresholds fall below the trial’s upper default bound.</p>
      <p>The borrower profit gain was ₹{number(profit["effect"], 1)} per week
      (95% CI ₹{interval(profit["ci"], 1)}, n={profit["n"]}). Using that one week as a hypothetical
      budget implies {number(proxy["pd_pp"])} pp (95% CI {interval(proxy["ci"])} pp).{feasibility}
      The borrower receives that profit around three years after disbursement.
      The lender bears the credit loss on the trial loan. This comparison shows scale across
      horizons.</p>
      <p>The surcharge covers only the modeled credit-loss difference. Funding, timing, operating
      costs and borrower responses to pricing are outside the calculation.</p>
    </section>"""
    )


def robustness(results):
    rob = results["robustness"]
    stress = rob["profit_stress"]
    names = {
        "winsor": "Winsorized profit",
        "trim": "Trimmed profit",
        "missing_low": "Missing profit · low endpoint",
        "missing_high": "Missing profit · high endpoint",
    }
    stress_table = table(
        ("Scenario", "Effect (₹/week)", "95% CI (₹/week)", "n", "Profit gate", "Pilot"),
        [
            (
                names[key],
                signed(row["effect"], 1),
                interval(row["ci"], 1),
                row["n"],
                status(row["decision"]["profit_pass"]),
                status(row["decision"]["pass"]),
            )
            for key, row in stress["scenarios"].items()
        ],
        "The primary default estimate and cap are fixed across the profit scenarios.",
    )
    ri = rob["randomization"]
    randomization_table = table(
        ("Outcome", "Permutation p-value"),
        [
            (name, number(ri["outcomes"][key]["p"], 4))
            for name, key in (
                ("52-week default", "default_52w"),
                ("Deposited loan spending", "investment"),
                ("Profit recorded", "profit_recorded"),
            )
        ],
        "Two-sided sharp-null checks. P-values summarize the permutation distribution.",
    )
    return (
        page_header(
            "robustness",
            "The profit result depends on the tail and missing values.",
            "Every profit scenario leaves the preset pilot rejected on default.",
        )
        + f"""
    <section class="chapter wide"><h2>Profit under stress</h2>
      {stress_table}
      <p>Winsorizing clips values to the pooled 1st and 99th percentiles
      (₹{interval(stress["cutoffs"], 1)} per week). Trimming drops rows outside those cutoffs.
      The trim’s weekly-profit interval crosses zero.</p>
      <p>The missing-profit scenarios assign the cutoffs in opposite directions by arm.
      They bound the fitted coefficient for the clipped outcome under the stated support assumption.
      Each interval is conditional on its completed values and cutoffs.</p>
    </section>
    <section class="chapter wide"><h2>Reassigning loan groups</h2>
      {randomization_table}
      <p>Each of the {ri["draws"]:,} simulated draws preserves the grace group count in each
      batch. The statistic is the absolute batch-adjusted effect. The loan-spending check
      uses the batch-only model. The profit test is for whether a value was recorded.</p>
    </section>"""
    )


def data_page(results):
    total = sum(arm["borrowers"] for arm in results["trial"]["availability"])
    return (
        page_header(
            "limits",
            "What this trial can tell us.",
            f"The data cover {total} borrowers at one lender. Follow-up and contract terms "
            "set the limits of the decision.",
        )
        + f"""
    <section class="chapter"><h2>Reading the estimates</h2><div>
      <p>A percentage point is the absolute difference between two rates.
      A 95% CI gives a range of estimates compatible with the data under the fitted model.
      Clustering accounts for shared outcomes among members of the same loan group.</p>
      <p>The experiment compares assignment to whole contracts. The grace arm also had a longer
      maturity and a lower effective interest rate. Evidence comes from loans assigned in 2007
      at one Kolkata lender. Applying it to another product or cohort would require new data.</p>
      <p>Reported business profit is available for a subset. The paper’s text reports 93% loan-use
      survey coverage, while Table 1 and the deposited outcome use all {total} rows.
      The deposited matching flag is used as coded. Its exact construction is unresolved.</p>
    </div></section>
    <section class="chapter"><h2>Data and code</h2><div>
      <p>Source data by Erica Field, Rohini Pande, John Papp and Natalia Rigol, published by the
      American Economic Association and distributed by ICPSR. The original deposit licenses code
      under BSD-3-Clause and other material under CC BY 4.0. This site presents independently
      calculated aggregates from that deposit. Use the deposit link to obtain the original data.</p>
      <p><a href="{DEPOSIT}">AEA replication package · project 112672 V1</a></p>
      <p><a href="data/results.json">Download the aggregate results</a></p>
    </div></section>"""
    )


def render(results, directory=SITE_DIR):
    pages = (overview, trial, reproduction, decision, pricing_page, robustness, data_page)
    for slug, content in zip(PAGES, pages, strict=True):
        (directory / f"{slug}.html").write_text(shell(slug, content(results)), encoding="utf-8")


if __name__ == "__main__":
    render(json.loads((SITE_DIR / "data" / "results.json").read_text(encoding="utf-8")))
