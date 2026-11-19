"""Paths and source identity for the replication package."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RAW_DIR = REPO_ROOT.parent / "first-payment-internal" / "raw"
ZIP_PATH = RAW_DIR / "112672-V1.zip"
STATA_MEMBER = "Publication-Data-and-Do-Files/Grace-Period-Data.dta"
STATA_SHA256 = "288cbb09fbdaf8d6e27c3923bbfd2110b06ab2b442f091bca82f8cc823851b78"
DATA_DIR = REPO_ROOT / "data"
PARQUET_PATH = DATA_DIR / "replication.parquet"
DUCKDB_PATH = DATA_DIR / "first_payment.duckdb"
SITE_DIR = REPO_ROOT / "site"
