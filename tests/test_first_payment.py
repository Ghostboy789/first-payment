import hashlib
import json
from zipfile import ZipFile

import pandas as pd
import pytest

import extract as package
from analysis import analyze, pilot
from build import build_marts
from config import SITE_DIR, STATA_MEMBER
from render_site import PAGES, render


def test_pilot_boundaries():
    assert pilot(2.0, 0.01) == {"default_pass": True, "profit_pass": True, "pass": True}
    assert pilot(2.0, 0.0) == {"default_pass": True, "profit_pass": False, "pass": False}
    assert pilot(2.00001, 0.01) == {"default_pass": False, "profit_pass": True, "pass": False}


def test_synthetic_archive_to_site(tmp_path, monkeypatch):
    rows = []
    baseline = {
        "Age_C": 31,
        "Married_C": 1,
        "Years_Education_C": 8,
        "HH_Size_C": 4,
        "Has_Business_C": 0,
    }
    for block in (1, 2):
        for group in range(4):
            grace = int(group >= 2)
            for member in range(5):
                loan = 8000 if member % 2 == 0 else 10000
                flag = int(member == 2)
                rows.append(
                    {
                        "slid": 1 + len(rows),
                        "sec_group_name": f"batch {block}, group {group}",
                        "sec_treat": grace,
                        "Stratification_Dummies": block,
                        "Match3rd_in3rd": flag,
                        "sec_loanamount": loan,
                        "not_finished_aug19": int(
                            (grace and member == 0) or (group % 2 == 0 and member == 1)
                        ),
                        "Outstanding_Loan_Amount_Default": 20 + 2 * grace,
                        "Business_Expenditures": 200 + 100 * grace + flag * 10 + loan // 10,
                        "Profit": 200 + 25 * grace + member + group % 2 if member < 4 else None,
                        "Income": 1000,
                        **baseline,
                        **{
                            "miss_" + name: int(member == 2 and name == "Age_C")
                            for name in baseline
                        },
                    }
                )
    stata = tmp_path / "synthetic.dta"
    pd.DataFrame(rows[::-1]).to_stata(stata, write_index=False)
    zip_path = tmp_path / "synthetic.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.write(stata, STATA_MEMBER)
    parquet = tmp_path / "trial.parquet"
    with pytest.raises(ValueError, match="does not match"):
        package.extract(zip_path, parquet)
    assert not parquet.exists()

    monkeypatch.setattr(package, "STATA_SHA256", hashlib.sha256(stata.read_bytes()).hexdigest())
    package.extract(zip_path, parquet)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["rows"] == 40
    assert manifest["parquet_sha256"] == hashlib.sha256(parquet.read_bytes()).hexdigest()
    assert pd.read_parquet(parquet).slid.to_list() == list(range(1, 41))

    database = tmp_path / "trial.duckdb"
    build_marts(parquet, database)
    output = tmp_path / "results.json"
    result = analyze(database, output)
    assert result["estimates"]["default_52w"]["effect"] == pytest.approx(20)
    assert result["estimates"]["profit"]["effect"] == pytest.approx(25)
    assert result["estimates"]["investment"]["effect"] == pytest.approx(100)
    restricted = result["robustness"]["investment_unflagged"]
    assert restricted["n"] == 32
    assert restricted["effect"] == pytest.approx(100)
    assert restricted["positive_interval"] is True
    assert result["trial"]["balance"]["age"]["n"] == 32
    assert result["trial"]["availability"][0]["income_without_profit"] == 4
    assert result["robustness"]["randomization"]["outcomes"]["profit_recorded"]["p"] == 1
    assert result["pricing"]["scenarios"][1]["loss"] == pytest.approx(800)
    assert result["decision"]["pass"] is False
    assert not any(check["pass"] for check in result["reproduction"].values())

    first = output.read_bytes()
    analyze(database, output)
    assert output.read_bytes() == first
    render(result, tmp_path)
    assert "Pilot FAIL" in (tmp_path / "decision.html").read_text()
    assert sorted(path.stem for path in tmp_path.glob("*.html")) == sorted(PAGES)


def test_site_snapshot_matches_aggregate(tmp_path):
    results = json.loads((SITE_DIR / "data" / "results.json").read_text())
    render(results, tmp_path)
    for slug in PAGES:
        filename = f"{slug}.html"
        assert (tmp_path / filename).read_bytes() == (SITE_DIR / filename).read_bytes()
