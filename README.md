# First Payment

A credit committee readout of a randomized microfinance trial in Kolkata.

**Pilot FAIL.** The grace-period contract increased reported weekly business profit by ₹906.6
among borrowers with recorded profit (95% CI ₹168.7 to ₹1,644.4, n=752). Default rose by 6.14
percentage points at 52 weeks past due (95% CI 1.20 to 11.09, n=845). The upper endpoint exceeded
the preset 2.00-point cap. Both the positive-profit and default checks had to pass.

The trial compares bundled contracts at one lender, with the grace period, maturity and
effective interest rate changing together, and missing follow-up leaves the effect on
full-cohort profit unresolved.

[Site files](site/index.html) · [Findings](docs/FINDINGS.md) ·
[Committee memo](docs/MEMO.md) · [Analysis plan](ANALYSIS_PLAN.md)

The build reproduces three rows from Field, Pande, Papp and Rigol, then applies a fixed pilot
rule, prices the incremental credit loss and stresses profit tails and missing outcomes.
The site includes two sliders for testing other caps and profit floors.

## Run locally

The checked-in site works as static files. For a browser served preview, run:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:8000/`. To regenerate the results, download the full project 112672 V1 ZIP
from the deposit, accepting its access terms. Pass its local path to the build. The default
path is `../first-payment-internal/raw/112672-V1.zip`. [Replication deposit](https://doi.org/10.3886/E112672V1)

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build.py /path/to/112672-V1.zip
ruff check .
python -m pytest
```

Python verifies the Stata member checksum and converts the relevant fields to sorted local
Parquet. The manifest records source and output hashes. dbt builds borrower, group and outcome
marts in DuckDB and checks the trial grain and assignment. Python fits the models, writes
aggregate JSON and renders the static pages. Inputs and row-level outputs stay local.
The test suite exercises the build with a synthetic archive, so GitHub Actions can run without
the real trial file. Same-environment repeated builds are checked for identical aggregate
JSON and HTML bytes.

## Source and licence

Field, Erica, Rohini Pande, John Papp and Natalia Rigol (2013), *Does the Classic Microfinance
Model Discourage Entrepreneurship among the Poor? Experimental Evidence from India*,
American Economic Review 103(6), 2196–2226. [Paper](https://doi.org/10.1257/aer.103.6.2196)

Replication data by the same authors, published by the American Economic Association in 2013
and distributed by ICPSR in 2019, V1. The deposit's licence covers source code under
BSD-3-Clause and other material under CC BY 4.0. The repository contains an independent
implementation and derived aggregates. The supplied scripts and borrower-level data are
available from the deposit. [AEA deposit](https://doi.org/10.3886/E112672V1)
