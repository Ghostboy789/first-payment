"""Render the portfolio pages from the aggregate result file."""

import json
from math import ceil
from pathlib import Path

from config import SITE_DIR

AEA_ARTICLE = "https://www.aeaweb.org/articles?id=10.1257/aer.103.6.2196"
DEPOSIT = "https://doi.org/10.3886/E112672V1"
TEMPLATES = Path(__file__).resolve().parent / "templates"
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
            f"<span>{value}</span></td>"
            for label, value in zip(headers[1:], values, strict=True)
        )
        row_html.append(f'<tr role="row"><th scope="row" role="rowheader">{name}</th>{cells}</tr>')
    return (
        f'<div class="glass table-wrap"><table role="table"><caption>{caption}</caption>'
        f'<thead role="rowgroup"><tr role="row">{headings}</tr></thead>'
        f'<tbody role="rowgroup">{"".join(row_html)}</tbody></table></div>'
    )


def shell(slug, body):
    names = list(PAGES)
    next_page = names[(names.index(slug) + 1) % len(names)]
    nav = "".join(
        f'<a href="{key}.html"{" aria-current=page" if key == slug else ""}>{name}</a>'
        for key, name in PAGES.items()
    )
    onward = ""
    if slug != "index":
        next_label = "Back to overview" if next_page == "index" else f"Next · {PAGES[next_page]}"
        onward = (
            f'<div class="next"><a class="action" href="{next_page}.html">{next_label}</a></div>'
        )
    interaction = (
        '  <script src="decision.js" defer></script>\n' if slug in ("index", "decision") else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="description" content="A Kolkata microfinance trial, reviewed as a credit pilot.">
  <title>{PAGES[slug]} · First Payment</title>
  <script src="theme.js"></script>
  <link rel="stylesheet" href="style.css">
  <script src="story.js" defer></script>
{interaction}</head>
<body class="{"overview" if slug == "index" else "detail"}">
  <div class="mesh" aria-hidden="true"><i></i><i></i><i></i></div>
  <a class="skip" href="#content">Skip to content</a>
  <header class="nav-shell">
    <div class="glass nav-pill">
      <a class="wordmark" href="index.html">
        <span class="mark" aria-hidden="true"></span>First Payment</a>
      <nav class="nav-wide" aria-label="Study pages">{nav}</nav>
      <details class="nav-menu">
        <summary>Pages</summary>
        <nav class="glass" aria-label="Study pages">{nav}</nav>
      </details>
      <label class="theme" hidden>
        <span class="sr-only">Theme</span><span class="theme-icon" aria-hidden="true"></span>
        <select id="theme">
          <option value="system">System</option>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </label>
    </div>
  </header>
  <main id="content" class="wrap" tabindex="-1">
    {body}
    {onward}
  </main>
  <footer class="wrap footer">
    <div><strong>First Payment</strong><p>By Medhansh Shekhawat</p></div>
    <div class="footer-links">
      <a href="{AEA_ARTICLE}">AEA article page</a>
      <a href="{DEPOSIT}">openICPSR project 112672 V1</a>
      <a href="https://github.com/Ghostboy789">GitHub</a>
      <a href="https://in.linkedin.com/in/medhansh-shekhawat">LinkedIn</a>
    </div>
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


def metric(key, est, label, unit, digits):
    low, high = est["ci"]
    # Include zero in the scale so the interval has a meaningful baseline.
    start, end = min(low, 0), max(high, 0)
    span = end - start or 1
    offsets = (low - start, high - low, est["effect"] - start)
    left, width, dot = (100 * value / span for value in offsets)
    estimate = signed(est["effect"], digits)
    return f"""<article class="glass metric {key}">
      <h3>{label}</h3>
      <p class="metric-value"><span class="sr-only">{estimate}</span><span
        aria-hidden="true" data-count="{est["effect"]}" data-start="{low}" data-digits="{digits}">
        {estimate}</span> <span class="metric-unit">{unit}</span></p>
      <div class="interval" aria-hidden="true"
        style="--left:{left:.6f}%;--width:{width:.6f}%;--dot:{dot:.6f}%"><i></i><b></b></div>
      <p class="metric-evidence">95% CI {interval(est["ci"], digits)} {unit}
        <span>·</span> n={est["n"]:,}</p>
    </article>"""


def overview(results):
    estimates = results["estimates"]
    profit, default = estimates["profit"], estimates["default_52w"]
    pilot = results["decision"]
    price = results["pricing"]
    base = next(row for row in price["scenarios"] if row["lgd"] == price["base_lgd"])
    trim = results["robustness"]["profit_stress"]["scenarios"]["trim"]
    evidence_pages = {
        "trial": "Who borrowed and what changed.",
        "reproduction": "The published estimates alongside the rebuild.",
        "decision": "How the pilot rule uses the intervals.",
        "pricing": "Loss scenarios and break-even thresholds.",
        "robustness": "Trimming, missing values, and randomization checks.",
        "limits": "What the deposit can support.",
    }
    links = "".join(
        f'<a class="glass evidence-link" href="{key}.html"><strong>{PAGES[key]}</strong>'
        f"<span>{description}</span></a>"
        for key, description in evidence_pages.items()
    )
    return f"""<section class="hero" aria-labelledby="headline">
      <div class="hero-copy">
        <p class="label">Kolkata microfinance trial</p>
        <h1 id="headline">Two months<br>of grace.</h1>
        <p class="hero-question">Would you approve it?</p>
        <p class="lede">A randomized trial gave borrowers a longer wait before their first payment.
        The new contract changed both business profit and credit risk.</p>
        <a class="action primary" href="#outcomes">See the results</a>
      </div>
      <div class="hero-object">
        <div class="ledger-orbit" aria-hidden="true"></div>
        <div class="glass ledger-layer ledger-bottom" aria-hidden="true"></div>
        <div class="glass ledger-layer ledger-middle" aria-hidden="true"></div>
        <figure class="glass schedule">
          <figcaption>First payment due</figcaption>
          <div class="schedule-row">
            <div><span>Regular contract</span><strong>Two weeks</strong></div>
            <i class="schedule-track" aria-hidden="true"></i>
          </div>
          <div class="schedule-row grace">
            <div><span>Grace contract</span><strong>Two months</strong></div>
            <i class="schedule-track" aria-hidden="true"></i>
          </div>
          <p>After disbursement · fortnightly instalments</p>
        </figure>
      </div>
    </section>

    <section class="scene" id="outcomes" aria-labelledby="outcome-title">
      <div class="scene-head" data-reveal>
        <p class="label">Trial results</p>
        <h2 id="outcome-title">Profit rose.<br>So did default.</h2>
      </div>
      <div class="metrics" data-reveal>
        {metric("profit", profit, "Weekly business profit", "₹/week", 1)}
        {metric("risk", default, "Default at 52 weeks past due", "pp", 2)}
      </div>
      <p class="note scene-note">Effects compare assignment to the two contracts. Profit was
      recorded for a subset of borrowers around three years after disbursement.
      pp means percentage points.</p>
    </section>

    <section class="scene" aria-labelledby="rule-title" data-reveal>
      <div class="scene-head">
        <p class="label">The preset rule</p>
        <h2 id="rule-title">Two checks.<br>Both must pass.</h2>
        <p class="lede">The default cap and profit floor were set before looking at the results.</p>
      </div>
      <div class="rules glass">
        <div class="rule risk">
          <span>Default cap</span>
          <strong>{number(pilot["cap"])} pp</strong>
          <p>The upper end of the 95% default interval must be at or below the cap.</p>
        </div>
        <div class="rule profit">
          <span>Profit floor</span>
          <strong>₹{number(pilot["floor"], 0)}<small>/week</small></strong>
          <p>The lower end of the 95% profit interval must be strictly above the floor.</p>
        </div>
      </div>
    </section>

    <section class="scene verdict-scene" aria-labelledby="verdict-title" data-reveal>
      <div class="verdict-glow" aria-hidden="true"></div>
      <p class="label">Preset pilot verdict</p>
      <h2 id="verdict-title" class="verdict-word" data-passing="{str(pilot["pass"]).lower()}">
        {status(pilot["pass"])}
      </h2>
      <div class="verdict-summary">
        <div><span>Default · {status(pilot["default_pass"])}</span>
          <p><strong>{number(default["ci"][1])} pp</strong> upper bound</p></div>
        <div><span>Profit · {status(pilot["profit_pass"])}</span>
          <p><strong>₹{number(profit["ci"][0], 1)}/week</strong> lower bound</p></div>
      </div>
    </section>

    {decision_lab(results)}

    <section class="scene pricing-scene" aria-labelledby="price-title" data-reveal>
      <div class="scene-head">
        <p class="label">Price the risk</p>
        <h2 id="price-title">What could it cost?</h2>
        <p class="lede">Estimated extra credit loss with ₹{price["exposure"]:,} at risk per loan
        and {price["base_lgd"]:.0%} loss given default.</p>
        <a class="action" href="pricing.html">Explore the pricing</a>
      </div>
      <div class="glass price-card risk">
        <p class="label">Extra expected loss</p>
        <p class="price-value">₹{number(base["loss"], 1)}</p>
        <p class="price-unit">per loan</p>
        <p class="metric-evidence">95% CI ₹{interval(base["ci"], 1)} · n={default["n"]:,}</p>
      </div>
    </section>

    <section class="scene" aria-labelledby="limits-title" data-reveal>
      <div class="scene-head">
        <p class="label">Limits of the evidence</p>
        <h2 id="limits-title">What this trial<br>cannot establish.</h2>
      </div>
      <dl class="limits-list">
        <div><dt>The grace period on its own</dt>
          <dd>Maturity and effective interest changed with the repayment schedule.</dd></div>
        <div><dt>Profit across all borrowers</dt>
          <dd>Profit was measured only where it was recorded. Missing follow-up leaves the
          full-cohort effect unresolved.</dd></div>
        <div><dt>A profit gain that holds after trimming</dt>
          <dd>Trimmed profit was {signed(trim["effect"], 1)} ₹/week (95% CI
          {interval(trim["ci"], 1)} ₹/week, n={trim["n"]:,}). Profit gate
          {status(trim["decision"]["profit_pass"])}.</dd></div>
      </dl>
    </section>

    <section class="scene" aria-labelledby="evidence-title" data-reveal>
      <div class="scene-head"><h2 id="evidence-title">Explore the evidence.</h2></div>
      <div class="evidence-grid">{links}</div>
    </section>"""


def trial(results):
    trial_data = results["trial"]
    control, grace = trial_data["availability"]
    total = control["borrowers"] + grace["borrowers"]
    groups = control["groups"] + grace["groups"]
    blocks = trial_data["blocks"]
    coverage_rows = [
        ("Default observed / missing", "default_observed"),
        ("Deposited loan spending observed / missing", "investment_observed"),
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
        "Available-case means by arm. Intervals and n refer to the block-adjusted differences.",
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
    <section data-reveal class="chapter">
      <h2>What changed</h2>
      <div><p>Groups were formed and loans approved before assignment. The regular arm had
      {control["groups"]} groups and the grace arm had {grace["groups"]}. The grace contract
      also changed maturity and effective interest, even though nominal charges stayed the same.</p>
      <p>Lender records tracked repayment. The loan-use survey measured how the loan was spent.
      The three-year survey asked about profits for current or most recently operating businesses.
      </p></div>
    </section>
    <section data-reveal class="chapter wide"><h2>Follow-up coverage</h2>
      {coverage}
      <p>Profit was missing despite a recorded income item for {control["income_without_profit"]}
      regular and {grace["income_without_profit"]} grace borrowers. The adjusted difference in
      profit coverage was {signed(attrition["effect"])} pp
      (95% CI {interval(attrition["ci"])} pp, n={attrition["n"]}).
      Income item availability is a proxy for Survey 3 coverage.</p>
    </section>
    <section data-reveal class="chapter wide"><h2>Baseline balance</h2>
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
    <section data-reveal class="chapter wide"><h2>Published and rebuilt</h2>
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
      <p><a href="{AEA_ARTICLE}">Field, Pande, Papp and Rigol · Tables 1–3</a></p>
    </section>"""
    )


def decision_lab(results):
    default, profit = (results["estimates"][key] for key in ("default_52w", "profit"))
    fixed = results["decision"]
    rows = []
    for key, name, est, limit, bound, tick, step, unit, digits in (
        ("default", "Maximum extra default", default, fixed["cap"], "upper", 10, "0.01", "pp", 2),
        (
            "profit", "Minimum weekly profit gain", profit, fixed["floor"],
            "lower", 1000, "1", "₹/week", 1,
        ),
    ):
        endpoint = est["ci"][1 if bound == "upper" else 0]
        maximum = tick * max(1, ceil(max(est["ci"][1], limit) / tick))
        band = [max(0, min(100, 100 * value / maximum)) for value in est["ci"]]
        passes = fixed[key + "_pass"]
        threshold = number(limit, 2 if key == "default" else 0)
        rows.append(f"""<div class="gate {key}">
          <div class="gate-title">
            <h3><label for="{key}-limit">{name}</label></h3>
            <p class="gate-result" data-passing="{str(passes).lower()}">
              <strong id="{key}-status">{status(passes)}</strong></p>
          </div>
          <p id="{key}-evidence" class="note">{bound.capitalize()} bound
          <strong>{number(endpoint, digits)} {unit}</strong><br>
          95% CI {interval(est["ci"], digits)} {unit} · n={est["n"]:,}</p>
          <div class="control-line">
            <span>Threshold</span>
            <strong id="{key}-value">{threshold} {unit}</strong>
          </div>
          <div class="rail" style="--low:{band[0]:.6f}%;--high:{band[1]:.6f}%;
          --threshold:{100 * limit / maximum:.6f}%">
            <div class="band" aria-hidden="true"><i></i><b></b></div>
            <input id="{key}-limit" type="range" min="0" max="{maximum}" step="{step}"
              value="{limit}" aria-describedby="{key}-evidence" hidden>
          </div>
          <div class="axis" aria-hidden="true"><span>0</span><span>{maximum:,} {unit}</span></div>
        </div>""")
    return f"""<section class="scene lab-scene" id="scenario"
      aria-labelledby="lab-heading" data-reveal>
      <div class="scene-head">
        <p class="label">Decision simulator</p>
        <h2 id="lab-heading">Where is your line?</h2>
        <p class="lede">Set a cap for extra default and a floor for weekly profit.</p>
      </div>
      <div class="glass decision-lab"
        data-upper="{default["ci"][1]}" data-lower="{profit["ci"][0]}">
        <div class="lab-head">
          <p class="note">Shading marks the 95% interval. The marker shows your threshold.</p>
          <button class="action" type="button" id="reset" hidden>Reset thresholds</button>
        </div>
        <div class="lab-gates">{"".join(rows)}</div>
        <div class="lab-result" data-passing="{str(fixed["pass"]).lower()}"
          role="status" aria-live="polite" aria-atomic="true">
          <p><span class="label">Scenario verdict</span>
          <strong id="joint-status">Pilot {status(fixed["pass"])}</strong></p>
          <p id="joint-detail">Default {"passes" if fixed["default_pass"] else "fails"} ·
          Profit {"passes" if fixed["profit_pass"] else "fails"}</p>
        </div>
        <p id="slider-fallback" class="note">Turn on JavaScript to change the preset thresholds.</p>
      </div>
    </section>"""


def decision(results):
    fixed = results["decision"]
    return (
        page_header(
            "decision",
            f"The preset decision. {status(fixed['pass'])}.",
            "The pilot rule uses the upper end of the default interval and the lower end "
            "of the profit interval.",
        )
        + decision_lab(results)
        + f"""
    <section data-reveal class="chapter"><h2>How to read it</h2><div>
      <p>Extra default clears its gate when the upper endpoint is at or below the cap.
      The profit gate requires the lower endpoint to be strictly above the floor.</p>
      <p>The preset default cap was {number(fixed["cap"])} percentage points and the
      preset profit floor was ₹{number(fixed["floor"], 0)} per week. The controls model
      alternative thresholds for the same trial results.</p>
    </div></section>"""
    )


def pricing_page(results):
    price = results["pricing"]
    profit = results["estimates"]["profit"]
    default_n = results["estimates"]["default_52w"]["n"]
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
        f"Scenario exposure ₹{price['exposure']:,}. "
        f"Intervals use the extra-default estimate (n={default_n}).",
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
            f"(95% CI ₹{interval(base['ci'], 1)}, n={default_n}).",
        )
        + f"""
    <section data-reveal class="chapter wide"><h2>A credit-loss surcharge</h2>
      <p class="formula">Extra default × exposure × loss given default</p>
      {scenario_table}
      <p>Exposure uses original principal as a proxy for the balance at risk. Loss given default is
      the share of that exposure the lender fails to recover. The scenarios hold both fixed across
      arms. Outstanding debt in the data rose by ₹{number(out["effect"], 1)} per loan
      (95% CI ₹{interval(out["ci"], 1)}, n={out["n"]}). That balance can still be recovered.</p>
    </section>
    <section data-reveal class="chapter wide"><h2>Where loss breaks even</h2>
      <p class="formula">contribution ÷ (exposure × loss given default)</p>
      {break_even}
      <p>The borrower profit gain was ₹{number(profit["effect"], 1)} per week
      (95% CI ₹{interval(profit["ci"], 1)}, n={profit["n"]}). Using that one week as a hypothetical
      budget implies {number(proxy["pd_pp"])} pp
      (95% CI {interval(proxy["ci"])} pp, n={profit["n"]}).{feasibility}
      The borrower receives that profit around three years after disbursement.
      The lender bears the credit loss on the trial loan. This comparison shows scale across
      horizons.</p>
      <p>The surcharge covers only the modeled credit-loss difference. Funding, timing, operating
      costs and borrower responses to pricing are outside the calculation.</p>
    </section>"""
    )


def robustness(results):
    rob = results["robustness"]
    investment = rob["investment_unflagged"]
    investment_interval = (
        "The 95% interval stays above zero."
        if investment["positive_interval"]
        else "The 95% interval fails the positive-effect check."
    )
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
    <section data-reveal class="chapter wide"><h2>Profit under stress</h2>
      {stress_table}
      <p>Winsorizing clips values to the pooled 1st and 99th percentiles
      (₹{interval(stress["cutoffs"], 1)} per week). Trimming drops rows outside those cutoffs.
      The trim’s weekly-profit interval crosses zero.</p>
      <p>The missing-profit scenarios assign the cutoffs in opposite directions by arm.
      They bound the fitted coefficient for the clipped outcome under the stated support assumption.
      Each interval is conditional on its completed values and cutoffs.</p>
    </section>
    <section data-reveal class="chapter wide"><h2>Reassigning loan groups</h2>
      {randomization_table}
      <p>Each of the {ri["draws"]:,} simulated draws preserves the grace group count in each
      batch. The statistic is the absolute batch-adjusted effect. The loan-spending check
      uses the batch-only model. The profit test is for whether a value was recorded.</p>
    </section>
    <section data-reveal id="loan-use" class="chapter"><h2>Loan-use coverage</h2><div>
      <p>After excluding flagged records, the estimated change in business spending was
      {signed(investment["effect"], 1)} ₹/loan (95% CI {interval(investment["ci"], 1)} ₹/loan,
      n={investment["n"]}). {investment_interval}</p>
      <p>This follow-up check uses the released flag to select records and adjusts for batch and
      loan size. The provenance of the selected records is uncertain. See the
      <a href="limits.html#loan-use-source">loan-use source notes</a>.</p>
    </div>
    </section>"""
    )


def data_page(results):
    arms = results["trial"]["availability"]
    total = sum(arm["borrowers"] for arm in arms)
    flagged = sum(arm["loan_use_flagged"] for arm in arms)
    unflagged = total - flagged
    return (
        page_header(
            "limits",
            "What this trial can tell us.",
            f"The data cover {total} borrowers at one lender. Follow-up and contract terms "
            "set the limits of the decision.",
        )
        + f"""
    <section data-reveal class="chapter"><h2>Reading the estimates</h2><div>
      <p>A percentage point is the absolute difference between two rates.
      A 95% CI gives a range of estimates compatible with the data under the fitted model.
      Clustering accounts for shared outcomes among members of the same loan group.</p>
      <p>The experiment compares assignment to whole contracts. The grace arm also had a longer
      maturity and a lower effective interest rate. Evidence comes from loans assigned in 2007
      at one Kolkata lender. Applying it to another product or cohort would require new data.</p>
      <p>Reported business profit is available for a subset of borrowers.</p>
    </div></section>
    <section data-reveal id="loan-use-source" class="chapter"><h2>Loan-use survey coverage</h2><div>
      <p>The paper’s methods report 93% completion for the Survey 2 loan-use module.
      The Table 1 note says all clients completed it. The deposit confirms that the regression
      used {total} records with a value for business spending.</p>
      <p>The Table 1 script adjusts for a flag that marks {flagged} records. Its regular-contract
      reference mean excludes those marked records. The {unflagged} unflagged records are
      {unflagged / total:.1%} of the file, which matches the reported completion rate after
      rounding. The deposit and appendix leave the flag’s meaning and survey provenance
      uncertain.</p>
      <p><a href="robustness.html#loan-use">See the estimate after excluding flagged records</a></p>
      <p><a href="{AEA_ARTICLE}">Paper, Section II.A and Table 1</a> ·
      <a href="https://www.aeaweb.org/articles/materials/2402">Supplemental appendix</a></p>
    </div></section>
    <section data-reveal class="chapter"><h2>Data and code</h2><div>
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
    for name in ("style.css", "theme.js", "story.js", "decision.js"):
        (directory / name).write_bytes((TEMPLATES / name).read_bytes())


if __name__ == "__main__":
    render(json.loads((SITE_DIR / "data" / "results.json").read_text(encoding="utf-8")))
