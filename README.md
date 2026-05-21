# ⚡ FinanceAI Assistant

> AI-powered personal finance analysis and budgeting tool built with Streamlit, LangChain, Gemini, and ChromaDB.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-purple)

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| 📁 **Upload** | CSV and PDF bank statement parsing |
| 🏷️ **Auto-Categorise** | Rule-based + AI expense categorisation |
| 📊 **Dashboard** | KPI cards, pie chart, trend lines, heatmaps |
| 💬 **AI Chatbot** | Context-aware Q&A using RAG + Gemini |
| 🔍 **Semantic Search** | ChromaDB-powered vector retrieval |
| 💡 **Budget Tips** | AI-generated personalised recommendations |
| ⚠️ **Anomaly Detection** | Statistical + AI anomaly analysis |
| 📥 **Reports** | Downloadable PDF and CSV exports |

---

## 🛠️ Quick Start

### 1. Clone / Download the project

```bash
git clone https://github.com/your-repo/financeai
cd financeai
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get a free Gemini API key at: https://makersuite.google.com/app/apikey

### 5. Run the application

```bash
streamlit run main.py
```

Open http://localhost:8501 in your browser.

---

## 📂 Project Structure

```
financeai/
├── main.py                     # Streamlit entry point
├── requirements.txt
├── .env.example
├── README.md
├── sample_data/
│   └── sample_transactions.csv # Demo data
└── app/
    ├── components/
    │   ├── charts.py            # Plotly visualisations
    │   └── ui_helpers.py        # KPI cards, CSS, layout
    ├── utils/
    │   ├── config.py            # Env vars, constants
    │   ├── parser.py            # CSV/PDF parsing, categorisation
    │   ├── rag_engine.py        # LangChain + ChromaDB RAG
    │   └── report_generator.py  # PDF report generation
    ├── data/                    # Temp uploaded files
    ├── embeddings/              # ChromaDB vector store
    └── reports/                 # Generated PDF reports
```

---

## 💬 AI Chatbot — Example Questions

- "Where did I spend the most money?"
- "How can I reduce my expenses next month?"
- "Summarize my spending for March."
- "What are my top 5 transactions?"
- "Am I saving enough? What's my savings rate?"
- "Show me all food and dining expenses."
- "Which subscriptions am I paying for?"

---

## 📊 Supported CSV Formats

The parser auto-detects columns. Common formats supported:

| Bank Format | Date Column | Amount Column |
|-------------|-------------|---------------|
| Generic | `Date` | `Amount` |
| Chase | `Transaction Date` | `Amount` |
| Bank of America | `Date` | `Amount` |
| Wells Fargo | `Date` | `Amount` |
| Custom | Auto-detected | Auto-detected |

For PDFs, the app uses `pdfplumber` to extract tables automatically.

---

## ☁️ Deploy to Streamlit Cloud

1. Push your code to GitHub (make sure `.env` is in `.gitignore`)

2. Go to [share.streamlit.io](https://share.streamlit.io)

3. Click **New app** → connect your GitHub repo

4. Set **Main file path**: `main.py`

5. Add secrets in the Streamlit Cloud dashboard:
   ```
   GEMINI_API_KEY = "your_key_here"
   ```

6. Click **Deploy** 🚀

---

## 🔧 Configuration Options (.env)

```env
GEMINI_API_KEY=your_key          # Required for AI features
APP_TITLE=FinanceAI Assistant    # App display name
ENABLE_AUTH=false                # Set true to add password protection
APP_PASSWORD=yourpassword        # Password if auth enabled
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
CHROMA_PERSIST_DIR=./app/embeddings/chroma_db
```

---

## 🧰 Tech Stack

- **Frontend**: Streamlit 1.32+
- **AI/LLM**: Google Gemini 1.5 Flash via LangChain
- **RAG Pipeline**: LangChain + ChromaDB
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Data**: Pandas, NumPy
- **Visualisation**: Plotly
- **PDF**: pdfplumber, ReportLab
- **Config**: python-dotenv

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ using Streamlit + LangChain + Gemini*
