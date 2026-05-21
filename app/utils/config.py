"""
Configuration and environment management for FinanceAI Assistant.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ─── Logging Setup ────────────────────────────────────────────────────────────

def setup_logging():
    """Configure application-wide logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Suppress noisy third-party loggers
    for noisy in ["chromadb", "httpx", "httpcore", "urllib3"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root
APP_DIR  = BASE_DIR / "app"
DATA_DIR = APP_DIR / "data"
EMBED_DIR = APP_DIR / "embeddings"
REPORT_DIR = APP_DIR / "reports"
SAMPLE_DIR = BASE_DIR / "sample_data"

# Ensure directories exist
for d in [DATA_DIR, EMBED_DIR, REPORT_DIR, SAMPLE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── API Keys ─────────────────────────────────────────────────────────────────

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL  : str = "gemini-1.5-flash"

# ─── ChromaDB ────────────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR: str = os.getenv(
    "CHROMA_PERSIST_DIR",
    str(EMBED_DIR / "chroma_db"),
)
CHROMA_COLLECTION = "financial_transactions"

# ─── App ──────────────────────────────────────────────────────────────────────

APP_TITLE    = os.getenv("APP_TITLE", "FinanceAI Assistant")
APP_VERSION  = os.getenv("APP_VERSION", "1.0.0")
ENABLE_AUTH  = os.getenv("ENABLE_AUTH", "false").lower() == "true"
APP_PASSWORD = os.getenv("APP_PASSWORD", "financeai2024")

# ─── Expense Categories ───────────────────────────────────────────────────────

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Food & Dining": [
        "mcdonald", "starbucks", "chipotle", "pizza", "restaurant",
        "dining", "sushi", "burger", "cafe", "coffee", "food", "eat",
        "subway", "taco", "kfc", "dominos", "uber eats", "doordash",
        "grubhub", "wendy", "panera", "chick", "olive garden",
    ],
    "Groceries": [
        "walmart", "target", "costco", "whole foods", "trader joe",
        "kroger", "safeway", "publix", "aldi", "sprouts", "wegmans",
        "grocery", "supermarket", "market", "fresh",
    ],
    "Shopping": [
        "amazon", "ebay", "etsy", "nordstrom", "best buy", "apple store",
        "h&m", "zara", "gap", "nike", "adidas", "macy", "jcpenney",
        "kohls", "bloomingdale", "neiman", "saks", "store", "shop",
    ],
    "Transportation": [
        "uber", "lyft", "taxi", "gas", "shell", "bp", "chevron",
        "exxon", "mobil", "parking", "metro", "transit", "bus",
        "train", "fuel", "airline", "delta", "united", "southwest",
        "american airlines", "flight",
    ],
    "Bills & Utilities": [
        "electricity", "water", "internet", "phone", "cable", "utility",
        "electric", "gas bill", "heating", "verizon", "att", "comcast",
        "spectrum", "xfinity", "t-mobile", "sprint", "bill",
    ],
    "Entertainment": [
        "netflix", "spotify", "hulu", "disney", "hbo", "apple tv",
        "youtube", "twitch", "steam", "playstation", "xbox", "cinema",
        "movie", "theater", "concert", "event", "ticket", "itunes",
        "google play", "amazon prime",
    ],
    "Health & Wellness": [
        "pharmacy", "cvs", "walgreens", "rite aid", "doctor", "hospital",
        "clinic", "dental", "vision", "gym", "fitness", "yoga",
        "medical", "health", "drug", "prescription", "lab",
    ],
    "Travel & Hotels": [
        "hotel", "airbnb", "vrbo", "marriott", "hilton", "hyatt",
        "booking", "expedia", "travel", "resort", "motel", "inn",
        "hostel", "vacation",
    ],
    "Rent & Housing": [
        "rent", "mortgage", "lease", "property", "hoa", "maintenance",
        "repair", "home depot", "lowes", "furniture", "ikea",
    ],
    "Subscriptions": [
        "subscription", "membership", "annual fee", "premium",
    ],
    "Income": [
        "salary", "payroll", "direct deposit", "wage", "freelance",
        "payment received", "transfer in", "deposit", "credit",
    ],
    "Other": [],
}

CATEGORY_COLORS: dict[str, str] = {
    "Food & Dining"      : "#FF6B6B",
    "Groceries"          : "#4ECDC4",
    "Shopping"           : "#45B7D1",
    "Transportation"     : "#96CEB4",
    "Bills & Utilities"  : "#FFEAA7",
    "Entertainment"      : "#DDA0DD",
    "Health & Wellness"  : "#98D8C8",
    "Travel & Hotels"    : "#F7DC6F",
    "Rent & Housing"     : "#BB8FCE",
    "Subscriptions"      : "#85C1E9",
    "Income"             : "#82E0AA",
    "Other"              : "#BDC3C7",
}
