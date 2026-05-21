"""
Transaction parser: handles CSV and PDF bank statements.
Normalises columns, infers categories, and returns a clean DataFrame.
"""

import io
import re
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import pdfplumber
    PDF_BACKEND = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        PDF_BACKEND = "pypdf2"
    except ImportError:
        PDF_BACKEND = None

from app.utils.config import CATEGORY_KEYWORDS

logger = logging.getLogger(__name__)

# ─── Column name aliases ──────────────────────────────────────────────────────

DATE_ALIASES   = ["date", "transaction date", "trans date", "posted date", "value date"]
DESC_ALIASES   = ["description", "desc", "merchant", "payee", "narration", "details", "transaction"]
AMOUNT_ALIASES = ["amount", "debit", "credit", "transaction amount", "value"]
TYPE_ALIASES   = ["type", "transaction type", "dr/cr"]
BAL_ALIASES    = ["balance", "running balance", "available balance"]


# ─── Public API ──────────────────────────────────────────────────────────────

def parse_file(file) -> pd.DataFrame:
    """
    Accept a Streamlit UploadedFile (or file-like) and return a clean DataFrame.
    Raises ValueError with a human-friendly message on failure.
    """
    name = getattr(file, "name", "unknown")
    ext  = Path(name).suffix.lower()

    if ext == ".csv":
        return _parse_csv(file)
    elif ext == ".pdf":
        return _parse_pdf(file)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Please upload a CSV or PDF.")


# ─── CSV Parsing ─────────────────────────────────────────────────────────────

def _parse_csv(file) -> pd.DataFrame:
    """Read a CSV bank statement and normalise columns."""
    try:
        content = file.read()
        # Try common encodings
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Could not decode the CSV file. Try saving it as UTF-8.")

        df.columns = df.columns.str.strip()
        return _normalise_df(df)
    except Exception as e:
        logger.error("CSV parse error: %s", e)
        raise ValueError(f"Failed to parse CSV: {e}") from e


# ─── PDF Parsing ─────────────────────────────────────────────────────────────

def _parse_pdf(file) -> pd.DataFrame:
    """Extract tabular transaction data from a PDF bank statement."""
    if PDF_BACKEND is None:
        raise ValueError("PDF parsing requires pdfplumber or PyPDF2. Install with: pip install pdfplumber")

    content = file.read()
    rows: list[dict] = []

    if PDF_BACKEND == "pdfplumber":
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    headers = [str(h).strip().lower() if h else "" for h in table[0]]
                    for row in table[1:]:
                        if row:
                            rows.append(dict(zip(headers, [str(c).strip() if c else "" for c in row])))
    else:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        rows = _parse_text_transactions(text)

    if not rows:
        raise ValueError("No transaction table found in the PDF. Try exporting as CSV from your bank.")

    df = pd.DataFrame(rows)
    df.columns = df.columns.str.strip()
    return _normalise_df(df)


def _parse_text_transactions(text: str) -> list[dict]:
    """Heuristic line-by-line extraction for text-based PDFs."""
    pattern = re.compile(
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})"   # date
        r"\s+(.+?)"                                # description
        r"\s+([-]?\$?[\d,]+\.\d{2})"              # amount
        r"(?:\s+([-]?\$?[\d,]+\.\d{2}))?",        # optional balance
        re.MULTILINE,
    )
    rows = []
    for m in pattern.finditer(text):
        rows.append({
            "date"       : m.group(1),
            "description": m.group(2).strip(),
            "amount"     : m.group(3).replace("$", "").replace(",", ""),
            "balance"    : (m.group(4) or "").replace("$", "").replace(",", ""),
        })
    return rows


# ─── Normalisation ───────────────────────────────────────────────────────────

def _normalise_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map arbitrary column names → standard schema, clean types,
    and apply expense categorisation.
    """
    col_map = _build_col_map(df.columns.tolist())
    df = df.rename(columns=col_map)

    # ── Date ──────────────────────────────────────────────────────────────────
    if "date" not in df.columns:
        raise ValueError("Could not find a date column. Columns found: " + str(df.columns.tolist()))
    df["date"] = pd.to_datetime(df["date"], infer_datetime_format=True, errors="coerce")
    df = df.dropna(subset=["date"])

    # ── Description ───────────────────────────────────────────────────────────
    if "description" not in df.columns:
        df["description"] = "Unknown"
    df["description"] = df["description"].fillna("Unknown").astype(str).str.strip()

    # ── Amount ────────────────────────────────────────────────────────────────
    df = _resolve_amount(df)

    # ── Balance ───────────────────────────────────────────────────────────────
    if "balance" not in df.columns:
        df["balance"] = np.nan
    else:
        df["balance"] = _clean_numeric(df["balance"])

    # ── Category ──────────────────────────────────────────────────────────────
    df["category"] = df["description"].apply(categorise)

    # ── Derived columns ───────────────────────────────────────────────────────
    df["month"]        = df["date"].dt.to_period("M").astype(str)
    df["day_of_week"]  = df["date"].dt.day_name()
    df["is_expense"]   = df["amount"] < 0

    df = df.sort_values("date").reset_index(drop=True)
    logger.info("Parsed %d transactions (%d expenses)", len(df), df["is_expense"].sum())
    return df


def _build_col_map(cols: list[str]) -> dict[str, str]:
    """Return a mapping from raw column names to standard names."""
    mapping: dict[str, str] = {}
    lower_cols = [c.lower().strip() for c in cols]

    def find(aliases: list[str], target: str):
        for alias in aliases:
            for i, c in enumerate(lower_cols):
                if alias in c and cols[i] not in mapping:
                    mapping[cols[i]] = target
                    return

    find(DATE_ALIASES,   "date")
    find(DESC_ALIASES,   "description")
    find(AMOUNT_ALIASES, "amount")
    find(TYPE_ALIASES,   "type")
    find(BAL_ALIASES,    "balance")
    return mapping


def _resolve_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Handle banks that split debit/credit into separate columns."""
    if "amount" in df.columns:
        df["amount"] = _clean_numeric(df["amount"])
        # If a separate type column exists, use it to sign amounts
        if "type" in df.columns:
            mask_debit = df["type"].str.lower().str.contains("debit|dr|expense", na=False)
            df.loc[mask_debit & (df["amount"] > 0), "amount"] *= -1
        return df

    # Try debit / credit columns
    debit_col  = next((c for c in df.columns if "debit" in c.lower()), None)
    credit_col = next((c for c in df.columns if "credit" in c.lower()), None)
    if debit_col and credit_col:
        df["debit_amt"]  = _clean_numeric(df[debit_col]).fillna(0)
        df["credit_amt"] = _clean_numeric(df[credit_col]).fillna(0)
        df["amount"]     = df["credit_amt"] - df["debit_amt"]
        return df

    raise ValueError("Cannot determine transaction amounts from the uploaded file.")


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Strip currency symbols and commas, coerce to float."""
    return (
        series.astype(str)
        .str.replace(r"[\$,£€\s]", "", regex=True)
        .str.replace(r"\((.+)\)", r"-\1", regex=True)  # (1,234.56) → -1234.56
        .pipe(pd.to_numeric, errors="coerce")
    )


# ─── Categorisation ──────────────────────────────────────────────────────────

def categorise(description: str) -> str:
    """Rule-based category inference from transaction description."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "Other"


# ─── Summary Helpers ─────────────────────────────────────────────────────────

def build_summary_text(df: pd.DataFrame) -> str:
    """
    Build a plain-text summary of transactions for RAG indexing.
    Returns one sentence per transaction.
    """
    lines = []
    expenses = df[df["is_expense"]].copy()
    for _, row in expenses.iterrows():
        lines.append(
            f"On {row['date'].strftime('%B %d, %Y')}, spent ${abs(row['amount']):.2f} "
            f"at {row['description']} (category: {row['category']})."
        )
    return "\n".join(lines)


def compute_kpis(df: pd.DataFrame) -> dict:
    """Compute key financial KPIs from the cleaned DataFrame."""
    expenses = df[df["is_expense"]]["amount"].abs()
    income   = df[~df["is_expense"]]["amount"]

    monthly = (
        df[df["is_expense"]]
        .groupby("month")["amount"]
        .sum()
        .abs()
    )
    cat_totals = (
        df[df["is_expense"]]
        .groupby("category")["amount"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )

    # Anomaly: transactions > 2σ above mean expense
    mean_exp = expenses.mean()
    std_exp  = expenses.std()
    anomalies = df[(df["is_expense"]) & (df["amount"].abs() > mean_exp + 2 * std_exp)]

    return {
        "total_expenses"      : expenses.sum(),
        "total_income"        : income.sum(),
        "net_savings"         : income.sum() - expenses.sum(),
        "num_transactions"    : len(df),
        "num_expenses"        : len(expenses),
        "avg_transaction"     : expenses.mean(),
        "largest_expense"     : expenses.max(),
        "top_category"        : cat_totals.index[0] if len(cat_totals) else "N/A",
        "top_category_amount" : cat_totals.iloc[0] if len(cat_totals) else 0,
        "monthly_totals"      : monthly.to_dict(),
        "category_totals"     : cat_totals.to_dict(),
        "anomalies"           : anomalies,
        "savings_rate"        : (
            (income.sum() - expenses.sum()) / income.sum() * 100
            if income.sum() > 0 else 0
        ),
    }
