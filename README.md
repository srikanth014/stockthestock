# StockTheStock

StockTheStock researches companies and compares stocks using web search,
financial and news analysis, risk assessment, and a balanced investment thesis.
It writes the findings as a Markdown report.

## Get started

Requires Python 3.10–3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
```

Add your API keys to `.env`:

- `OPENAI_API_KEY` — required for the research agents and entity memory.
- `SERPER_API_KEY` — required for web and news search.

## Run

```bash
uv run kickoff
```

The app prompts for a research query; geography defaults to India. For example,
enter `Compare TCS and Infosys` or `Discover renewable energy stocks` for a
full report. You can also ask about a stock's price; without a dedicated market
data API, the app will report a price only when it can verify a dated value from
web research. Reports are saved to `output/research_report.md`.

## What to expect

Research includes source links and dates, financial and qualitative evidence,
risks, and both bull and bear cases. Search results and remembered information
are not substitutes for checking current company filings and other cited
sources. Reports are for research, not personalized financial advice.

Run the offline checks with:

```bash
uv run python -m unittest discover -s tests -v
```
