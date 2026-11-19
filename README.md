# 📈 StockTheStock — AI-Powered Stock Research

### Powered by CrewAI • Company and Sector Research • Multi-Agent Workflow

StockTheStock researches companies, sectors, or stock-discovery questions and
turns the findings into a source-linked Markdown report. Specialist agents
gather market, financial, and news evidence; a separate review crew checks the
evidence before the report is written.

> **Note:** Reports are for research and education, not personalized financial
> advice or a buy/sell recommendation. Check the cited sources and current
> company filings before making investment decisions.

---

## 🚀 Features

- 🔎 **Company and sector research** — Research named companies and peers, or
  explore listed companies in a sector.

- 📊 **Specialist analysis** — Gather business and market context, financial
  evidence, dated news and
  catalysts, and a balanced assessment of risks and bull/bear cases.

- 🔗 **Evidence-focused reporting** — Ask agents to cite sources and dates,
  distinguish facts from analysis, and
  flag missing, conflicting, or unverified information.

- 🧠 **Memory for continuity** — Entity memory retrieves company-related
  context; long-term memory stores
  research insights locally in SQLite. Remembered information is a starting
  point, not verification of current facts.

- 📝 **Markdown output** — Save the final report to
  `output/research_report.md`.

- ⚙️ **YAML-configured agents and tasks** — Edit crew roles and task
  instructions in each crew's `config/` directory.

---

## 🧠 Architecture

The application uses a CrewAI **Flow** to coordinate two sequential crews.
There is no manager agent or hierarchical delegation.

### 1. Research Crew

Four specialist agents work through an ordered set of tasks:

- **Market researcher** establishes company identity, sector context, and
  discovery rationale.
- **Financial analyst** reviews reported financial performance and valuation
  evidence.
- **News analyst** searches for dated company, sector, and regulatory
  developments.
- **Investment analyst** combines the findings into a risk assessment and
  balanced bull and bear cases.

The financial and news tasks use the market research as context. The investment
assessment uses the market, financial, and news findings.

### 2. Report Crew

- **Evidence reviewer** flags unsupported claims, missing citations,
  contradictions, and date or period mismatches in the research package.
- **Report writer** uses the research and review to produce the final report.

---

## 🔄 How It Works

1. **Provide a research question** — for example, compare companies or explore
   a sector.
2. **Set the research context** — geography defaults to India, the horizon to
   long term, and the research date to the current UTC date.
3. **Gather evidence** — the research crew uses Serper web and news search to
   collect dated source material.
4. **Review and write** — the report crew checks the supplied evidence and
   creates a Markdown report.
5. **Read the report** — find it at `output/research_report.md`.

No dedicated market-price API is configured. If agents cannot verify a dated
price from web research, the report should say so rather than invent one.

---

## 🧰 Technology Stack

| Technology | Use in this project |
| --- | --- |
| **Python** | Application language and CLI entry point. |
| **CrewAI Flow** | Coordinates research and report-writing stages and carries validated inputs and findings in typed state. |
| **CrewAI agents, tasks, and crews** | Divide the work among specialists and pass task context through sequential workflows. |
| **EntityMemory with RAG storage** | Retrieves entity-focused context using OpenAI embeddings (`text-embedding-3-small`). |
| **LongTermMemory with SQLite** | Persists longer-lived task insights locally for retrieval in later runs. |
| **SerperDevTool** | Provides web and news search to research agents. |
| **OpenAI** | Supplies language-model access through CrewAI and embeddings for entity memory. |
| **Pydantic** | Validates and stores Flow inputs such as query, geography, horizon, and research date. |
| **uv** | Installs project dependencies and runs the application and tests. |

CrewAI's default short-term memory is disabled. Entity and long-term memory are
configured separately; neither replaces checking current claims against dated
sources.

---

## 🧪 Run It

### Requirements

- Python 3.10–3.13
- [uv](https://docs.astral.sh/uv/)
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Serper API key](https://serper.dev/)

### Install and configure

```bash
uv sync
cp .env.example .env
```

Add your keys to `.env`:

```dotenv
OPENAI_API_KEY=your-openai-api-key
SERPER_API_KEY=your-serper-api-key
```

Keep `.env` private; it is excluded from version control.

### Start research

```bash
uv run kickoff
```

Enter a question when prompted, such as `Compare TCS and Infosys`. Each run
replaces the report at `output/research_report.md`.

---

## ✅ Tests

Run the offline test suite with:

```bash
uv run python -m unittest discover -s tests -v
```
