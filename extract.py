"""Read the verified Stata member into a local, sorted Parquet file."""

import hashlib
import io
import json
from zipfile import ZipFile

import pandas as pd

from config import STATA_MEMBER, STATA_SHA256

SOURCE_COLUMNS = [
    "slid",
    "sec_group_name",
    "sec_treat",
    "Stratification_Dummies",
    "sec_loanamount",
    "Match3rd_in3rd",
    "not_finished_aug19",
    "Outstanding_Loan_Amount_Default",
    "Business_Expenditures",
    "Profit",
    "Income",
    "Age_C",
    "Married_C",
    "Years_Education_C",
    "HH_Size_C",
    "Has_Business_C",
    "miss_Age_C",
    "miss_Married_C",
    "miss_Years_Education_C",
    "miss_HH_Size_C",
    "miss_Has_Business_C",
]


def extract(archive, parquet):
    package = archive.read_bytes()
    with ZipFile(io.BytesIO(package)) as zip_file:
        contents = zip_file.read(STATA_MEMBER)
    if hashlib.sha256(contents).hexdigest() != STATA_SHA256:
        raise ValueError("The Stata member does not match openICPSR project 112672 V1.")

    data = pd.read_stata(io.BytesIO(contents), columns=SOURCE_COLUMNS, convert_categoricals=False)
    parquet.parent.mkdir(parents=True, exist_ok=True)
    temporary = parquet.with_suffix(".tmp")
    data.sort_values("slid").to_parquet(temporary, index=False)
    temporary.replace(parquet)
    manifest = {
        "deposit": "https://doi.org/10.3886/E112672V1",
        "archive_sha256": hashlib.sha256(package).hexdigest(),
        "source_member": STATA_MEMBER,
        "source_sha256": STATA_SHA256,
        "parquet_sha256": hashlib.sha256(parquet.read_bytes()).hexdigest(),
        "rows": len(data),
        "columns": SOURCE_COLUMNS,
    }
    parquet.with_name("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
